"""نقطة تشغيل برنامج تحميل فيديوهات يوتيوب."""
import sys

from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow
from core.logger import setup_logger


def main():
    setup_logger()
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Downloader")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
