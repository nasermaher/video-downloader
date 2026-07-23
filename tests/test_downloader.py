"""اختبارات منطق حساب التقدم وبناء خيارات yt-dlp وسلوك الإيقاف المؤقت في core.downloader.DownloadWorker."""
from PyQt5.QtCore import QEventLoop

import core.downloader as downloader_module
from core.downloader import DownloadOptions, DownloadWorker


def _make_worker(qapp, **overrides):
    options = DownloadOptions(format_id="best", output_dir="/tmp", **overrides)
    return DownloadWorker(["http://example.com/v1"], options)


def test_progress_hook_computes_percent_from_downloaded_bytes(qapp):
    worker = _make_worker(qapp)
    received = []
    worker.progress.connect(lambda url, percent, status: received.append((url, percent, status)))

    worker._progress_hook("http://example.com/v1", {
        "status": "downloading",
        "downloaded_bytes": 50,
        "total_bytes": 200,
    })

    assert received == [("http://example.com/v1", 25.0, "")]


def test_progress_hook_reports_zero_percent_when_total_size_unknown(qapp):
    # total_bytes=0 يعني حجم غير معروف؛ يجب ألا يقسم على صفر ويرجع 0% بدل استثناء.
    worker = _make_worker(qapp)
    received = []
    worker.progress.connect(lambda url, percent, status: received.append(percent))

    worker._progress_hook("http://example.com/v1", {
        "status": "downloading",
        "downloaded_bytes": 50,
        "total_bytes": 0,
    })

    assert received == [0.0]


def test_progress_hook_reports_full_percent_when_finished(qapp):
    worker = _make_worker(qapp)
    received = []
    worker.progress.connect(lambda url, percent, status: received.append(percent))

    worker._progress_hook("http://example.com/v1", {"status": "finished"})

    assert received == [100.0]


def test_default_opts_enable_resume_and_skip_extras(qapp):
    worker = _make_worker(qapp)
    opts = worker._build_ydl_opts("http://example.com/v1")

    assert opts["continuedl"] is True
    assert opts["nopart"] is False
    assert "writesubtitles" not in opts
    assert "writedescription" not in opts


def test_subtitles_enabled_adds_srt_conversion_with_requested_langs(qapp):
    worker = _make_worker(qapp, download_subtitles=True, subtitle_langs="ar, en")
    opts = worker._build_ydl_opts("http://example.com/v1")

    assert opts["writesubtitles"] is True
    assert opts["subtitleslangs"] == ["ar", "en"]
    assert opts["subtitlesformat"] == "srt"
    assert opts["postprocessors"] == [{"key": "FFmpegSubtitlesConvertor", "format": "srt"}]


def test_description_enabled_writes_txt_extension_matching_video_name(qapp):
    worker = _make_worker(qapp, download_description=True)
    opts = worker._build_ydl_opts("http://example.com/v1")

    assert opts["writedescription"] is True
    assert opts["outtmpl"]["description"].endswith(".txt")
    assert opts["outtmpl"]["description"].startswith(opts["outtmpl"]["default"].rsplit("%(title)s", 1)[0])


def test_ydl_opts_include_bundled_ffmpeg_path_when_available(qapp, monkeypatch):
    monkeypatch.setattr(downloader_module, "get_bundled_ffmpeg_path", lambda: "/opt/app/ffmpeg")
    worker = _make_worker(qapp)

    opts = worker._build_ydl_opts("http://example.com/v1")

    assert opts["ffmpeg_location"] == "/opt/app/ffmpeg"


def test_ydl_opts_omit_ffmpeg_location_in_dev_mode(qapp, monkeypatch):
    monkeypatch.setattr(downloader_module, "get_bundled_ffmpeg_path", lambda: None)
    worker = _make_worker(qapp)

    opts = worker._build_ydl_opts("http://example.com/v1")

    assert "ffmpeg_location" not in opts


class _InstantFakeYDL:
    """بديل مزيف لـ yt_dlp.YoutubeDL ينجح فورًا بدون اتصال فعلي بالشبكة."""

    def __init__(self, opts):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def download(self, urls):
        pass


def test_pausing_before_any_download_emits_all_remaining_urls(qapp, monkeypatch):
    monkeypatch.setattr(downloader_module.yt_dlp, "YoutubeDL", _InstantFakeYDL)

    worker = DownloadWorker(["u1", "u2", "u3"], DownloadOptions(format_id="best", output_dir="/tmp"))
    worker.pause()  # الإيقاف المؤقت مطلوب قبل ما نبدأ التشغيل خالص

    received_paused = []
    loop = QEventLoop()
    worker.paused.connect(lambda remaining: (received_paused.append(remaining), loop.quit()))
    worker.all_finished.connect(loop.quit)
    worker.start()
    loop.exec_()

    assert received_paused == [["u1", "u2", "u3"]]


def test_pausing_during_inter_item_delay_keeps_remaining_urls_only(qapp, monkeypatch):
    monkeypatch.setattr(downloader_module.yt_dlp, "YoutubeDL", _InstantFakeYDL)

    options = DownloadOptions(format_id="best", output_dir="/tmp", delay_seconds=1.0)
    worker = DownloadWorker(["u1", "u2", "u3"], options)

    received_paused = []
    loop = QEventLoop()
    worker.paused.connect(lambda remaining: (received_paused.append(remaining), loop.quit()))
    worker.all_finished.connect(loop.quit)

    # نطلب الإيقاف المؤقت بعد بداية التشغيل بلحظة قصيرة (أثناء فترة الانتظار بين u1 و u2)
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(100, worker.pause)

    worker.start()
    loop.exec_()

    assert received_paused == [["u2", "u3"]]


def test_stop_still_emits_all_finished_not_paused(qapp, monkeypatch):
    monkeypatch.setattr(downloader_module.yt_dlp, "YoutubeDL", _InstantFakeYDL)

    worker = DownloadWorker(["u1", "u2"], DownloadOptions(format_id="best", output_dir="/tmp"))
    worker.stop()

    paused_calls = []
    loop = QEventLoop()
    worker.paused.connect(lambda remaining: paused_calls.append(remaining))
    worker.all_finished.connect(loop.quit)
    worker.start()
    loop.exec_()

    assert paused_calls == []
