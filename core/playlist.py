"""أدوات مساعدة للتعامل مع روابط قوائم التشغيل."""


def is_playlist_url(url: str) -> bool:
    """تحقق سريع أولي هل الرابط يبدو رابط قائمة تشغيل (غير مستخدمة حاليًا؛ الفحص الفعلي يتم داخل extractor.get_info)."""
    return "list=" in url or "/playlist" in url


def filter_selected_entries(entries: list, selected_ids: set) -> list:
    """
    يعيد فقط عناصر القائمة اللي ضمن selected_ids.
    مجموعة selected_ids فارغة تعني عمدًا إن المستخدم لم يحدد أي عنصر، فترجع قائمة فارغة.
    """
    return [e for e in entries if e.get("id") in selected_ids]
