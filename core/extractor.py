"""استخلاص معلومات الفيديو أو قائمة التشغيل والصيغ المتاحة دون تحميل."""
import yt_dlp

from core.logger import get_logger

logger = get_logger()


class ExtractionError(Exception):
    """يُرفع عند فشل استخلاص معلومات الرابط (رابط غير صالح، فيديو محذوف...)."""


def get_info(url: str) -> dict:
    """
    يستدعي yt-dlp لجلب معلومات الرابط بدون تحميل فعلي.
    يعيد قاموسًا موحّدًا يميّز بين فيديو مفرد وقائمة تشغيل.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            raw_info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        logger.error("فشل استخلاص المعلومات للرابط %s: %s", url, e)
        raise ExtractionError(str(e)) from e

    is_playlist = raw_info.get("_type") == "playlist" or "entries" in raw_info

    if is_playlist:
        entries = [
            {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "url": entry.get("webpage_url") or entry.get("url"),
                "duration": entry.get("duration"),
                "thumbnail": entry.get("thumbnail"),
            }
            for entry in raw_info.get("entries", [])
            if entry
        ]
        return {
            "is_playlist": True,
            "title": raw_info.get("title"),
            "entries": entries,
        }

    formats = _extract_formats(raw_info.get("formats", []))

    return {
        "is_playlist": False,
        "title": raw_info.get("title"),
        "duration": raw_info.get("duration"),
        "thumbnail": raw_info.get("thumbnail"),
        "url": raw_info.get("webpage_url", url),
        "formats": formats,
    }


def _extract_formats(raw_formats: list) -> list:
    """يبسّط قائمة الصيغ الخام من yt-dlp إلى بيانات تُعرض في الواجهة، مع تحديد صريح
    هل الصيغة فيها فيديو و/أو صوت، لأن يوتيوب غالبًا بيفصلهم في صيغ منفصلة."""
    formats = []
    for f in raw_formats:
        if not f.get("format_id"):
            continue
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        formats.append(
            {
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution") or f.get("format_note") or "audio",
                "fps": f.get("fps"),
                "filesize": f.get("filesize") or f.get("filesize_approx"),
                "vcodec": vcodec,
                "acodec": acodec,
                "has_video": vcodec not in (None, "none"),
                "has_audio": acodec not in (None, "none"),
            }
        )
    return formats
