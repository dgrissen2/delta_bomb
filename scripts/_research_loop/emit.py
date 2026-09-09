#!/usr/bin/env python3
"""Assemble saved Charlie/Quant Codex JSON responses; never call a model or subprocess."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import contracts as C
import verify_round as V


def _inputs(project: Path, rnd: int, phase: str,
            cfg: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Read and validate every required response before writing phase artifacts."""
    inputs = []
    for persona in cfg["personas"]:
        path = C.raw_path(project, rnd, phase, persona)
        raw = C.validate_raw_payload(C._load_json(path, "raw"), phase)
        persona_path = Path(cfg.get("persona_paths", {}).get(persona, C.PERSONA_PATHS[persona]))
        if not persona_path.is_file():
            raise C.MalformedArtifact(f"persona definition missing: {persona_path}")
        metadata = {
            "persona_id": persona,
            "resolved_source": cfg.get("persona_source", "global"),
            "resolved_path": str(persona_path.resolve()),
            "primary": {
                "engine": "codex",
                "producer_status": "ok",
                "raw_path": str(path.relative_to(project)),
                "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            },
        }
        inputs.append((metadata, raw))
    return inputs


def run(project: Path, rnd: int, phase: str) -> list[Path]:
    """Assemble one required phase from canonical verbatim agent raw files."""
    project = project.resolve()
    cfg = V.load_config(project)
    C.validate_codex_config(cfg)
    if rnd < 1 or (phase == "seed" and rnd != 1):
        raise C.MalformedArtifact("round must be positive; seed expansion belongs to round 1")
    if phase not in {"seed", "commentary", "proposals"}:
        raise C.MalformedArtifact(f"unsupported phase: {phase}")
    inputs = _inputs(project, rnd, phase, cfg)
    base = {"round": rnd, "engine_mode": "codex_only"}
    staged: list[tuple[Path, dict[str, Any]]] = []
    if phase == "seed":
        blocks = [{**meta, "primary": {**meta["primary"], "response": raw}}
                  for meta, raw in inputs]
        staged.append((project / "outputs" / "seed_expansion.json", {**base, "personas": blocks}))
    elif phase == "commentary":
        hids = set(inputs[0][1]["by_hid"])
        if any(set(raw["by_hid"]) != hids for _, raw in inputs):
            raise C.MalformedArtifact("both personas must comment on the same hypothesis IDs")
        for hid in sorted(hids):
            blocks = [{**meta, "primary": {**meta["primary"], **raw["by_hid"][hid]}}
                      for meta, raw in inputs]
            path = project / "outputs" / "commentary" / f"round{rnd}" / f"{hid}.json"
            staged.append((path, {**base, "hypothesis_id": hid, "personas": blocks}))
    else:
        # Preserve the framework's flat proposal blocks for unchanged synthesis/promotion.
        blocks = [{**{key: value for key, value in meta.items() if key != "primary"},
                   **meta["primary"], "candidates": raw["candidates"],
                   "reprioritize": raw["reprioritize"]} for meta, raw in inputs]
        path = project / "outputs" / "proposals" / f"round{rnd}.json"
        staged.append((path, {**base, "blocks": blocks}))

    for _, data in staged:
        blocks = data["blocks"] if phase == "proposals" else data["personas"]
        problems = V.check_panel(project, rnd, phase, blocks, cfg, data.get("hypothesis_id"))
        if problems:
            raise C.MalformedArtifact("; ".join(problem.message for problem in problems))
    for path, data in staged:
        path.parent.mkdir(parents=True, exist_ok=True)
        C.atomic_write(path, json.dumps(data, indent=2) + "\n")
    return [path for path, _ in staged]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="project root (default: cwd)")
    parser.add_argument("--phase", choices=("seed", "commentary", "proposals"), required=True)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        outputs = run(Path(args.project), args.round, args.phase)
    except (C.ContractError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return C.EXIT_MALFORMED
    for output in outputs:
        print(output)
    return C.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
