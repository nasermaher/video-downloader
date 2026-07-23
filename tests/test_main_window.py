"""اختبارات دخان لعناصر MainWindow الحرجة."""
from gui.main_window import MainWindow


def _playlist_info():
    return {
        "is_playlist": True,
        "title": "Test Playlist",
        "entries": [{"id": "a", "title": "A", "url": "http://x/a"}],
    }


def _single_video_info():
    return {
        "is_playlist": False,
        "title": "My Video",
        "url": "http://x/video",
        "formats": [
            {
                "format_id": "137",
                "ext": "mp4",
                "resolution": "1920x1080",
                "vcodec": "avc1",
                "acodec": "none",
                "has_video": True,
                "has_audio": False,
            },
            {
                "format_id": "22",
                "ext": "mp4",
                "resolution": "1280x720",
                "vcodec": "avc1",
                "acodec": "mp4a",
                "has_video": True,
                "has_audio": True,
            },
            {
                "format_id": "140",
                "ext": "m4a",
                "resolution": "audio",
                "vcodec": "none",
                "acodec": "mp4a",
                "has_video": False,
                "has_audio": True,
            },
        ],
    }


def test_playlist_quality_combo_offers_multiple_resolution_presets(qapp):
    # اختبار يغطي باگ حقيقي: قائمة التشغيل كانت تعرض خيار جودة واحد ثابت فقط.
    window = MainWindow()
    window._populate_playlist_ui(_playlist_info())

    assert window.quality_combo.count() == 5
    labels = [window.quality_combo.itemText(i) for i in range(window.quality_combo.count())]
    assert any("1080" in label for label in labels)
    assert any("720" in label for label in labels)
    assert any("480" in label for label in labels)
    assert any("360" in label for label in labels)


def test_playlist_quality_selection_survives_language_switch(qapp):
    window = MainWindow()
    window._populate_playlist_ui(_playlist_info())

    window.quality_combo.setCurrentIndex(2)  # 720p
    selected_format = window.quality_combo.currentData()

    window._set_language("en")

    assert window.quality_combo.currentData() == selected_format
    assert window.quality_combo.count() == 5


def test_single_video_quality_labels_state_whether_audio_is_included(qapp):
    window = MainWindow()
    window._populate_single_video_ui(_single_video_info())

    labels = [window.quality_combo.itemText(i) for i in range(window.quality_combo.count())]

    assert any("1920x1080" in label and "بدون صوت" in label for label in labels)
    assert any("1280x720" in label and "فيديو + صوت" in label for label in labels)
    assert any("audio" in label and "صوت فقط" in label for label in labels)


def test_video_only_format_is_merged_with_best_audio_for_download(qapp):
    window = MainWindow()
    window._populate_single_video_ui(_single_video_info())

    # الصيغة الأولى (137) فيديو فقط بدون صوت؛ لازم يتضاف لها bestaudio تلقائيًا عند التحميل
    assert window.quality_combo.itemData(0) == "137+bestaudio/best"
    # الصيغة الثانية (22) أصلاً فيها فيديو وصوت؛ متتغيرش
    assert window.quality_combo.itemData(1) == "22"
