"""عنصر واجهة قائمة انتظار تحميل عدة روابط منفصلة بالتتابع أو بالتوازي."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QComboBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)

from core.i18n import tr
from core.queue_manager import QueueManager
from core.settings import Settings


class QueueWidget(QWidget):
    """
    يسمح بإضافة عدة روابط منفصلة (فيديوهات فردية من أي موقع يدعمه yt-dlp) لقائمة
    انتظار، واختيار تحميلها بالتتابع (واحد تلو الآخر) أو بالتوازي (عدة تحميلات
    في نفس الوقت بحد أقصى قابل للتحديد). كل عنصر يُحمَّل بأفضل جودة متاحة تلقائيًا.
    """

    def __init__(self, settings: Settings, get_output_dir, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._get_output_dir = get_output_dir
        self.lang = settings.get("language", "ar")
        self.manager = None
        self._is_paused = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.links_input = QPlainTextEdit()
        self.links_input.setFixedHeight(80)
        layout.addWidget(self.links_input)

        self.add_button = QPushButton()
        self.add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(self.add_button)

        layout.addLayout(self._build_controls_row())
        layout.addLayout(self._build_buttons_row())

        self.table = QTableWidget(0, 3)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.retranslate(self.lang)

    def _build_controls_row(self):
        row = QHBoxLayout()
        self.mode_label = QLabel()
        self.mode_combo = QComboBox()
        self.max_parallel_label = QLabel()
        self.max_parallel_spin = QSpinBox()
        self.max_parallel_spin.setRange(1, 10)
        self.max_parallel_spin.setValue(self.settings.get("queue_max_parallel", 3))
        row.addWidget(self.mode_label)
        row.addWidget(self.mode_combo)
        row.addWidget(self.max_parallel_label)
        row.addWidget(self.max_parallel_spin)
        return row

    def _build_buttons_row(self):
        row = QHBoxLayout()
        self.start_button = QPushButton()
        self.start_button.clicked.connect(self._on_start_clicked)
        self.pause_button = QPushButton()
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.stop_button = QPushButton()
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        row.addWidget(self.start_button)
        row.addWidget(self.pause_button)
        row.addWidget(self.stop_button)
        return row

    # ---------- الترجمة ----------
    def retranslate(self, lang: str):
        self.lang = lang
        self.links_input.setPlaceholderText(tr("queue_links_placeholder", lang))
        self.add_button.setText(tr("queue_add_button", lang))
        self.mode_label.setText(tr("queue_mode_label", lang))
        self.max_parallel_label.setText(tr("queue_max_parallel_label", lang))
        self.start_button.setText(tr("queue_start_button", lang))
        self.stop_button.setText(tr("queue_stop_button", lang))
        self.table.setHorizontalHeaderLabels([
            tr("queue_column_link", lang),
            tr("queue_column_status", lang),
            tr("queue_column_progress", lang),
        ])
        self._retranslate_mode_combo(lang)
        self._retranslate_status_column(lang)
        self._update_pause_button_text()

    def _update_pause_button_text(self):
        key = "queue_resume_button" if self._is_paused else "queue_pause_button"
        self.pause_button.setText(tr(key, self.lang))

    def _retranslate_mode_combo(self, lang: str):
        current_data = self.mode_combo.currentData()
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        self.mode_combo.addItem(tr("queue_mode_sequential", lang), "sequential")
        self.mode_combo.addItem(tr("queue_mode_parallel", lang), "parallel")
        if current_data:
            index = self.mode_combo.findData(current_data)
            if index >= 0:
                self.mode_combo.setCurrentIndex(index)
        self.mode_combo.blockSignals(False)

    def _retranslate_status_column(self, lang: str):
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 1)
            status_key = status_item.data(Qt.UserRole) if status_item else None
            if status_key:
                status_item.setText(tr(status_key, lang))

    # ---------- إضافة روابط ----------
    def _on_add_clicked(self):
        links = [line.strip() for line in self.links_input.toPlainText().splitlines() if line.strip()]
        for url in links:
            self._add_row(url)
        self.links_input.clear()

    def _add_row(self, url: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(url))
        self._set_status(row, "queue_status_waiting")
        self.table.setItem(row, 2, QTableWidgetItem("0%"))

    def _set_status(self, row: int, status_key: str):
        item = QTableWidgetItem(tr(status_key, self.lang))
        item.setData(Qt.UserRole, status_key)
        self.table.setItem(row, 1, item)

    # ---------- تشغيل القائمة ----------
    def _on_start_clicked(self):
        if self.table.rowCount() == 0:
            return
        output_dir = self._get_output_dir()
        if not output_dir:
            QMessageBox.warning(self, tr("warn_title", self.lang), tr("warn_need_path", self.lang))
            return

        self.manager = self._create_manager(output_dir)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self._is_paused = False
        self._update_pause_button_text()
        self.manager.start(self.mode_combo.currentData())

    def _create_manager(self, output_dir: str) -> QueueManager:
        max_parallel = self.max_parallel_spin.value()
        self.settings.set("queue_max_parallel", max_parallel)

        manager = QueueManager(
            output_dir=output_dir,
            delay_seconds=self.settings.get("download_delay_seconds", 2.0),
            max_parallel=max_parallel,
        )
        for row in range(self.table.rowCount()):
            manager.add(self.table.item(row, 0).text())

        manager.item_status_changed.connect(self._on_item_status_changed)
        manager.item_progress.connect(self._on_item_progress)
        manager.queue_finished.connect(self._on_queue_finished)
        return manager

    def _on_pause_clicked(self):
        if not self.manager:
            return
        if self._is_paused:
            self.manager.resume()
        else:
            self.manager.pause()
        self._is_paused = not self._is_paused
        self._update_pause_button_text()

    def _on_stop_clicked(self):
        if self.manager:
            self.manager.stop()
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self._is_paused = False
        self._update_pause_button_text()

    # ---------- إشارات التقدم ----------
    def _on_item_status_changed(self, index: int, status_key: str):
        self._set_status(index, status_key)

    def _on_item_progress(self, index: int, percent: float):
        self.table.setItem(index, 2, QTableWidgetItem(f"{percent:.0f}%"))

    def _on_queue_finished(self):
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self._is_paused = False
        self._update_pause_button_text()
