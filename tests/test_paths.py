"""اختبارات core.paths.get_bundled_ffmpeg_path (اكتشاف ffmpeg المرفق مع النسخة المجمّعة)."""
import os
import sys

import core.paths as paths_module


def test_returns_none_when_not_frozen(monkeypatch):
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert paths_module.get_bundled_ffmpeg_path() is None


def test_returns_none_when_frozen_but_ffmpeg_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "app.exe"))

    assert paths_module.get_bundled_ffmpeg_path() is None


def test_returns_path_when_frozen_and_ffmpeg_present(monkeypatch, tmp_path):
    ffmpeg_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    ffmpeg_file = tmp_path / ffmpeg_name
    ffmpeg_file.write_bytes(b"")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "app.exe"))

    assert paths_module.get_bundled_ffmpeg_path() == str(ffmpeg_file)
