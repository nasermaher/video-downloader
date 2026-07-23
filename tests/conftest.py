"""إعدادات مشتركة لاختبارات pytest."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5.QtWidgets import QApplication

import core.settings as settings_module


@pytest.fixture(scope="session")
def qapp():
    """يوفر QApplication واحد لكل جلسة اختبار (مطلوب لأي QObject من PyQt يحمل إشارات)."""
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """
    يعزل كل اختبار عن ملف الإعدادات الحقيقي (settings.json) بمسار مؤقت خاص به.
    بدون هذا، أي اختبار بيغيّر إعداد زي اللغة (مثلاً عبر MainWindow) هيكتبه على قرص
    المشروع الفعلي، فتتأثر نتائج اختبارات تانية بترتيب تشغيلها.
    """
    settings_dir = tmp_path / "config"
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", str(settings_dir))
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", str(settings_dir / "settings.json"))
