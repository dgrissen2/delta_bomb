"""Registration must resume after a partial write without a premature sentinel."""
from pathlib import Path
import pytest


def test_interrupted_registration_rolls_forward(tmp_path: Path,monkeypatch) -> None:
    import registry_transaction as rt
    first,second,inventory = [tmp_path/name for name in ['dictionary','changelog','inventory']]
    first.write_text('old dictionary')
    second.write_text('old changelog')
    plan = tmp_path/'plan.json'
    updates = [(first,'new dictionary'),(second,'new changelog'),(inventory,'complete')]
    real = rt.atomic_text
    def fail_second(path,content):
        if path==second:
            raise OSError('simulated interruption')
        real(path,content)
    monkeypatch.setattr(rt,'atomic_text',fail_second)
    with pytest.raises(OSError,match='interruption'):
        rt.commit_files(plan,updates)
    assert first.read_text()=='new dictionary' and not inventory.exists()
    monkeypatch.setattr(rt,'atomic_text',real)
    rt.resume(plan)
    assert second.read_text()=='new changelog' and inventory.read_text()=='complete'


def test_concurrent_registry_edit_is_preserved(tmp_path: Path,monkeypatch) -> None:
    import registry_transaction as rt
    target=tmp_path/'dictionary'
    target.write_text('original')
    plan=tmp_path/'plan.json'
    monkeypatch.setattr(rt,'resume',lambda path:None)
    rt.commit_files(plan,[(target,'intended')])
    target.write_text('another task wrote this')
    monkeypatch.undo()
    with pytest.raises(ValueError,match='changed'):
        rt.resume(plan)
    assert target.read_text()=='another task wrote this'
