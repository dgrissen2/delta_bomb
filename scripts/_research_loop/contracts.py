#!/usr/bin/env python3
"""The single inter-phase contract layer for research_loop's back-half enforcement.

This module is the one place that owns:

1. **JSON artifact structure** — `load_commentary` / `load_proposals` / `load_synthesis`
   read a file, parse it, and structurally validate it. Malformed/empty JSON or any
   structural/enum violation raises `MalformedArtifact` (the gate maps this to exit 3).
   Per the plan (PR-9), only *structural* rules live here; relational/semantic rules
   (coverage, traceability, materialization, the producer_status->agreement implication)
   live in `verify_round.py`.
2. **Shared enums** — including `persona_source` and the provenance tuple — so producers,
   `promote.py`, and `verify_round.py` never duplicate string literals.
3. **The markdown artifact grammar** — index columns + order, note frontmatter keys, the
   required note sections, link/ID/status-cell formats — imported by both `promote.py`
   (which writes) and `verify_round.py` (which verifies), so the two cannot drift.
4. **The action -> edit map** for reprioritization.

Stdlib only. Lives in `framework/shared/` (installed to `.claude/skills/_research_loop/`).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- exit codes
EXIT_OK = 0          # round is closeable
EXIT_INCOMPLETE = 2  # round incomplete (semantic) — raised by verify_round, not here
EXIT_MALFORMED = 3   # malformed/structurally-invalid required artifact


# --------------------------------------------------------------------------- exceptions
class ContractError(Exception):
    """Base for contract violations."""


class MalformedArtifact(ContractError):
    """A required artifact is missing, empty, unparseable, or structurally invalid.

    The message is field-keyed (e.g. ``proposals.blocks[0].engine``) so the gate's
    punchlist names the exact location. Maps to exit code 3.
    """


# --------------------------------------------------------------------------- atomic file io
def atomic_write(path: Path, text: str) -> None:
    """Atomically write `text` to `path`: a temp file in the SAME directory + ``os.replace``.

    The single shared writer for every JSON/markdown artifact a project produces (emit,
    synthesize, promote). The temp lives beside the target so it is on the same filesystem
    and ``os.replace`` is atomic; ``encoding="utf-8"`` matches every existing call site so
    the bytes are byte-identical to a direct ``write_text(..., encoding="utf-8")``. A reader
    therefore never sees a half-written or interleaved file, and a crash before the replace
    leaves the previous file intact.
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- enums
PRIORITY = frozenset({"high", "medium", "low"})
ENGINE = frozenset({"codex"})
CODEX_PERSONAS = ("charlie-mcelligott", "quant")
PERSONA_PATHS = {
    "charlie-mcelligott": Path.home() / ".config/skillshare/personas/market/charlie-mcelligott.md",
    "quant": Path.home() / ".config/skillshare/personas/strategy/quant.md",
}
KIND = frozenset({"hypothesis", "experiment"})
CLASSIFICATION = frozenset({"promote", "experiment", "defer", "drop"})
HYPOTHESIS_STATUS = frozenset({"active", "deferred", "dropped"})
PRODUCER_STATUS = frozenset({"ok", "timeout", "unavailable"})
EXPERIMENT_STATUS = frozenset({"planned", "running", "done", "dropped"})
PERSONA_SOURCE = frozenset({"local", "global"})
ACTIONS = frozenset({"deprioritize", "drop"})

# Program-level convergence / early-termination (distinct from per-round `deferred`).
# The loop only ever RECOMMENDS via synthesis.termination_recommendation.recommend;
# the binding decision is the human-authorized `termination:` block whose status the
# gate reads (it never terminates on its own). See RESEARCH_PROCESS.md.
TERMINATION_RECOMMEND = frozenset({"continue", "converge", "stop"})
TERMINATION_STATUS = frozenset({"active", "terminated"})

# Action -> concrete index-table edit. Single source consumed by promote.py (to apply)
# and verify_round.py (to check). Experiment->hypothesis promotion is NOT here — it is a
# synthesis `promote` decision carrying `from_experiment_id` (PR-11).
ACTION_EDIT = {
    "deprioritize": "lower Priority cell one step (high->medium->low; low is a no-op)",
    "drop": "set Status cell to 'dropped' + a why note; never delete the row",
}


# --------------------------------------------------------------------------- markdown grammar
# Index `Hypotheses` table columns, in order. `Status` (outcome/verdict, human-facing)
# pre-existed; the enforcement migration appends `Round` (D2). The gate's *lifecycle*
# authority is the note frontmatter `hypothesis_status` (active/deferred/dropped), not
# this Status column. promote.py writes the Round cell; verify_round.py cross-checks it.
INDEX_HYPOTHESES_COLUMNS = (
    "Hypothesis ID", "Claim", "Primary Signal/Variable", "Primary Target/Outcome",
    "Scope", "Note", "Supporting Docs", "Supporting Files", "Status", "Best Evidence",
    "Next Step", "Round",
)
INDEX_FOLLOWUP_COLUMNS = (
    "Experiment ID", "Proposed Experiment", "Why Run It", "Scope",
    "Parent Hypothesis", "Source Note", "Priority", "Status",
)

# Note YAML frontmatter keys (D2).
FRONTMATTER_KEYS = ("id", "round", "hypothesis_status", "phase")
PHASES = ("method", "execute", "interpret", "verdict", "commentary", "recorded")

# Required note section headings the gate checks (matched case-insensitively as
# substrings of the note's `##` headings). Mirrors the findings template.
NOTE_REQUIRED_SECTIONS = (
    "Target / Outcome Definition",
    "Sample Integrity",
    "Method",
    "Results",
    "Threats To Validity",
    "Final Verdict",
    "Decision Impact",
    "Reproduction",
    "Feynman",
    "Persona Commentary",
)

VERDICTS = frozenset(
    {"supported", "weak_support", "mixed", "not_supported", "inconclusive"}
)

# Stable-ID grammar: H-<PREFIX>-001 / E-<PREFIX>-001 (prefix: letters/digits, <=8).
ID_RE = re.compile(r"^(?P<kind>[HE])-(?P<prefix>[A-Z0-9]{1,8})-(?P<num>\d{3,})$")
# A markdown link target: [text](path) — path is what we resolve for backlinks.
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def stable_id(kind_letter: str, prefix: str, num: int, width: int = 3) -> str:
    """Build a stable hypothesis/experiment ID (e.g. ``H-COR-004``)."""
    if kind_letter not in {"H", "E"}:
        raise ValueError(f"kind_letter must be H or E, got {kind_letter!r}")
    return f"{kind_letter}-{prefix.upper()}-{num:0{width}d}"


def parse_id(value: str) -> dict[str, Any] | None:
    """Parse a stable ID into {kind, prefix, num}; None if it doesn't match the grammar."""
    m = ID_RE.match(value.strip())
    if not m:
        return None
    return {"kind": m["kind"], "prefix": m["prefix"], "num": int(m["num"])}


def link_targets(markdown: str) -> list[str]:
    """Return every markdown link target in `markdown` (for backlink checks)."""
    return LINK_RE.findall(markdown)


# Index table identifiers: table key -> (first column header, full column tuple).
INDEX_TABLES = {
    "hypotheses": ("Hypothesis ID", INDEX_HYPOTHESES_COLUMNS),
    "followup": ("Experiment ID", INDEX_FOLLOWUP_COLUMNS),
}


def _split_row(line: str) -> list[str]:
    """Split a markdown table row ``| a | b |`` into stripped, unescaped cells.

    Splits only on UNescaped pipes so a cell containing a literal ``\\|`` (e.g. a claim
    like ``SPY \\| QQQ``) does not shift later columns; the ``\\|`` is unescaped back to ``|``.
    """
    body = line.strip()
    cells = re.split(r"(?<!\\)\|", body)
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return [c.replace("\\|", "|").strip() for c in cells]


def format_index_row(table: str, cells: dict[str, str]) -> str:
    """Render a markdown row for `table` from a column->value dict (escaping pipes).

    The single writer path for index rows — used by append_index_row and by promote.py's
    in-place row edits, so reader (_split_row) and writers can't drift on cell formatting.
    """
    _, columns = INDEX_TABLES[table]
    esc = [str(cells.get(col, "")).replace("|", "\\|") for col in columns]
    return "| " + " | ".join(esc) + " |"


def _table_bounds(lines: list[str], first_col: str) -> tuple[int, int, int]:
    """Return (header_idx, first_data_idx, end_idx) for the table whose header
    starts with ``| <first_col>``. end_idx is exclusive (first non-row line)."""
    header_idx = next(
        (i for i, ln in enumerate(lines) if ln.lstrip().startswith(f"| {first_col}")),
        -1,
    )
    if header_idx < 0:
        raise ContractError(f"index table not found (first column {first_col!r})")
    first_data = header_idx + 2  # header + separator
    end = first_data
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    return header_idx, first_data, end


def read_index_table(markdown: str, table: str) -> tuple[list[str], list[dict[str, str]]]:
    """Parse one index table into (columns, rows). Empty placeholder rows are skipped."""
    first_col, _ = INDEX_TABLES[table]
    lines = markdown.splitlines()
    header_idx, first_data, end = _table_bounds(lines, first_col)
    columns = _split_row(lines[header_idx])
    rows: list[dict[str, str]] = []
    for ln in lines[first_data:end]:
        cells = _split_row(ln)
        if not any(cells):  # placeholder/empty row
            continue
        rows.append({columns[i]: (cells[i] if i < len(cells) else "") for i in range(len(columns))})
    return columns, rows


def append_index_row(markdown: str, table: str, cells: dict[str, str]) -> str:
    """Append a row (cells keyed by column name) to an index table; returns new markdown."""
    first_col, _ = INDEX_TABLES[table]
    lines = markdown.splitlines(keepends=True)
    flat = [ln.rstrip("\n") for ln in lines]
    _, _, end = _table_bounds(flat, first_col)
    flat.insert(end, format_index_row(table, cells))
    return "\n".join(flat) + ("\n" if markdown.endswith("\n") else "")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse a leading ``---`` YAML frontmatter block into a flat str->str dict.

    Minimal scalar parser (the frontmatter only holds id/round/hypothesis_status/phase).
    Returns {} when no frontmatter block is present.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        out[key.strip()] = val.strip().strip("\"'")
    return out


def format_frontmatter(values: dict[str, Any]) -> str:
    """Render a frontmatter block for the known keys, in canonical order."""
    lines = ["---"]
    for key in FRONTMATTER_KEYS:
        if key in values:
            lines.append(f"{key}: {values[key]}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- validation helpers
def _err(field: str, msg: str) -> MalformedArtifact:
    return MalformedArtifact(f"{field}: {msg}")


def _obj(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _err(field, f"expected object, got {type(value).__name__}")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise _err(field, f"expected array, got {type(value).__name__}")
    return value


def _str(obj: dict[str, Any], key: str, field: str, *, required: bool = True) -> str | None:
    if key not in obj:
        if required:
            raise _err(f"{field}.{key}", "required")
        return None
    val = obj[key]
    if val is None and not required:
        return None
    if not isinstance(val, str):
        raise _err(f"{field}.{key}", f"expected string, got {type(val).__name__}")
    return val


def _enum(obj: dict[str, Any], key: str, allowed: frozenset[str], field: str,
          *, required: bool = True) -> str | None:
    val = _str(obj, key, field, required=required)
    if val is None:
        return None
    if val not in allowed:
        raise _err(f"{field}.{key}", f"must be one of {sorted(allowed)}, got {val!r}")
    return val


def _int(obj: dict[str, Any], key: str, field: str) -> int:
    if key not in obj:
        raise _err(f"{field}.{key}", "required")
    val = obj[key]
    if isinstance(val, bool) or not isinstance(val, int):
        raise _err(f"{field}.{key}", f"expected integer, got {type(val).__name__}")
    return val


def _load_json(path: Path, root_field: str) -> Any:
    """Read + parse JSON; empty/unparseable -> MalformedArtifact (exit 3)."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise _err(root_field, f"file not found: {path}") from exc
    if not raw.strip():
        raise _err(root_field, f"empty file: {path}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise _err(root_field, f"invalid JSON ({exc})") from exc


def _provenance(block: dict[str, Any], field: str) -> None:
    """Validate the per-persona-record provenance fields (resolved_source/resolved_path)."""
    _enum(block, "resolved_source", PERSONA_SOURCE, field)
    _str(block, "resolved_path", field)


def validate_codex_config(cfg: dict[str, Any]) -> None:
    """Require the user-selected native Codex panel; no silently skipped persona."""
    if cfg.get("engine_mode") != "codex_only":
        raise _err("config.engine_mode", "must be codex_only")
    personas = cfg.get("personas")
    if (not isinstance(personas, list) or not all(isinstance(p, str) for p in personas)
            or sorted(personas) != sorted(CODEX_PERSONAS)):
        raise _err("config.personas", f"must contain exactly {list(CODEX_PERSONAS)}")
    if cfg.get("codex"):
        raise _err("config.codex", "legacy twin mode is incompatible with codex_only")
    paths = cfg.get("persona_paths", {})
    if not isinstance(paths, dict) or any(not isinstance(p, str) for p in paths.values()):
        raise _err("config.persona_paths", "expected persona ID to path mapping")


def validate_primary(block: dict[str, Any], field: str) -> None:
    """Validate native producer metadata without inventing cross-model agreement."""
    if block.get("engine") != "codex":
        raise _err(f"{field}.engine", "native primary must be codex")
    if block.get("producer_status") != "ok":
        raise _err(f"{field}.producer_status", "native primary must be ok")
    if "claude" in block or "twin" in block or "agreement" in block:
        raise _err(field, "codex_only does not permit Claude/twin/agreement blocks")
    _str(block, "raw_path", field)
    digest = _str(block, "raw_sha256", field)
    if not re.fullmatch(r"[0-9a-f]{64}", digest or ""):
        raise _err(f"{field}.raw_sha256", "expected SHA256 hex digest")


def validate_raw_payload(data: Any, phase: str) -> dict[str, Any]:
    """Validate only the three raw response shapes used by this small adapter."""
    data = _obj(data, f"raw.{phase}")
    if phase == "seed":
        hypotheses = _list(data.get("hypotheses"), "raw.seed.hypotheses")
        if not 1 <= len(hypotheses) <= 3:
            raise _err("raw.seed.hypotheses", "require one to three hypotheses")
        for i, hypothesis in enumerate(hypotheses):
            field = f"raw.seed.hypotheses[{i}]"
            hypothesis = _obj(hypothesis, field)
            for key in ("claim", "pass_criterion", "controls"):
                if not hypothesis.get(key):
                    raise _err(f"{field}.{key}", "required and nonempty")
            if not (hypothesis.get("target") or hypothesis.get("outcome")):
                raise _err(f"{field}.target", "target or outcome required and nonempty")
        if not data.get("simple_protocol"):
            raise _err("raw.seed.simple_protocol", "required and nonempty")
    elif phase == "commentary":
        items = _obj(data.get("by_hid"), "raw.commentary.by_hid")
        if not items:
            raise _err("raw.commentary.by_hid", "cannot be empty")
        for hid, item in items.items():
            if not parse_id(hid) or not hid.startswith("H-"):
                raise _err("raw.commentary.by_hid", f"invalid hypothesis ID: {hid}")
            item = _obj(item, f"raw.commentary.{hid}")
            for key in ("interpret", "act"):
                if not (_str(item, key, f"raw.commentary.{hid}") or "").strip():
                    raise _err(f"raw.commentary.{hid}.{key}", "cannot be empty")
    elif phase == "proposals":
        seen: set[str] = set()
        for i, candidate in enumerate(_list(data.get("candidates"), "raw.proposals.candidates")):
            field = f"raw.proposals.candidates[{i}]"
            candidate = _obj(candidate, field)
            _validate_candidate(candidate, field)
            _enum(candidate, "kind", KIND, field)
            for key in ("candidate_key", "title", "rationale", "falsification", "decision_impact"):
                if not (_str(candidate, key, field) or "").strip():
                    raise _err(f"{field}.{key}", "cannot be empty")
            if candidate["candidate_key"] in seen:
                raise _err(field, "duplicate candidate_key")
            seen.add(candidate["candidate_key"])
        for item in _list(data.get("reprioritize"), "raw.proposals.reprioritize"):
            item = _obj(item, "raw.proposals.reprioritize")
            _str(item, "id", "raw.proposals.reprioritize")
            _enum(item, "action", ACTIONS, "raw.proposals.reprioritize")
    else:
        raise _err("phase", f"unsupported phase: {phase}")
    return data


def raw_path(project: Path, rnd: int, phase: str, persona: str) -> Path:
    """Return the fixed raw-response location, with no caller-selected substitute."""
    return project / "outputs" / "persona_raw" / f"round{rnd}" / phase / f"{persona}.json"


def verify_raw_link(project: Path, rnd: int, phase: str, persona: str,
                    primary: dict[str, Any], hid: str | None = None) -> None:
    """Require an exact raw-file hash and an unchanged payload in the emitted block."""
    validate_primary(primary, f"{phase}.{persona}.primary")
    expected = raw_path(project, rnd, phase, persona)
    linked = project / primary["raw_path"]
    if linked.resolve() != expected.resolve():
        raise _err(f"{phase}.{persona}.raw_path", f"must resolve to {expected}")
    if not expected.is_file():
        raise _err(f"{phase}.{persona}.raw_path", "raw file missing")
    if hashlib.sha256(expected.read_bytes()).hexdigest() != primary["raw_sha256"]:
        raise _err(f"{phase}.{persona}.raw_sha256", "raw hash mismatch")
    raw = validate_raw_payload(_load_json(expected, "raw"), phase)
    if phase == "seed":
        matches = primary.get("response") == raw
    elif phase == "commentary":
        original = raw["by_hid"].get(hid)
        matches = original is not None and all(
            primary.get(key) == original[key] for key in ("interpret", "act")
        )
    else:
        matches = all(primary.get(key) == raw[key] for key in ("candidates", "reprioritize"))
    if not matches:
        raise _err(f"{phase}.{persona}", "emitted content differs from verbatim raw response")


# --------------------------------------------------------------------------- loaders
def load_commentary(path: str | Path) -> dict[str, Any]:
    """Load + structurally validate one round/hypothesis commentary artifact."""
    path = Path(path)
    field = "commentary"
    data = _obj(_load_json(path, field), field)
    _int(data, "round", field)
    _str(data, "hypothesis_id", field)
    personas = _list(data.get("personas"), f"{field}.personas")
    if not personas:
        raise _err(f"{field}.personas", "at least one persona block required")
    for i, p in enumerate(personas):
        pf = f"{field}.personas[{i}]"
        p = _obj(p, pf)
        _str(p, "persona_id", pf)
        if any(key in p for key in ("claude", "twin", "agreement")):
            raise _err(pf, "codex_only does not permit Claude/twin/agreement blocks")
        primary = _obj(p.get("primary"), f"{pf}.primary")
        validate_primary(primary, f"{pf}.primary")
        _str(primary, "interpret", f"{pf}.primary")
        _str(primary, "act", f"{pf}.primary")
        _provenance(p, pf)
    return data


def _validate_candidate(c: dict[str, Any], field: str) -> None:
    _str(c, "candidate_key", field)
    kind = _enum(c, "kind", KIND, field, required=False)
    _str(c, "title", field)
    _enum(c, "priority", PRIORITY, field)
    # parent may be null only for hypothesis candidates
    parent = c.get("parent")
    if parent is not None and not isinstance(parent, str):
        raise _err(f"{field}.parent", "expected string or null")
    if parent is None and kind == "experiment":
        raise _err(f"{field}.parent", "experiment candidates require a parent")


def load_proposals(path: str | Path) -> dict[str, Any]:
    """Load + structurally validate a round's proposals artifact.

    Structural only: per-block candidate_key uniqueness and cross-engine cardinality
    are checked here (within-block uniqueness) but coverage/traceability are the
    verifier's job.
    """
    path = Path(path)
    field = "proposals"
    data = _obj(_load_json(path, field), field)
    _int(data, "round", field)
    blocks = _list(data.get("blocks"), f"{field}.blocks")
    for i, b in enumerate(blocks):
        bf = f"{field}.blocks[{i}]"
        b = _obj(b, bf)
        _str(b, "persona_id", bf)
        validate_primary(b, bf)
        _provenance(b, bf)
        seen: set[str] = set()
        for j, c in enumerate(_list(b.get("candidates", []), f"{bf}.candidates")):
            cf = f"{bf}.candidates[{j}]"
            c = _obj(c, cf)
            _validate_candidate(c, cf)
            key = c["candidate_key"]
            if key in seen:
                raise _err(f"{cf}.candidate_key", f"duplicate within block: {key!r}")
            seen.add(key)
        for j, r in enumerate(_list(b.get("reprioritize", []), f"{bf}.reprioritize")):
            rf = f"{bf}.reprioritize[{j}]"
            r = _obj(r, rf)
            _str(r, "id", rf)
            _enum(r, "action", ACTIONS, rf)
    return data


def load_termination(block: Any) -> dict[str, Any] | None:
    """Validate a parsed ``termination:`` mapping from research_loop.yml.

    The binding, human-authorized program-close record (fact-early-stop-human-only).
    Returns the normalized record (``round`` coerced to int) or ``None`` when no
    termination block is present. A present-but-invalid block raises
    `MalformedArtifact` (exit 3). All four fields are required when a block exists.

    Values arrive from `verify_round.load_config`'s minimal YAML reader as strings,
    so ``round`` is accepted as an int or a digit-string and normalized to int.
    """
    if block is None:
        return None
    field = "termination"
    block = _obj(block, field)
    status = _enum(block, "status", TERMINATION_STATUS, field)
    reason = _str(block, "reason", field)
    if not (reason or "").strip():
        raise _err(f"{field}.reason", "required (non-empty)")
    authorized_by = _str(block, "authorized_by", field)
    if not (authorized_by or "").strip():
        raise _err(f"{field}.authorized_by", "required (non-empty)")
    raw_round = block.get("round")
    if raw_round is None:
        raise _err(f"{field}.round", "required")
    if isinstance(raw_round, bool) or not isinstance(raw_round, (int, str)):
        raise _err(f"{field}.round", f"expected integer, got {type(raw_round).__name__}")
    try:
        rnd = int(raw_round)
    except ValueError as exc:
        raise _err(f"{field}.round", f"expected integer, got {raw_round!r}") from exc
    return {"status": status, "reason": reason, "round": rnd, "authorized_by": authorized_by}


def load_synthesis(path: str | Path) -> dict[str, Any]:
    """Load + structurally validate a round's synthesis artifact (one decisions[] array)."""
    path = Path(path)
    field = "synthesis"
    data = _obj(_load_json(path, field), field)
    _int(data, "round", field)
    deferred = _obj(data.get("deferred"), f"{field}.deferred")
    if not isinstance(deferred.get("is_deferred"), bool):
        raise _err(f"{field}.deferred.is_deferred", "expected boolean")
    if deferred["is_deferred"] and not (deferred.get("reason") or "").strip():
        raise _err(f"{field}.deferred.reason", "required when is_deferred is true")
    # Optional advisory recommendation (fact-termination-recommendation). Validated only
    # when present so pre-existing synthesis files still load; never closes a program.
    tr = data.get("termination_recommendation")
    if tr is not None:
        trf = f"{field}.termination_recommendation"
        tr = _obj(tr, trf)
        _enum(tr, "recommend", TERMINATION_RECOMMEND, trf)
        _str(tr, "reason", trf, required=False)
        for k, item in enumerate(_list(tr.get("data_blocked", []), f"{trf}.data_blocked")):
            if not isinstance(item, str):
                raise _err(f"{trf}.data_blocked[{k}]",
                           f"expected string, got {type(item).__name__}")
    decisions = _list(data.get("decisions"), f"{field}.decisions")
    seen: set[str] = set()
    for i, d in enumerate(decisions):
        dfld = f"{field}.decisions[{i}]"
        d = _obj(d, dfld)
        key = _str(d, "decision_key", dfld)
        if key in seen:
            raise _err(f"{dfld}.decision_key", f"duplicate within round: {key!r}")
        seen.add(key)
        classification = _enum(d, "classification", CLASSIFICATION, dfld)
        _str(d, "reason", dfld)
        sources = _list(d.get("sources"), f"{dfld}.sources")
        if not sources:
            raise _err(f"{dfld}.sources", "at least one source tuple required")
        for j, s in enumerate(sources):
            sf = f"{dfld}.sources[{j}]"
            s = _obj(s, sf)
            _str(s, "persona_id", sf)
            _enum(s, "engine", ENGINE, sf)
            _str(s, "candidate_key", sf)
        if classification in {"promote", "experiment"}:
            _str(d, "title", dfld)
            _enum(d, "priority", PRIORITY, dfld)
    for j, r in enumerate(_list(data.get("reprioritize", []), f"{field}.reprioritize")):
        rf = f"{field}.reprioritize[{j}]"
        r = _obj(r, rf)
        _str(r, "id", rf)
        _enum(r, "action", ACTIONS, rf)
    return data
