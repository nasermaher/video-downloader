"""إعداد نظام تسجيل الأحداث والأخطاء للبرنامج."""
import logging
import os

from core.paths import get_app_data_dir

LOG_DIR = os.path.join(get_app_data_dir(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def setup_logger():
    """يهيئ logger عام يكتب في ملف logs/app.log وفي الطرفية."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("youtube_downloader")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger():
    return logging.getLogger("youtube_downloader")
