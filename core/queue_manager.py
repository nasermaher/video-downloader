"""إدارة قائمة انتظار تحميل عدة روابط منفصلة بالتتابع أو بالتوازي، مع دعم إيقاف مؤقت/استكمال."""
from dataclasses import dataclass

from PyQt5.QtCore import QObject, pyqtSignal

from core.downloader import DownloadOptions, DownloadWorker

QUALITY_BEST = "best"


@dataclass
class QueueItem:
    url: str


class QueueManager(QObject):
    """
    ينسّق تنفيذ عدة روابط منفصلة إما بالتتابع (عامل واحد يمر عليها بالترتيب مع فاصل
    زمني بينها) أو بالتوازي (عدة عمال يعملون في نفس الوقت بحد أقصى max_parallel).
    كل عنصر في القائمة يُحمَّل بأفضل جودة متاحة تلقائيًا.

    يدعم pause()/resume(): الإيقاف المؤقت بيقطع كل العمال النشطين حاليًا (كل واحد
    بيحتفظ بملفه الجزئي)، والاستكمال بيعيد تشغيل نفس العناصر من حيث توقفت.
    """

    item_status_changed = pyqtSignal(int, str)  # index, translation_key
    item_progress = pyqtSignal(int, float)       # index, percent
    queue_finished = pyqtSignal()

    def __init__(self, output_dir: str, delay_seconds: float, max_parallel: int = 3, parent=None):
        super().__init__(parent)
        self.output_dir = output_dir
        self.delay_seconds = delay_seconds
        self.max_parallel = max(1, max_parallel)
        self.items: list[QueueItem] = []

        self._mode = "sequential"
        self._is_paused = False

        self._sequential_worker = None
        self._sequential_resume_index = None

        self._parallel_workers: dict[int, DownloadWorker] = {}
        self._paused_parallel_indices: set = set()
        self._next_index = 0
        self._active_count = 0

    def add(self, url: str):
        self.items.append(QueueItem(url=url))

    def start(self, mode: str):
        self._mode = mode
        if mode == "parallel":
            self._fill_parallel_slots()
        else:
            self._start_sequential_worker(start_index=0)

    def stop(self):
        if self._sequential_worker:
            self._sequential_worker.stop()
        for worker in self._parallel_workers.values():
            worker.stop()

    def pause(self):
        self._is_paused = True
        if self._sequential_worker:
            self._sequential_worker.pause()
        for worker in self._parallel_workers.values():
            worker.pause()

    def resume(self):
        self._is_paused = False
        if self._mode == "sequential":
            if self._sequential_resume_index is not None:
                index = self._sequential_resume_index
                self._sequential_resume_index = None
                self._start_sequential_worker(start_index=index)
        else:
            self._resume_parallel()

    def _download_options(self, delay_seconds: float) -> DownloadOptions:
        return DownloadOptions(format_id=QUALITY_BEST, output_dir=self.output_dir, delay_seconds=delay_seconds)

    # ---------- وضع التتابع ----------
    def _start_sequential_worker(self, start_index: int):
        items_to_run = self.items[start_index:]
        urls = [item.url for item in items_to_run]
        url_to_index = {url: start_index + i for i, url in enumerate(urls)}

        worker = DownloadWorker(urls, self._download_options(self.delay_seconds))
        worker.progress.connect(lambda url, percent, status: self._emit_progress(url_to_index, url, percent))
        worker.item_finished.connect(lambda url, ok, msg: self._emit_status(url_to_index, url, ok))
        worker.paused.connect(lambda remaining: self._on_sequential_paused(start_index, len(items_to_run) - len(remaining)))
        worker.all_finished.connect(self._on_sequential_all_finished)
        self._sequential_worker = worker
        worker.start()

    def _on_sequential_paused(self, previous_start_index: int, items_completed: int):
        self._sequential_resume_index = previous_start_index + items_completed

    def _on_sequential_all_finished(self):
        self._sequential_worker = None
        if not self._is_paused:
            self.queue_finished.emit()

    def _emit_progress(self, url_to_index: dict, url: str, percent: float):
        index = url_to_index.get(url)
        if index is not None:
            self.item_progress.emit(index, percent)

    def _emit_status(self, url_to_index: dict, url: str, success: bool):
        index = url_to_index.get(url)
        if index is not None:
            self.item_status_changed.emit(index, "queue_status_done" if success else "queue_status_failed")

    # ---------- وضع التوازي ----------
    def _fill_parallel_slots(self):
        if self._is_paused:
            return
        while self._active_count < self.max_parallel and self._next_index < len(self.items):
            self._start_worker_for_index(self._next_index)
            self._next_index += 1
            self._active_count += 1

    def _start_worker_for_index(self, index: int):
        worker = DownloadWorker([self.items[index].url], self._download_options(delay_seconds=0))
        worker.progress.connect(lambda url, percent, status, i=index: self.item_progress.emit(i, percent))
        worker.item_finished.connect(lambda url, ok, msg, i=index: self._on_parallel_item_finished(i, ok))
        worker.paused.connect(lambda remaining, i=index: self._on_parallel_item_paused(i))
        self._parallel_workers[index] = worker
        self.item_status_changed.emit(index, "queue_status_downloading")
        worker.start()

    def _on_parallel_item_finished(self, index: int, success: bool):
        self._parallel_workers.pop(index, None)
        self.item_status_changed.emit(index, "queue_status_done" if success else "queue_status_failed")
        self._active_count -= 1
        if self._is_paused:
            return
        if self._next_index < len(self.items):
            self._start_worker_for_index(self._next_index)
            self._next_index += 1
            self._active_count += 1
        elif self._active_count == 0:
            self.queue_finished.emit()

    def _on_parallel_item_paused(self, index: int):
        self._parallel_workers.pop(index, None)
        self._paused_parallel_indices.add(index)
        self._active_count -= 1
        self.item_status_changed.emit(index, "queue_status_paused")

    def _resume_parallel(self):
        resuming_indices = sorted(self._paused_parallel_indices)
        self._paused_parallel_indices.clear()
        for index in resuming_indices:
            self._start_worker_for_index(index)
            self._active_count += 1
        self._fill_parallel_slots()
