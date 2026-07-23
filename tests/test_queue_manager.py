"""اختبارات core.queue_manager.QueueManager (بتزييف حد النظام الخارجي yt_dlp.YoutubeDL فقط)."""
from PyQt5.QtCore import QEventLoop, QTimer

import core.downloader as downloader_module
from core.queue_manager import QueueManager


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


def _run_queue_to_completion(monkeypatch, mode: str, url_count: int, max_parallel: int = 3) -> dict:
    monkeypatch.setattr(downloader_module.yt_dlp, "YoutubeDL", _InstantFakeYDL)

    manager = QueueManager(output_dir="/tmp", delay_seconds=0, max_parallel=max_parallel)
    for i in range(url_count):
        manager.add(f"http://example.com/{i}")

    status_history = {}
    manager.item_status_changed.connect(lambda index, key: status_history.setdefault(index, []).append(key))

    loop = QEventLoop()
    manager.queue_finished.connect(loop.quit)
    manager.start(mode)
    loop.exec_()
    return status_history


def test_sequential_mode_downloads_every_item(qapp, monkeypatch):
    status_history = _run_queue_to_completion(monkeypatch, "sequential", url_count=3)

    assert len(status_history) == 3
    assert all(history[-1] == "queue_status_done" for history in status_history.values())


def test_parallel_mode_downloads_every_item(qapp, monkeypatch):
    status_history = _run_queue_to_completion(monkeypatch, "parallel", url_count=5, max_parallel=2)

    assert len(status_history) == 5
    assert all(history[-1] == "queue_status_done" for history in status_history.values())


def test_pause_then_resume_completes_all_items_sequential(qapp, monkeypatch):
    monkeypatch.setattr(downloader_module.yt_dlp, "YoutubeDL", _InstantFakeYDL)

    manager = QueueManager(output_dir="/tmp", delay_seconds=1.0, max_parallel=3)
    for i in range(3):
        manager.add(f"http://example.com/{i}")

    status_history = {}
    manager.item_status_changed.connect(lambda index, key: status_history.setdefault(index, []).append(key))

    loop = QEventLoop()
    manager.queue_finished.connect(loop.quit)

    manager.start("sequential")
    QTimer.singleShot(100, manager.pause)   # يوقف مؤقتًا أثناء فترة الانتظار بين العنصر الأول والثاني
    QTimer.singleShot(300, manager.resume)
    loop.exec_()

    assert len(status_history) == 3
    assert all(history[-1] == "queue_status_done" for history in status_history.values())


def test_pause_then_resume_completes_all_items_parallel(qapp, monkeypatch):
    monkeypatch.setattr(downloader_module.yt_dlp, "YoutubeDL", _InstantFakeYDL)

    manager = QueueManager(output_dir="/tmp", delay_seconds=0, max_parallel=2)
    for i in range(4):
        manager.add(f"http://example.com/{i}")

    status_history = {}
    manager.item_status_changed.connect(lambda index, key: status_history.setdefault(index, []).append(key))

    loop = QEventLoop()
    manager.queue_finished.connect(loop.quit)

    manager.start("parallel")
    manager.pause()  # قبل ما أي worker يبدأ التنفيذ الفعلي (QThread.start غير متزامن)
    QTimer.singleShot(150, manager.resume)
    loop.exec_()

    assert len(status_history) == 4
    assert all(history[-1] == "queue_status_done" for history in status_history.values())
