"""حفظ واسترجاع إعدادات المستخدم (مسار التحميل، الجودة الافتراضية...)."""
import json
import os

from core.paths import get_app_data_dir

SETTINGS_DIR = os.path.join(get_app_data_dir(), "config")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "last_download_path": os.path.expanduser("~"),
    "default_quality": "best",
    "preferred_format": "mp4",
    "download_delay_seconds": 2.0,
    "language": "ar",
    "theme": "light",
    "download_subtitles": False,
    "subtitle_langs": "ar,en",
    "download_description": False,
    "queue_max_parallel": 3,
}


class Settings:
    """طبقة بسيطة لقراءة وكتابة إعدادات المستخدم في ملف JSON محلي."""

    def __init__(self):
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        self._data = self._load()

    def _load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    merged = DEFAULT_SETTINGS.copy()
                    merged.update(data)
                    return merged
            except (json.JSONDecodeError, OSError):
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()

    def save(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()
