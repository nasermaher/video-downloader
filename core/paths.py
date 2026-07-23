"""تحديد مجلد بيانات التطبيق (سجلات وإعدادات) بما يتوافق مع وضع التشغيل."""
import os
import sys

APP_DIR_NAME = "YoutubeDownloader"


def get_app_data_dir() -> str:
    """
    يرجع مجلد أساسي قابل للكتابة لتخزين بيانات التطبيق.

    في وضع exe مجمّع بـ PyInstaller (sys.frozen=True) يستخدم %APPDATA%
    (أو المجلد الشخصي كبديل) بدل مجلد التثبيت المؤقت غير الدائم.
    في وضع التطوير العادي يستخدم جذر المشروع كما كان سابقًا.
    """
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, APP_DIR_NAME)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_bundled_ffmpeg_path():
    """
    يرجع مسار ffmpeg المرفق بجانب الملف التنفيذي المجمّع (لو المستخدم حطه هناك)،
    أو None لو البرنامج شغال في وضع التطوير أو مفيش ffmpeg مرفق فعليًا، وفي الحالتين
    yt-dlp هيدور عليه تلقائيًا في PATH النظام بدل كده.
    """
    if not getattr(sys, "frozen", False):
        return None
    base_dir = os.path.dirname(sys.executable)
    binary_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    candidate = os.path.join(base_dir, binary_name)
    return candidate if os.path.isfile(candidate) else None
