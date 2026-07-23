"""أنماط المظهر الفاتح/الداكن للواجهة."""

LIGHT_STYLESHEET = ""  # المظهر الافتراضي لنظام التشغيل بدون أي تخصيص

DARK_STYLESHEET = """
QWidget { background-color: #2b2b2b; color: #e0e0e0; }
QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTableWidget, QSpinBox {
    background-color: #3c3f41; color: #e0e0e0; border: 1px solid #555;
}
QPushButton { background-color: #4a4a4a; color: #e0e0e0; border: 1px solid #666; padding: 5px; }
QPushButton:hover { background-color: #5a5a5a; }
QPushButton:disabled { color: #888; }
QProgressBar { border: 1px solid #555; text-align: center; color: #e0e0e0; }
QProgressBar::chunk { background-color: #3a7bd5; }
QHeaderView::section { background-color: #3c3f41; color: #e0e0e0; }
QTabBar::tab { background-color: #3c3f41; color: #e0e0e0; padding: 6px; }
QTabBar::tab:selected { background-color: #4a4a4a; }
QMenuBar, QMenu { background-color: #3c3f41; color: #e0e0e0; }
"""


def stylesheet_for(theme: str) -> str:
    """يرجع نص الـ QSS المناسب لاسم المظهر ('dark' أو أي قيمة أخرى تعتبر فاتحًا)."""
    return DARK_STYLESHEET if theme == "dark" else LIGHT_STYLESHEET
