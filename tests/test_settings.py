"""اختبارات core.settings.Settings مع مجلد إعدادات مؤقت حقيقي (بدون mock)."""
import core.settings as settings_module
from core.settings import DEFAULT_SETTINGS, Settings


def _use_tmp_settings_dir(monkeypatch, tmp_path):
    settings_dir = tmp_path / "config"
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", str(settings_dir))
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", str(settings_dir / "settings.json"))


def test_first_run_without_file_uses_default_settings(monkeypatch, tmp_path):
    _use_tmp_settings_dir(monkeypatch, tmp_path)

    settings = Settings()

    assert settings.get("default_quality") == DEFAULT_SETTINGS["default_quality"]
    assert settings.get("download_delay_seconds") == DEFAULT_SETTINGS["download_delay_seconds"]


def test_saved_value_survives_reload(monkeypatch, tmp_path):
    _use_tmp_settings_dir(monkeypatch, tmp_path)

    settings = Settings()
    settings.set("last_download_path", "/downloads/videos")

    reloaded = Settings()

    assert reloaded.get("last_download_path") == "/downloads/videos"


def test_corrupted_settings_file_falls_back_to_defaults(monkeypatch, tmp_path):
    _use_tmp_settings_dir(monkeypatch, tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.json").write_text("{not valid json", encoding="utf-8")

    settings = Settings()

    assert settings.get("default_quality") == DEFAULT_SETTINGS["default_quality"]
