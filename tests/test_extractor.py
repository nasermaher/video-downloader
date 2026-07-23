"""اختبارات core.extractor.get_info مع تزييف حد النظام الخارجي (yt_dlp.YoutubeDL) فقط."""
import pytest
import yt_dlp

import core.extractor as extractor_module
from core.extractor import ExtractionError, get_info


class _FakeYoutubeDL:
    """بديل مزيف لـ yt_dlp.YoutubeDL يرجع بيانات محددة مسبقًا بدل الاتصال الفعلي بيوتيوب."""

    def __init__(self, raw_info=None, error=None):
        self._raw_info = raw_info
        self._error = error

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def extract_info(self, url, download=False):
        if self._error:
            raise self._error
        return self._raw_info


def test_single_video_link_returns_available_formats(monkeypatch):
    raw_info = {
        "title": "My Video",
        "duration": 120,
        "thumbnail": "http://example.com/thumb.jpg",
        "webpage_url": "http://example.com/watch?v=xyz",
        "formats": [
            {"format_id": "137", "ext": "mp4", "resolution": "1920x1080", "vcodec": "avc1", "acodec": "none"},
            {"format_id": "140", "ext": "m4a", "format_note": "audio only", "vcodec": "none", "acodec": "mp4a"},
        ],
    }
    monkeypatch.setattr(extractor_module.yt_dlp, "YoutubeDL", lambda opts: _FakeYoutubeDL(raw_info=raw_info))

    info = get_info("http://example.com/watch?v=xyz")

    assert info["is_playlist"] is False
    assert info["title"] == "My Video"
    assert [f["format_id"] for f in info["formats"]] == ["137", "140"]


def test_playlist_link_returns_entries_with_urls(monkeypatch):
    raw_info = {
        "_type": "playlist",
        "title": "My Playlist",
        "entries": [
            {"id": "v1", "title": "Video 1", "webpage_url": "http://example.com/v1"},
            {"id": "v2", "title": "Video 2", "webpage_url": "http://example.com/v2"},
        ],
    }
    monkeypatch.setattr(extractor_module.yt_dlp, "YoutubeDL", lambda opts: _FakeYoutubeDL(raw_info=raw_info))

    info = get_info("http://example.com/playlist?list=abc")

    assert info["is_playlist"] is True
    assert [e["id"] for e in info["entries"]] == ["v1", "v2"]
    assert info["entries"][0]["url"] == "http://example.com/v1"


def test_deleted_video_link_raises_extraction_error(monkeypatch):
    monkeypatch.setattr(
        extractor_module.yt_dlp,
        "YoutubeDL",
        lambda opts: _FakeYoutubeDL(error=yt_dlp.utils.DownloadError("Video unavailable")),
    )

    with pytest.raises(ExtractionError):
        get_info("http://example.com/watch?v=deleted")
