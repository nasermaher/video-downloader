"""اختبارات core.playlist.filter_selected_entries."""
from core.playlist import filter_selected_entries


def test_all_entries_selected_returns_all_entries():
    entries = [{"id": "a"}, {"id": "b"}]
    assert filter_selected_entries(entries, {"a", "b"}) == entries


def test_partial_selection_returns_only_selected_entries():
    entries = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    assert filter_selected_entries(entries, {"b"}) == [{"id": "b"}]


def test_empty_selection_returns_empty_list():
    # هذا الاختبار يغطي باگ حقيقي كان موجودًا: إلغاء تحديد كل الفيديوهات
    # كان يحمّل القائمة كاملة بدل ما يحمّل صفر فيديو.
    entries = [{"id": "a"}, {"id": "b"}]
    assert filter_selected_entries(entries, set()) == []
