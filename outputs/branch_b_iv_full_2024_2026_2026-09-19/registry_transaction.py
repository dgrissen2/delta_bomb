"""Durable, resumable local registration; the completion inventory is written last."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile


def content_hash(value: str | None) -> str | None:
    return hashlib.sha256(value.encode()).hexdigest() if value is not None else None


def atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary = tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        if path.exists():
            os.chmod(temporary,path.stat().st_mode & 0o777)
        with os.fdopen(fd,'w') as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def resume(plan_path: Path) -> None:
    plan = json.loads(plan_path.read_text())
    for item in plan['files']:
        path = Path(item['path'])
        current = path.read_text() if path.exists() else None
        if current == item['after']:
            continue
        if content_hash(current) != item['before_sha256']:
            raise ValueError(f'Registry changed since the transaction was prepared: {path}')
        atomic_text(path,item['after'])


def commit_files(plan_path: Path, updates: list[tuple[Path,str]]) -> None:
    if plan_path.exists():
        raise FileExistsError('Use resume() for the existing durable transaction')
    items = [dict(path=str(p),before_sha256=content_hash(p.read_text() if p.exists() else None),
                  after=text) for p,text in updates]
    atomic_text(plan_path,json.dumps(dict(files=items),indent=2)+'\n')
    resume(plan_path)
