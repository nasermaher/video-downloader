"""تنفيذ عملية التحميل الفعلية في خيط منفصل مع تقارير تقدم."""
import os
from dataclasses import dataclass

import yt_dlp
from PyQt5.QtCore import QThread, pyqtSignal

from core.logger import get_logger
from core.paths import get_bundled_ffmpeg_path

logger = get_logger()

_STOP_POLL_INTERVAL_SECONDS = 0.1


@dataclass
class DownloadOptions:
    """إعدادات عملية التحميل: الصيغة، مسار الحفظ، والمرفقات الاختيارية (ترجمة/وصف)."""

    format_id: str
    output_dir: str
    delay_seconds: float = 2.0
    download_subtitles: bool = False
    subtitle_langs: str = "ar,en"
    download_description: bool = False


class DownloadWorker(QThread):
    """
    خيط منفصل ينفذ تحميل فيديو واحد أو أكثر عبر yt-dlp، مع فاصل زمني بين كل فيديو
    والتالي لتخفيف الضغط على سيرفرات يوتيوب، ويبث إشارات التقدم والحالة والانتهاء
    إلى الواجهة الرسومية. يدعم استكمال التحميلات المتوقفة تلقائيًا طالما ملف
    ".part" الجزئي موجود في مسار الحفظ.

    الإيقاف المؤقت (pause) بينهي تنفيذ الخيط الحالي (بدل تجميده) ويبث قائمة الروابط
    المتبقية عبر إشارة paused؛ استئناف التحميل مسؤولية المستدعي: ينشئ DownloadWorker
    جديد بنفس الروابط المتبقية ونفس الإعدادات، وبيكمّل الفيديو الجاري من ملف ".part"
    تلقائيًا بفضل نفس آلية الاستكمال.
    """

    progress = pyqtSignal(str, float, str)   # url, percent, status_text
    item_finished = pyqtSignal(str, bool, str)  # url, success, message
    paused = pyqtSignal(list)   # remaining urls (تشمل الفيديو اللي كان بيتحمّل وقت الإيقاف)
    all_finished = pyqtSignal()

    def __init__(self, urls: list, options: DownloadOptions, parent=None):
        super().__init__(parent)
        self.urls = urls
        self.options = options
        self._stop_requested = False
        self._pause_requested = False

    def stop(self):
        """يطلب إلغاء التحميل بالكامل بعد إنهاء الفيديو الجاري (لا يقطعه في المنتصف)."""
        self._stop_requested = True

    def pause(self):
        """يطلب إيقاف مؤقت: يقطع الفيديو الجاري ويحتفظ بملفه الجزئي لاستكماله لاحقًا."""
        self._pause_requested = True

    def _interrupted(self) -> bool:
        return self._stop_requested or self._pause_requested

    def run(self):
        last_index = len(self.urls) - 1
        for index, url in enumerate(self.urls):
            if self._interrupted():
                return self._finish_interrupted(self.urls[index:])

            self._download_one(url)
            if self._pause_requested:
                return self._finish_interrupted(self.urls[index:])
            if self._stop_requested:
                break

            if index != last_index:
                self._wait_before_next_download()
                if self._pause_requested:
                    return self._finish_interrupted(self.urls[index + 1:])
                if self._stop_requested:
                    break

        self.all_finished.emit()

    def _finish_interrupted(self, remaining_urls: list):
        if self._pause_requested:
            self.paused.emit(remaining_urls)
        else:
            self.all_finished.emit()

    def _wait_before_next_download(self):
        """ينتظر بين تحميل وآخر، مع فحص دوري لطلب الإيقاف/التوقف المؤقت حتى لا تتأخر الاستجابة."""
        remaining = self.options.delay_seconds
        while remaining > 0 and not self._interrupted():
            step = min(_STOP_POLL_INTERVAL_SECONDS, remaining)
            self.msleep(int(step * 1000))
            remaining -= step

    def _download_one(self, url: str):
        ydl_opts = self._build_ydl_opts(url)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.item_finished.emit(url, True, "تم التحميل بنجاح")
        except yt_dlp.utils.DownloadError as e:
            if self._interrupted():
                return  # إيقاف مقصود من المستخدم، مش فشل حقيقي؛ run() هيتعامل معاه
            logger.error("فشل تحميل %s: %s", url, e)
            self.item_finished.emit(url, False, str(e))

    def _build_ydl_opts(self, url: str) -> dict:
        opts = {
            "format": self.options.format_id or "bestvideo+bestaudio/best",
            "outtmpl": {
                "default": os.path.join(self.options.output_dir, "%(title)s.%(ext)s"),
                # yt-dlp بيحفظ الوصف افتراضيًا بامتداد .description؛ هنا بنجبره يستخدم .txt
                # بنفس اسم ملف الفيديو حسب المطلوب.
                "description": os.path.join(self.options.output_dir, "%(title)s.txt"),
            },
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [lambda d: self._progress_hook(url, d)],
            "merge_output_format": "mp4",
            # استكمال التحميلات المتوقفة: يستأنف من ملف ".part" الموجود بدل البدء من الصفر.
            "continuedl": True,
            "nopart": False,
        }
        ffmpeg_path = get_bundled_ffmpeg_path()
        if ffmpeg_path:
            # في النسخة المجمّعة (exe)، لو ffmpeg.exe موجود بجانب البرنامج نستخدمه مباشرة
            # بدل الاعتماد على تثبيته يدويًا في PATH النظام.
            opts["ffmpeg_location"] = ffmpeg_path
        if self.options.download_subtitles:
            opts.update(self._subtitle_opts())
        if self.options.download_description:
            opts["writedescription"] = True
        return opts

    def _subtitle_opts(self) -> dict:
        langs = [lang.strip() for lang in self.options.subtitle_langs.split(",") if lang.strip()]
        return {
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": langs or ["en"],
            "subtitlesformat": "srt",
            "postprocessors": [{"key": "FFmpegSubtitlesConvertor", "format": "srt"}],
        }

    def _progress_hook(self, url: str, d: dict):
        if self._interrupted():
            message = "تم الإيقاف المؤقت" if self._pause_requested else "تم إيقاف التحميل بواسطة المستخدم"
            raise yt_dlp.utils.DownloadError(message)

        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            percent = (downloaded / total * 100) if total else 0.0
            speed = d.get("_speed_str", "").strip()
            self.progress.emit(url, percent, speed)
        elif d.get("status") == "finished":
            self.progress.emit(url, 100.0, "جارٍ المعالجة...")
