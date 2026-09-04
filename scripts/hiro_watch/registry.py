"""hiro_watch W1 — the candidate registry: every yaml under docs/hiro_watch/configs/, validated.

One home for "what is a candidate" so run.py and compare.py cannot disagree. Validation is the
guard the engines' loaders do not give us: each candidate's log dir must be its own directory under
docs/replay/hiro_watch/, unique across candidates, and never the baseline ledger.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS.parent
CONFIGS = REPO_ROOT / "docs/hiro_watch/configs"
WATCH_ROOT = REPO_ROOT / "docs/replay/hiro_watch"
BASELINE_DIR = REPO_ROOT / "docs/replay/hiro"
KINDS = ("control", "promotable", "diagnostic")
ENGINES = ("hiro_engine", "hiro_engine_v2")


@dataclass(frozen=True)
class Candidate:
    name: str
    engine: str
    kind: str
    registered: str
    change: str
    path: Path
    config_hash: str            # sha256 of the yaml bytes = what the engine stamps on every row
    log_dir: Path
    paper_log: Path             # <log_dir>/paper_log_backtest.csv  (engine derives it from logging.paper_log)
    sessions: Path              # <log_dir>/sessions_backtest.csv   (engine derives it from logging.sessions_log)
    raw: dict


def _resolve(p: str) -> Path:
    q = Path(p).expanduser()
    return q if q.is_absolute() else REPO_ROOT / q


def candidates() -> list[Candidate]:
    out: list[Candidate] = []
    for p in sorted(CONFIGS.glob("*.yaml")):
        raw = yaml.safe_load(p.read_text())
        w = raw.get("watch")
        if not w:
            raise SystemExit(f"REFUSED: {p.name} has no watch: section")
        for k in ("name", "engine", "kind", "registered", "change"):
            if k not in w:
                raise SystemExit(f"REFUSED: {p.name} watch.{k} missing")
        if w["name"] != p.stem:
            raise SystemExit(f"REFUSED: {p.name} watch.name {w['name']!r} != file stem")
        if w["engine"] not in ENGINES or w["kind"] not in KINDS:
            raise SystemExit(f"REFUSED: {p.name} engine/kind not in {ENGINES}/{KINDS}")
        paper = _resolve(raw["logging"]["paper_log"]).with_name("paper_log_backtest.csv")
        sess = _resolve(raw["logging"]["sessions_log"]).with_name("sessions_backtest.csv")
        log_dir = paper.parent
        if log_dir != WATCH_ROOT / w["name"] or sess.parent != log_dir:
            raise SystemExit(f"REFUSED: {p.name} logging paths must both live in {WATCH_ROOT / w['name']} "
                             f"(got {paper.parent}, {sess.parent}) — never the baseline ledger {BASELINE_DIR}")
        out.append(Candidate(name=w["name"], engine=w["engine"], kind=w["kind"], registered=str(w["registered"]),
                             change=str(w["change"]), path=p, config_hash=hashlib.sha256(p.read_bytes()).hexdigest(),
                             log_dir=log_dir, paper_log=paper, sessions=sess, raw=raw))
    if not out:
        raise SystemExit(f"REFUSED: no candidate yamls under {CONFIGS}")
    if len({c.config_hash for c in out}) != len(out):
        raise SystemExit("REFUSED: two candidate yamls have identical bytes")
    return out


def baseline_data() -> dict:
    """The data: section of baseline_v2.yaml (spx_dir, hiro_era_start, ...)."""
    return yaml.safe_load((CONFIGS / "baseline_v2.yaml").read_text())["data"]
