"""Codex-only persona provenance must not weaken the research back-half gates."""

import importlib
import json
import sys
from pathlib import Path

import pytest

FRAMEWORK = Path(__file__).resolve().parents[1] / "scripts" / "_research_loop"
PERSONAS = ["charlie-mcelligott", "quant"]
HID = "H-PNDR-001"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def framework():
    sys.path.insert(0, str(FRAMEWORK))
    try:
        return tuple(importlib.import_module(name) for name in
                     ("contracts", "emit", "verify_round", "synthesize", "promote"))
    finally:
        sys.path.remove(str(FRAMEWORK))


@pytest.fixture
def project(tmp_path: Path) -> Path:
    ht = tmp_path / "hypothesis_tracking"
    ht.mkdir()
    (ht / "research_loop.yml").write_text(
        "engine_mode: codex_only\npersonas: [charlie-mcelligott, quant]\n"
        "persona_source: global\nround_cap: 2\nK: 2\nprefix: PNDR\n",
        encoding="utf-8",
    )
    for persona in PERSONAS:
        root = tmp_path / "outputs" / "persona_raw" / "round1"
        write_json(root / "seed" / f"{persona}.json", {
            "hypotheses": [{"claim": "Frozen claim", "target": "Paired profit",
                            "pass_criterion": "Positive interval", "controls": "Same exit"}],
            "simple_protocol": {"rule": "Fixed timing"},
        })
        write_json(root / "commentary" / f"{persona}.json", {
            "by_hid": {HID: {"interpret": "Evidence is incomplete.",
                              "act": "Keep the verdict inconclusive."}},
        })
        write_json(root / "proposals" / f"{persona}.json", {
            "candidates": [{"candidate_key": f"audit-{persona}", "kind": "experiment",
                            "title": f"Audit {persona}", "priority": "high", "parent": HID,
                            "rationale": "Coverage is unknown", "falsification": "PIT absent",
                            "decision_impact": "Continue only with verified inputs"}],
            "reprioritize": [],
        })
    return tmp_path


def emit_all(framework, project: Path) -> None:
    for phase in ("seed", "commentary", "proposals"):
        framework[1].run(project, 1, phase)


def commentary_check(framework, project: Path):
    verifier = framework[2]
    return verifier.check_commentary(project, 1, HID, verifier.load_config(project))


def test_native_commentary_is_accepted_with_verbatim_raw_links(framework, project):
    emit_all(framework, project)
    path = project / "outputs/commentary/round1" / f"{HID}.json"
    data = framework[0].load_commentary(path)
    assert {block["persona_id"] for block in data["personas"]} == set(PERSONAS)
    assert all("claude" not in block and "twin" not in block for block in data["personas"])
    assert all(block["primary"]["engine"] == "codex" for block in data["personas"])
    assert commentary_check(framework, project) == []


@pytest.mark.parametrize("field,value", [("engine", "claude"), ("producer_status", "timeout")])
def test_rejects_non_codex_or_unsuccessful_primary(framework, project, field, value):
    emit_all(framework, project)
    path = project / "outputs/commentary/round1" / f"{HID}.json"
    data = json.loads(path.read_text())
    data["personas"][0]["primary"][field] = value
    write_json(path, data)
    assert commentary_check(framework, project)


def test_rejects_missing_persona_and_invalid_config(framework, project):
    emit_all(framework, project)
    path = project / "outputs/commentary/round1" / f"{HID}.json"
    data = json.loads(path.read_text())
    data["personas"].pop()
    write_json(path, data)
    assert any("quant" in p.message for p in commentary_check(framework, project))
    cfg = project / "hypothesis_tracking/research_loop.yml"
    cfg.write_text(cfg.read_text().replace("charlie-mcelligott, quant", "quant"))
    with pytest.raises(framework[0].ContractError, match="personas"):
        framework[1].run(project, 1, "seed")


def test_rejects_raw_hash_mismatch(framework, project):
    emit_all(framework, project)
    raw = project / "outputs/persona_raw/round1/commentary/quant.json"
    raw.write_text(raw.read_text() + " ")
    assert any("hash" in p.message for p in commentary_check(framework, project))


def test_rejects_edited_commentary_with_unchanged_raw(framework, project):
    emit_all(framework, project)
    path = project / "outputs/commentary/round1" / f"{HID}.json"
    data = json.loads(path.read_text())
    data["personas"][0]["primary"]["interpret"] = "Invented favorable verdict."
    write_json(path, data)
    assert any("raw" in p.message for p in commentary_check(framework, project))


def test_missing_raw_fails_without_partial_phase_output(framework, project):
    (project / "outputs/persona_raw/round1/seed/quant.json").unlink()
    with pytest.raises(framework[0].ContractError):
        framework[1].run(project, 1, "seed")
    assert not (project / "outputs/seed_expansion.json").exists()


def test_seed_accepts_original_outcome_key_without_rewriting_raw(framework, project):
    path = project / "outputs/persona_raw/round1/seed/charlie-mcelligott.json"
    data = json.loads(path.read_text())
    data["hypotheses"][0]["outcome"] = data["hypotheses"][0].pop("target")
    write_json(path, data)
    original = path.read_bytes()
    framework[1].run(project, 1, "seed")
    emitted = json.loads((project / "outputs/seed_expansion.json").read_text())
    response = emitted["personas"][0]["primary"]["response"]
    assert response == data and "target" not in response["hypotheses"][0]
    assert path.read_bytes() == original


def test_missing_back_half_and_backlink_still_fail(framework, project):
    emit_all(framework, project)
    contracts, _, verifier, _, _ = framework
    note = contracts.format_frontmatter({"id": HID, "round": 1,
                                        "hypothesis_status": "active", "phase": "recorded"})
    note += "\n" + "\n".join(f"## {s}\n\ninconclusive\n" for s in
                                 contracts.NOTE_REQUIRED_SECTIONS)
    note += "\n[Absent data](absent.csv)\n"
    (project / "hypothesis_tracking/h-pndr-001.md").write_text(note)
    problems = verifier.verify(project, 1)
    assert any("missing proposals.json or synthesis.json" in p.message for p in problems)
    assert any("memo" in p.message for p in problems)
    assert any("dangling backlink" in p.message for p in problems)


def test_synthesis_still_requires_materialization_and_both_personas(framework, project):
    emit_all(framework, project)
    _, _, verifier, synthesize, _ = framework
    synthesize.run(project, 1)
    cfg = verifier.load_config(project)
    problems = verifier.check_phase8(project, 1, cfg)
    assert sum("not materialized" in p.message for p in problems) == 2
    path = project / "outputs/proposals/round1.json"
    data = json.loads(path.read_text())
    data["blocks"].pop()
    write_json(path, data)
    assert any("quant" in p.message for p in verifier.check_phase8(project, 1, cfg))


def test_rejects_wrong_round_and_fake_twin(framework, project):
    emit_all(framework, project)
    path = project / "outputs/commentary/round1" / f"{HID}.json"
    data = json.loads(path.read_text())
    data["round"] = 2
    data["personas"][0]["twin"] = {"engine": "codex", "producer_status": "ok"}
    write_json(path, data)
    assert commentary_check(framework, project)


def test_complete_native_round_closes_after_real_materialization(framework, project):
    emit_all(framework, project)
    contracts, _, verifier, synthesize, promote = framework
    index = "# Research index\n\n"
    for table, (_, columns) in contracts.INDEX_TABLES.items():
        index += "| " + " | ".join(columns) + " |\n"
        index += "| " + " | ".join("---" for _ in columns) + " |\n\n"
    ht = project / "hypothesis_tracking"
    (ht / "RESEARCH_HYPOTHESIS_INDEX.md").write_text(index)
    note = contracts.format_frontmatter({"id": HID, "round": 1,
                                        "hypothesis_status": "active", "phase": "recorded"})
    note += "\n" + "\n".join(f"## {s}\n\ninconclusive\n" for s in
                                 contracts.NOTE_REQUIRED_SECTIONS)
    note += "\n[Index](RESEARCH_HYPOTHESIS_INDEX.md)\n"
    (ht / "h-pndr-001.md").write_text(note)
    (ht / "memo-pndr.md").write_text(
        "# Memo\n\n**Status:** living\n**Verdict:** inconclusive\n\n"
        "## 4. Timeline\n\n| Round | Result |\n|---|---|\n| 1 | Inputs audited |\n"
    )
    synthesize.run(project, 1)
    result = promote.apply_round(project, 1)
    assert len(result["experiments_added"]) == 2
    assert verifier.verify(project, 1) == []
    assert promote.apply_round(project, 1)["experiments_added"] == []
    assert "E-PNDR-001" in (ht / "RESEARCH_HYPOTHESIS_INDEX.md").read_text()
