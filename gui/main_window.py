"""النافذة الرئيسية لبرنامج تحميل الفيديوهات."""
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QPlainTextEdit,
    QTabWidget,
)
from PyQt5.QtCore import Qt

from core.extractor import get_info, ExtractionError
from core.playlist import filter_selected_entries
from core.downloader import DownloadWorker, DownloadOptions
from core.settings import Settings
from core.logger import get_logger
from core.i18n import tr, layout_direction_for
from core.theme import stylesheet_for
from gui.queue_widget import QueueWidget

logger = get_logger()

DEFAULT_DOWNLOAD_DELAY_SECONDS = 2.0

# اختيارات جودة عامة لقوائم التشغيل: بدل جلب صيغ كل فيديو على حدة (بطيء لقائمة كبيرة)،
# بنستخدم صيغ yt-dlp العامة اللي بتحدد أقصى دقة وتترك له اختيار أفضل صيغة متاحة تحتها.
PLAYLIST_QUALITY_PRESETS = [
    ("best_quality", "bestvideo+bestaudio/best"),
    ("quality_1080p", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"),
    ("quality_720p", "bestvideo[height<=720]+bestaudio/best[height<=720]"),
    ("quality_480p", "bestvideo[height<=480]+bestaudio/best[height<=480]"),
    ("quality_360p", "bestvideo[height<=360]+bestaudio/best[height<=360]"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.lang = self.settings.get("language", "ar")
        self.current_info = None
        self.worker = None
        self._paused_download_state = None  # dict{"remaining_urls", "options"} أثناء الإيقاف المؤقت

        self.resize(750, 700)
        self._build_menu()
        self._build_ui()
        self._apply_theme(self.settings.get("theme", "light"))
        self._retranslate_ui()

    # ---------- شريط القوائم (اللغة والمظهر) ----------
    def _build_menu(self):
        menu_bar = self.menuBar()
        self.language_menu = menu_bar.addMenu("")
        self.action_lang_ar = self.language_menu.addAction("", lambda: self._set_language("ar"))
        self.action_lang_en = self.language_menu.addAction("", lambda: self._set_language("en"))

        self.theme_menu = menu_bar.addMenu("")
        self.action_theme_light = self.theme_menu.addAction("", lambda: self._set_theme("light"))
        self.action_theme_dark = self.theme_menu.addAction("", lambda: self._set_theme("dark"))

    def _set_language(self, lang: str):
        self.lang = lang
        self.settings.set("language", lang)
        QApplication.instance().setLayoutDirection(layout_direction_for(lang))
        self._retranslate_ui()

    def _set_theme(self, theme: str):
        self.settings.set("theme", theme)
        self._apply_theme(theme)

    def _apply_theme(self, theme: str):
        QApplication.instance().setStyleSheet(stylesheet_for(theme))

    # ---------- بناء الواجهة ----------
    def _build_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self._build_download_tab(), "")
        self.queue_widget = QueueWidget(self.settings, lambda: self.path_input.text().strip())
        self.tabs.addTab(self.queue_widget, "")

    def _build_download_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addLayout(self._build_url_row())
        layout.addWidget(self._build_title_label())
        layout.addWidget(self._build_playlist_section())
        layout.addLayout(self._build_quality_row())
        layout.addLayout(self._build_extra_options_row())
        layout.addLayout(self._build_path_row())
        layout.addLayout(self._build_download_controls_row())
        layout.addWidget(self._build_progress_bar())
        self.log_label = QLabel()
        layout.addWidget(self.log_label)
        layout.addWidget(self._build_log_view())
        return tab

    def _build_url_row(self):
        row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.fetch_button = QPushButton()
        self.fetch_button.clicked.connect(self.on_fetch_clicked)
        row.addWidget(self.url_input)
        row.addWidget(self.fetch_button)
        return row

    def _build_title_label(self):
        self.title_label = QLabel("—")
        self.title_label.setWordWrap(True)
        return self.title_label

    def _build_playlist_section(self):
        """يبني قسم قائمة التشغيل كاملاً (أزرار تحديد الكل/إلغاء الكل + قائمة الفيديوهات) في حاوية واحدة قابلة للإخفاء دفعة واحدة."""
        container = QWidget()
        section_layout = QVBoxLayout(container)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.addLayout(self._build_playlist_controls_row())

        self.entries_list = QListWidget()
        self.entries_list.setSelectionMode(QListWidget.NoSelection)
        section_layout.addWidget(self.entries_list)

        self.playlist_section = container
        self.playlist_section.hide()
        return container

    def _build_playlist_controls_row(self):
        row = QHBoxLayout()
        self.select_all_button = QPushButton()
        self.select_all_button.clicked.connect(lambda: self._set_all_entries_checked(True))
        self.deselect_all_button = QPushButton()
        self.deselect_all_button.clicked.connect(lambda: self._set_all_entries_checked(False))
        row.addWidget(self.select_all_button)
        row.addWidget(self.deselect_all_button)
        return row

    def _build_quality_row(self):
        row = QHBoxLayout()
        self.quality_label = QLabel()
        row.addWidget(self.quality_label)
        self.quality_combo = QComboBox()
        row.addWidget(self.quality_combo)
        return row

    def _build_extra_options_row(self):
        row = QHBoxLayout()
        self.subtitles_checkbox = QCheckBox()
        self.subtitles_checkbox.setChecked(self.settings.get("download_subtitles", False))
        self.subtitle_langs_input = QLineEdit(self.settings.get("subtitle_langs", "ar,en"))
        self.subtitle_langs_input.setFixedWidth(120)
        self.description_checkbox = QCheckBox()
        self.description_checkbox.setChecked(self.settings.get("download_description", False))
        row.addWidget(self.subtitles_checkbox)
        row.addWidget(self.subtitle_langs_input)
        row.addWidget(self.description_checkbox)
        return row

    def _build_path_row(self):
        row = QHBoxLayout()
        self.path_input = QLineEdit(self.settings.get("last_download_path"))
        self.browse_button = QPushButton()
        self.browse_button.clicked.connect(self.on_browse_clicked)
        row.addWidget(self.path_input)
        row.addWidget(self.browse_button)
        return row

    def _build_download_controls_row(self):
        row = QHBoxLayout()
        self.download_button = QPushButton()
        self.download_button.clicked.connect(self.on_download_clicked)
        self.pause_button = QPushButton()
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.stop_button = QPushButton()
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.on_stop_clicked)
        row.addWidget(self.download_button)
        row.addWidget(self.pause_button)
        row.addWidget(self.stop_button)
        return row

    def _build_progress_bar(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        return self.progress_bar

    def _build_log_view(self):
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        return self.log_view

    # ---------- الترجمة ----------
    def _retranslate_ui(self):
        self.setWindowTitle(tr("app_title", self.lang))
        self.url_input.setPlaceholderText(tr("url_placeholder", self.lang))
        self.fetch_button.setText(tr("fetch_button", self.lang))
        self.select_all_button.setText(tr("select_all_button", self.lang))
        self.deselect_all_button.setText(tr("deselect_all_button", self.lang))
        self.quality_label.setText(tr("quality_label", self.lang))
        self.subtitles_checkbox.setText(tr("subtitles_checkbox", self.lang))
        self.subtitle_langs_input.setPlaceholderText(tr("subtitles_lang_placeholder", self.lang))
        self.description_checkbox.setText(tr("description_checkbox", self.lang))
        self.browse_button.setText(tr("browse_button", self.lang))
        self.download_button.setText(tr("download_button", self.lang))
        self.stop_button.setText(tr("stop_button", self.lang))
        self.log_label.setText(tr("log_label", self.lang))
        self.tabs.setTabText(0, tr("tab_download", self.lang))
        self.tabs.setTabText(1, tr("tab_queue", self.lang))
        self._retranslate_menu()
        self._retranslate_playlist_quality_combo()
        self._update_pause_button_text()
        self.queue_widget.retranslate(self.lang)

    def _update_pause_button_text(self):
        key = "resume_button" if self._paused_download_state else "pause_button"
        self.pause_button.setText(tr(key, self.lang))

    def _retranslate_playlist_quality_combo(self):
        if not self.current_info or not self.current_info.get("is_playlist"):
            return
        selected_format = self.quality_combo.currentData()
        self.quality_combo.blockSignals(True)
        self._fill_playlist_quality_presets()
        index = self.quality_combo.findData(selected_format)
        if index >= 0:
            self.quality_combo.setCurrentIndex(index)
        self.quality_combo.blockSignals(False)

    def _retranslate_menu(self):
        self.language_menu.setTitle(tr("menu_language", self.lang))
        self.action_lang_ar.setText(tr("lang_ar", self.lang))
        self.action_lang_en.setText(tr("lang_en", self.lang))
        self.theme_menu.setTitle(tr("menu_theme", self.lang))
        self.action_theme_light.setText(tr("theme_light", self.lang))
        self.action_theme_dark.setText(tr("theme_dark", self.lang))

    # ---------- جلب المعلومات ----------
    def on_fetch_clicked(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, tr("warn_title", self.lang), tr("warn_need_url", self.lang))
            return

        self._log(f"{tr('fetch_button', self.lang)}: {url}")
        try:
            info = get_info(url)
        except ExtractionError as e:
            QMessageBox.critical(self, tr("error_title", self.lang), tr("fetch_failed", self.lang, error=e))
            self._log(str(e))
            return

        self.current_info = info
        if info["is_playlist"]:
            self._populate_playlist_ui(info)
        else:
            self._populate_single_video_ui(info)

    def _populate_playlist_ui(self, info):
        self.title_label.setText(f"{info['title']} ({len(info['entries'])})")

        self.entries_list.clear()
        for entry in info["entries"]:
            item = QListWidgetItem(entry["title"] or entry["url"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, entry)
            self.entries_list.addItem(item)
        self.playlist_section.show()

        self._fill_playlist_quality_presets()

    def _fill_playlist_quality_presets(self):
        self.quality_combo.clear()
        for label_key, format_selector in PLAYLIST_QUALITY_PRESETS:
            self.quality_combo.addItem(tr(label_key, self.lang), format_selector)

    def _populate_single_video_ui(self, info):
        self.title_label.setText(info["title"] or tr("no_title", self.lang))
        self.playlist_section.hide()

        self.quality_combo.clear()
        for fmt in info["formats"]:
            label = f"{fmt['resolution']} - {fmt['ext']} ({self._audio_tag(fmt)})"
            self.quality_combo.addItem(label, self._format_selector(fmt))

    def _audio_tag(self, fmt: dict) -> str:
        """يوضّح في اسم كل خيار جودة هل معاه صوت أو لا، لأن يوتيوب غالبًا بيفصل الصوت عن الفيديو."""
        if fmt["has_video"] and fmt["has_audio"]:
            return tr("audio_video_tag", self.lang)
        if fmt["has_video"]:
            return tr("video_only_tag", self.lang)
        return tr("audio_only_tag", self.lang)

    def _format_selector(self, fmt: dict) -> str:
        """لو الصيغة فيديو بدون صوت، بندمج معاها أفضل صوت متاح تلقائيًا عشان الملف النهائي يطلع فيه صوت فعليًا."""
        if fmt["has_video"] and not fmt["has_audio"]:
            return f"{fmt['format_id']}+bestaudio/best"
        return fmt["format_id"]

    def _set_all_entries_checked(self, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.entries_list.count()):
            self.entries_list.item(i).setCheckState(state)

    # ---------- مسار الحفظ ----------
    def on_browse_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, tr("browse_button", self.lang), self.path_input.text())
        if folder:
            self.path_input.setText(folder)
            self.settings.set("last_download_path", folder)

    # ---------- التحميل ----------
    def on_download_clicked(self):
        if not self.current_info:
            QMessageBox.warning(self, tr("warn_title", self.lang), tr("warn_need_fetch", self.lang))
            return

        output_dir = self.path_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, tr("warn_title", self.lang), tr("warn_need_path", self.lang))
            return

        urls = self._get_urls_to_download()
        if not urls:
            QMessageBox.warning(self, tr("warn_title", self.lang), tr("warn_need_selection", self.lang))
            return

        self._start_download(urls, output_dir)

    def _get_urls_to_download(self) -> list:
        if not self.current_info["is_playlist"]:
            return [self.current_info["url"]]

        selected_ids = {
            self.entries_list.item(i).data(Qt.UserRole)["id"]
            for i in range(self.entries_list.count())
            if self.entries_list.item(i).checkState() == Qt.Checked
        }
        entries = filter_selected_entries(self.current_info["entries"], selected_ids)
        return [e["url"] for e in entries]

    def _start_download(self, urls: list, output_dir: str):
        options = self._build_download_options(output_dir)
        self._run_worker(urls, options)

    def _run_worker(self, urls: list, options: DownloadOptions):
        self._paused_download_state = None
        self.download_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self._update_pause_button_text()
        self.progress_bar.setValue(0)

        self.worker = DownloadWorker(urls, options)
        self.worker.progress.connect(self.on_progress)
        self.worker.item_finished.connect(self.on_item_finished)
        self.worker.all_finished.connect(self.on_all_finished)
        self.worker.paused.connect(lambda remaining: self.on_worker_paused(remaining, options))
        self.worker.start()

    def _build_download_options(self, output_dir: str) -> DownloadOptions:
        download_subtitles = self.subtitles_checkbox.isChecked()
        subtitle_langs = self.subtitle_langs_input.text().strip() or "en"
        download_description = self.description_checkbox.isChecked()

        self.settings.set("download_subtitles", download_subtitles)
        self.settings.set("subtitle_langs", subtitle_langs)
        self.settings.set("download_description", download_description)

        return DownloadOptions(
            format_id=self.quality_combo.currentData(),
            output_dir=output_dir,
            delay_seconds=self.settings.get("download_delay_seconds", DEFAULT_DOWNLOAD_DELAY_SECONDS),
            download_subtitles=download_subtitles,
            subtitle_langs=subtitle_langs,
            download_description=download_description,
        )

    def on_pause_clicked(self):
        if self._paused_download_state:
            self._resume_download()
        elif self.worker:
            self.worker.pause()
            self.pause_button.setEnabled(False)  # لحد ما نتأكد إن الإيقاف اتم فعليًا عبر إشارة paused

    def on_worker_paused(self, remaining_urls: list, options: DownloadOptions):
        self._paused_download_state = {"remaining_urls": remaining_urls, "options": options}
        self.pause_button.setEnabled(True)
        self._update_pause_button_text()
        self._log(tr("log_paused", self.lang))

    def _resume_download(self):
        state = self._paused_download_state
        self._run_worker(state["remaining_urls"], state["options"])

    def on_stop_clicked(self):
        if self._paused_download_state:
            self._paused_download_state = None
            self._reset_download_controls()
            return
        if self.worker:
            self.worker.stop()
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)

    def _reset_download_controls(self):
        self.download_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self._update_pause_button_text()

    # ---------- إشارات التحميل ----------
    def on_progress(self, url, percent, status_text):
        self.progress_bar.setValue(int(percent))
        self._log(f"{status_text} - {percent:.1f}%")

    def on_item_finished(self, url, success, message):
        status = "OK" if success else "FAIL"
        self._log(f"[{status}] {url}: {message}")

    def on_all_finished(self):
        self._paused_download_state = None
        self._reset_download_controls()

    # ---------- أدوات مساعدة ----------
    def _log(self, text: str):
        self.log_view.appendPlainText(text)
        logger.info(text)
