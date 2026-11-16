import stat
from pathlib import Path

import pytest

from deploy.update import replace_file


def test_replace_file(tmp_path):
    source_file = tmp_path / "new-health.py"
    target_file = tmp_path / "health.py"

    source_file.write_text("new")
    target_file.write_text("old")
    replace_file(source_file, target_file)

    assert target_file.read_text() == 'new'

    file_mode = target_file.stat().st_mode
    permissions = stat.S_IMODE(file_mode)

    assert permissions == 0o644

    tmp_list = list(tmp_path.glob(".health.py.*"))

    assert tmp_list == []

def test_copy_error(tmp_path, monkeypatch):
    def fail_copy(source, target):
        target_file = Path(target)
        target_file.write_text('partial')
        raise OSError("simulated copy error")

    monkeypatch.setattr("deploy.update.shutil.copyfile", fail_copy)

    source_file = tmp_path / "new-health.py"
    target_file = tmp_path / "health.py"

    source_file.write_text("new")
    target_file.write_text("old")

    with pytest.raises(OSError, match="simulated copy error"):
        replace_file(source_file, target_file)

    assert target_file.read_text() == "old"

    tmp_list = list(tmp_path.glob(".health.py.*"))

    assert tmp_list == []