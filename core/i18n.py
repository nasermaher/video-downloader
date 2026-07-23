"""طبقة ترجمة بسيطة للواجهة (عربي/إنجليزي)."""
from PyQt5.QtCore import Qt

SUPPORTED_LANGUAGES = ("ar", "en")

_TRANSLATIONS = {
    "app_title": {"ar": "برنامج تحميل الفيديوهات", "en": "Video Downloader"},
    "url_placeholder": {
        "ar": "الصق رابط الفيديو أو قائمة التشغيل (يوتيوب، فيميو، تويتر، وغيرها)...",
        "en": "Paste a video or playlist link (YouTube, Vimeo, Twitter, and more)...",
    },
    "fetch_button": {"ar": "جلب المعلومات", "en": "Fetch Info"},
    "select_all_button": {"ar": "تحديد الكل", "en": "Select All"},
    "deselect_all_button": {"ar": "إلغاء تحديد الكل", "en": "Deselect All"},
    "quality_label": {"ar": "الجودة / الصيغة:", "en": "Quality / Format:"},
    "browse_button": {"ar": "استعراض...", "en": "Browse..."},
    "download_button": {"ar": "بدء التحميل", "en": "Start Download"},
    "pause_button": {"ar": "إيقاف مؤقت", "en": "Pause"},
    "resume_button": {"ar": "استكمال", "en": "Resume"},
    "stop_button": {"ar": "إيقاف", "en": "Stop"},
    "log_label": {"ar": "سجل الحالة:", "en": "Status Log:"},
    "log_paused": {"ar": "تم الإيقاف المؤقت. اضغط \"استكمال\" للمتابعة من نفس النقطة.", "en": "Paused. Click \"Resume\" to continue from the same point."},
    "audio_video_tag": {"ar": "فيديو + صوت", "en": "video + audio"},
    "video_only_tag": {"ar": "فيديو فقط، بدون صوت", "en": "video only, no audio"},
    "audio_only_tag": {"ar": "صوت فقط", "en": "audio only"},
    "subtitles_checkbox": {"ar": "تحميل الترجمة (SRT)", "en": "Download subtitles (SRT)"},
    "subtitles_lang_placeholder": {"ar": "رموز اللغات، مثال: ar,en", "en": "Language codes, e.g. ar,en"},
    "description_checkbox": {"ar": "تحميل وصف الفيديو (TXT)", "en": "Download video description (TXT)"},
    "tab_download": {"ar": "تحميل", "en": "Download"},
    "tab_queue": {"ar": "قائمة الانتظار", "en": "Queue"},
    "queue_links_placeholder": {
        "ar": "الصق رابط واحد في كل سطر لإضافته للقائمة...",
        "en": "Paste one link per line to add to the queue...",
    },
    "queue_add_button": {"ar": "إضافة للقائمة", "en": "Add to Queue"},
    "queue_mode_label": {"ar": "طريقة التحميل:", "en": "Download mode:"},
    "queue_mode_sequential": {"ar": "متتابع", "en": "Sequential"},
    "queue_mode_parallel": {"ar": "متوازي", "en": "Parallel"},
    "queue_max_parallel_label": {"ar": "أقصى عدد متزامن:", "en": "Max concurrent:"},
    "queue_start_button": {"ar": "بدء تحميل القائمة", "en": "Start Queue"},
    "queue_pause_button": {"ar": "إيقاف مؤقت", "en": "Pause"},
    "queue_resume_button": {"ar": "استكمال", "en": "Resume"},
    "queue_stop_button": {"ar": "إيقاف القائمة", "en": "Stop Queue"},
    "queue_column_link": {"ar": "الرابط", "en": "Link"},
    "queue_column_status": {"ar": "الحالة", "en": "Status"},
    "queue_column_progress": {"ar": "التقدم", "en": "Progress"},
    "queue_status_waiting": {"ar": "بالانتظار", "en": "Waiting"},
    "queue_status_downloading": {"ar": "جارٍ التحميل", "en": "Downloading"},
    "queue_status_paused": {"ar": "متوقف مؤقتًا", "en": "Paused"},
    "queue_status_done": {"ar": "تم", "en": "Done"},
    "queue_status_failed": {"ar": "فشل", "en": "Failed"},
    "menu_language": {"ar": "اللغة", "en": "Language"},
    "menu_theme": {"ar": "المظهر", "en": "Theme"},
    "theme_light": {"ar": "فاتح", "en": "Light"},
    "theme_dark": {"ar": "داكن", "en": "Dark"},
    "lang_ar": {"ar": "العربية", "en": "Arabic"},
    "lang_en": {"ar": "الإنجليزية", "en": "English"},
    "warn_title": {"ar": "تنبيه", "en": "Notice"},
    "error_title": {"ar": "خطأ", "en": "Error"},
    "warn_need_url": {"ar": "من فضلك أدخل رابط الفيديو أو قائمة التشغيل أولاً.", "en": "Please enter a video or playlist link first."},
    "warn_need_fetch": {"ar": "من فضلك اجلب معلومات الرابط أولاً.", "en": "Please fetch the link info first."},
    "warn_need_path": {"ar": "من فضلك اختر مسار الحفظ.", "en": "Please choose a save location."},
    "warn_need_selection": {"ar": "لم يتم تحديد أي فيديو للتحميل.", "en": "No video selected for download."},
    "fetch_failed": {"ar": "تعذّر جلب معلومات الرابط:\n{error}", "en": "Failed to fetch link info:\n{error}"},
    "no_title": {"ar": "بدون عنوان", "en": "Untitled"},
    "best_quality": {"ar": "أفضل جودة متاحة", "en": "Best available quality"},
    "quality_1080p": {"ar": "1080p فأقل", "en": "1080p or lower"},
    "quality_720p": {"ar": "720p فأقل", "en": "720p or lower"},
    "quality_480p": {"ar": "480p فأقل", "en": "480p or lower"},
    "quality_360p": {"ar": "360p فأقل", "en": "360p or lower"},
}


def tr(key: str, lang: str, **kwargs) -> str:
    """يرجع النص المترجم لمفتاح معيّن باللغة المطلوبة، مع دعم القيم المتغيرة عبر kwargs."""
    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("ar", key))
    return text.format(**kwargs) if kwargs else text


def layout_direction_for(lang: str):
    """يرجع اتجاه الواجهة المناسب للغة (عربي = من اليمين لليسار)."""
    return Qt.RightToLeft if lang == "ar" else Qt.LeftToRight
