"""اختبارات core.i18n."""
from PyQt5.QtCore import Qt

from core.i18n import layout_direction_for, tr


def test_tr_returns_arabic_by_default():
    assert tr("stop_button", "ar") == "إيقاف"


def test_tr_returns_english_when_requested():
    assert tr("stop_button", "en") == "Stop"


def test_tr_falls_back_to_key_for_unknown_key():
    assert tr("no_such_key", "en") == "no_such_key"


def test_tr_formats_kwargs_into_message():
    message = tr("fetch_failed", "en", error="boom")
    assert "boom" in message


def test_layout_direction_matches_language():
    assert layout_direction_for("ar") == Qt.RightToLeft
    assert layout_direction_for("en") == Qt.LeftToRight
