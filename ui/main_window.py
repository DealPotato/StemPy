from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.backup import delete_backups_in_root
from core.config import AppSettings, load_settings, save_settings
from core.logger import logger
from core.runtime_check import run_runtime_check
from core.separator import create_builtin_preset
from core.version import __version__
from ui.advanced_ui import AdvancedPage
from ui.ez_ui import EZPage
from ui.widgets.header import HeaderWidget
from ui.widgets.log_panel import LogPanel
from ui.widgets.mode_switch import ModeSwitch
from ui.widgets.progress_panel import ProgressPanel
from ui.widgets.runtime_panel import RuntimePanel
from ui.widgets.stats_panel import StatsPanel
from ui.widgets.workers import ProcessingWorker, RuntimeSetupWorker, ScanWorker


class MainWindow(QMainWindow):
    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller
        self.settings = load_settings()
        self.processing_worker = None
        self.scan_worker = None
        self.runtime_setup_worker = None
        self.active_processing_page = "ez"

        self.setWindowTitle(f"StemPy v{__version__}")
        self.resize(self.settings.window_width, self.settings.window_height)

        self.header = HeaderWidget()
        self.mode_switch = ModeSwitch()
        self.runtime_panel = RuntimePanel()
        self.stats_panel = StatsPanel()
        self.progress_panel = ProgressPanel()
        self.log_panel = LogPanel()
        self.ez_page = EZPage()
        self.advanced_page = AdvancedPage()

        self.pages = QStackedWidget()
        self.pages.addWidget(self.ez_page)
        self.pages.addWidget(self.advanced_page)
        logger.add_listener(self.log_panel.append_log)

        self.build_layout()
        self.connect_signals()
        self.apply_styles()
        self.apply_saved_settings()
        self.run_startup_checks()

    def build_layout(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(12)
        root_layout.addWidget(self.header)
        root_layout.addWidget(self.mode_switch)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(12)
        sidebar_layout.addWidget(self.runtime_panel)
        sidebar_layout.addWidget(self.stats_panel)
        sidebar_layout.addWidget(self.progress_panel)
        sidebar_layout.addStretch()

        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)
        content_layout.addWidget(self.pages, stretch=4)
        content_layout.addWidget(self.log_panel, stretch=1)
        body_layout.addWidget(sidebar, stretch=1)
        body_layout.addLayout(content_layout, stretch=5)
        root_layout.addLayout(body_layout, stretch=1)
        self.setCentralWidget(root)

    def connect_signals(self):
        self.mode_switch.mode_changed.connect(self.change_mode)
        self.ez_page.scan_requested.connect(lambda folder: self.scan_folder(folder, "ez"))
        self.advanced_page.scan_requested.connect(
            lambda folder: self.scan_folder(folder, "advanced")
        )
        self.ez_page.start_button.clicked.connect(
            lambda: self.start_processing("ez")
        )
        self.advanced_page.start_button.clicked.connect(
            lambda: self.start_processing("advanced")
        )
        self.ez_page.delete_backups_button.clicked.connect(self.delete_backups)
        self.advanced_page.delete_backups_button.clicked.connect(self.delete_backups)
        self.advanced_page.delete_backup_after_success.toggled.connect(
            lambda _checked: self.save_current_settings()
        )
        self.runtime_panel.repair_button.clicked.connect(self.repair_runtime)

    def apply_saved_settings(self):
        settings = self.settings
        for page in (self.ez_page, self.advanced_page):
            page.folder_input.setText(settings.songs_folder)
            page.create_backup.setChecked(settings.create_backup)
            page.skip_processed.setChecked(settings.skip_already_processed)
            page.continue_on_error.setChecked(settings.continue_on_error)

        self._set_combo(self.ez_page.preset_combo, settings.ez_preset)
        self.ez_page.same_format.setChecked(settings.output_format == "same_as_input")
        self._set_combo(self.advanced_page.device_combo, settings.device)
        self._set_combo(
            self.advanced_page.output_format,
            settings.output_format.replace("_", " "),
        )
        self.advanced_page.delete_backup_after_success.setChecked(
            settings.delete_backup_after_success
        )
        self.advanced_page.use_autocast.setChecked(settings.use_autocast)
        self.advanced_page.refresh_presets(settings.advanced_preset)
        selected_preset = self.advanced_page.preset_combo.currentText()
        if selected_preset != "Custom":
            self.advanced_page.load_selected_preset(selected_preset)
        elif settings.advanced_models:
            self.advanced_page.apply_model_state(settings.advanced_models)
        self.mode_switch.set_mode(settings.ui_mode)
        if settings.window_maximized:
            self.showMaximized()

    @staticmethod
    def _set_combo(combo, value: str):
        index = combo.findText(value, Qt.MatchFixedString)
        if index >= 0:
            combo.setCurrentIndex(index)

    def change_mode(self, mode: str):
        self.pages.setCurrentWidget(
            self.ez_page if mode == "ez" else self.advanced_page
        )
        self.settings.ui_mode = mode
        save_settings(self.settings)
        logger.info(f"Switched to {mode.upper()} UI")

    def run_startup_checks(self):
        status = run_runtime_check()
        self.runtime_panel.update_status(status)
        if not status.ready:
            QTimer.singleShot(500, self.offer_runtime_repair)

    def offer_runtime_repair(self):
        if QMessageBox.question(
            self,
            "Runtime components missing",
            "StemPy found missing runtime components. Install or repair them now?\n\n"
            "The first setup may download several GB.",
        ) == QMessageBox.Yes:
            self.repair_runtime()

    def repair_runtime(self):
        if self.runtime_setup_worker is not None and self.runtime_setup_worker.isRunning():
            return
        self.runtime_panel.repair_button.setEnabled(False)
        self.runtime_panel.repair_button.setText("Installing...")
        logger.info("Starting runtime installation/repair")
        self.runtime_setup_worker = RuntimeSetupWorker()
        self.runtime_setup_worker.setup_finished.connect(self.on_runtime_setup_finished)
        self.runtime_setup_worker.finished.connect(self.on_runtime_setup_thread_finished)
        self.runtime_setup_worker.start()

    def on_runtime_setup_finished(self, success: bool, message: str):
        if success:
            logger.success(message)
            status = run_runtime_check()
            self.runtime_panel.update_status(status)
            QMessageBox.information(
                self,
                "Runtime Ready",
                "Runtime setup completed. Restart StemPy before processing songs.",
            )
        else:
            logger.error(f"Runtime setup failed: {message}")
            QMessageBox.critical(self, "Runtime Setup", message)

    def on_runtime_setup_thread_finished(self):
        self.runtime_panel.repair_button.setEnabled(True)
        self.runtime_panel.repair_button.setText("Install / Repair Runtime")
        worker = self.runtime_setup_worker
        self.runtime_setup_worker = None
        if worker is not None:
            worker.deleteLater()

    def scan_folder(self, folder: str, page_name: str):
        if self.scan_worker is not None and self.scan_worker.isRunning():
            QMessageBox.information(self, "StemPy", "A scan is already running.")
            return
        page = self.ez_page if page_name == "ez" else self.advanced_page
        page.scan_button.setEnabled(False)
        page.scan_button.setText("Scanning...")
        logger.info(f"Scan requested: {folder}")
        self.scan_worker = ScanWorker(folder, page.skip_processed.isChecked())
        self.scan_worker.finished_scan.connect(
            lambda report, name=page_name: self.on_scan_finished(report, name)
        )
        self.scan_worker.failed_scan.connect(self.on_scan_failed)
        self.scan_worker.finished.connect(self.on_scan_thread_finished)
        self.scan_worker.start()
        self.settings.songs_folder = folder
        save_settings(self.settings)

    def on_scan_finished(self, report, page_name: str):
        page = self.ez_page if page_name == "ez" else self.advanced_page
        self.stats_panel.update_from_scan_report(report)
        page.song_table.load_songs(report.ready_songs)
        page.update_selected_count(0)
        logger.success(f"Loaded {report.ready_count} songs into table")

    def on_scan_failed(self, message: str):
        logger.error(f"Scan failed: {message}")
        QMessageBox.critical(self, "Scan Error", message)

    def on_scan_thread_finished(self):
        for page in (self.ez_page, self.advanced_page):
            page.scan_button.setEnabled(True)
            page.scan_button.setText("Scan")
        worker = self.scan_worker
        self.scan_worker = None
        if worker is not None:
            worker.deleteLater()

    def start_processing(self, page_name: str):
        if self.processing_worker is not None and self.processing_worker.isRunning():
            QMessageBox.information(self, "StemPy", "Processing is already running.")
            return
        page = self.ez_page if page_name == "ez" else self.advanced_page
        songs = page.song_table.get_selected_songs()
        if not songs:
            logger.warning("No songs selected.")
            return

        try:
            if page_name == "ez":
                preset = create_builtin_preset(page.preset_combo.currentText())
                preset.output_format = (
                    "same_as_input" if page.same_format.isChecked() else "ogg"
                )
                preset.create_backup = page.create_backup.isChecked()
                preset.continue_on_error = page.continue_on_error.isChecked()
                preset.use_autocast = self.settings.use_autocast
            else:
                preset = page.build_preset()
        except Exception as ex:
            QMessageBox.critical(self, "Preset Error", str(ex))
            return

        self.active_processing_page = page_name
        logger.info(f"Starting processing: {len(songs)} songs")
        logger.info(f"Preset: {preset.name}")
        self.set_processing_controls(False)
        self.progress_panel.set_progress(0, len(songs))

        self.processing_worker = ProcessingWorker(songs, preset)
        self.processing_worker.progress_changed.connect(self.on_processing_progress)
        self.processing_worker.finished_processing.connect(self.on_processing_finished)
        self.processing_worker.failed_processing.connect(self.on_processing_failed)
        self.processing_worker.finished.connect(self.on_processing_thread_finished)
        self.processing_worker.start()
        self.save_current_settings()

    def on_processing_progress(self, current: int, total: int, song):
        self.progress_panel.set_progress(current, total)
        self.progress_panel.set_current_song(song.artist, song.title)

    def on_processing_finished(self, results: list):
        successful = sum(1 for result in results if result.success)
        failed = len(results) - successful
        logger.success(f"Processing finished: {successful} successful, {failed} failed")
        self.set_processing_controls(True)

    def on_processing_failed(self, error: str):
        logger.error(f"Processing worker failed: {error}")
        self.set_processing_controls(True)

    def on_processing_thread_finished(self):
        worker = self.processing_worker
        self.processing_worker = None
        if worker is not None:
            worker.deleteLater()

    def set_processing_controls(self, enabled: bool):
        for page in (self.ez_page, self.advanced_page):
            page.start_button.setEnabled(enabled)
            if enabled:
                page.update_selected_count(page.song_table.selected_count())
            else:
                page.start_button.setText("Processing...")

    def delete_backups(self):
        folder = self.current_page().folder_input.text().strip()
        if not folder:
            return
        if QMessageBox.question(
            self,
            "Delete Backups",
            "Delete every StemPy Backup folder under the selected songs folder?",
        ) != QMessageBox.Yes:
            return
        try:
            count = delete_backups_in_root(folder)
            QMessageBox.information(self, "Delete Backups", f"Deleted {count} backup folders.")
        except Exception as ex:
            QMessageBox.critical(self, "Delete Backups", str(ex))

    def current_page(self):
        return self.ez_page if self.pages.currentWidget() is self.ez_page else self.advanced_page

    def save_current_settings(self):
        active = self.current_page()
        self.settings.songs_folder = active.folder_input.text().strip()
        self.settings.ui_mode = "ez" if active is self.ez_page else "advanced"
        self.settings.ez_preset = self.ez_page.preset_combo.currentText()
        self.settings.advanced_preset = self.advanced_page.preset_combo.currentText()
        if active is self.ez_page:
            self.settings.output_format = (
                "same_as_input" if self.ez_page.same_format.isChecked() else "ogg"
            )
        else:
            self.settings.output_format = (
                self.advanced_page.output_format.currentText()
                .casefold()
                .replace(" ", "_")
            )
        self.settings.device = self.advanced_page.device_combo.currentText().casefold()
        self.settings.create_backup = active.create_backup.isChecked()
        self.settings.skip_already_processed = active.skip_processed.isChecked()
        self.settings.continue_on_error = active.continue_on_error.isChecked()
        self.settings.delete_backup_after_success = self.advanced_page.delete_backup_after_success.isChecked()
        self.settings.use_autocast = self.advanced_page.use_autocast.isChecked()
        self.settings.advanced_models = self.advanced_page.export_model_state()
        if not self.isMaximized():
            self.settings.window_width = self.width()
            self.settings.window_height = self.height()
        self.settings.window_maximized = self.isMaximized()
        save_settings(self.settings)

    def closeEvent(self, event):
        if self.runtime_setup_worker is not None and self.runtime_setup_worker.isRunning():
            QMessageBox.information(
                self,
                "Runtime setup in progress",
                "Wait for runtime setup to finish before closing StemPy.",
            )
            event.ignore()
            return
        if self.scan_worker is not None and self.scan_worker.isRunning():
            if not self.scan_worker.wait(10000):
                QMessageBox.information(
                    self,
                    "Scan in progress",
                    "Wait for the current scan to finish before closing StemPy.",
                )
                event.ignore()
                return
        if self.processing_worker is not None and self.processing_worker.isRunning():
            if QMessageBox.question(
                self,
                "Processing in progress",
                "Cancel processing and close StemPy?",
            ) != QMessageBox.Yes:
                event.ignore()
                return
            self.processing_worker.cancel()
            if not self.processing_worker.wait(10000):
                QMessageBox.warning(
                    self,
                    "Still stopping",
                    "The active model is still stopping. Try closing again in a moment.",
                )
                event.ignore()
                return
        self.save_current_settings()
        super().closeEvent(event)

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #12121a; color: #f2f2f5; font-family: "Segoe UI Variable", "Segoe UI"; font-size: 13px; }
            #TitleLabel { font-size: 32px; font-weight: 800; }
            #SubtitleLabel { color: #aaaabd; font-size: 14px; }
            #Sidebar, QGroupBox { background-color: #181824; border: 1px solid #303044; border-radius: 8px; }
            QGroupBox { margin-top: 8px; padding-top: 10px; font-weight: 700; }
            QLabel { color: #f2f2f5; }
            QPushButton { background-color: #242436; border: 1px solid #3a3a52; border-radius: 6px; padding: 8px 12px; font-weight: 600; }
            QPushButton:hover { background-color: #2f2f46; }
            QPushButton:checked { background-color: #6f55dd; color: white; border-color: #8f79ef; }
            QPushButton:disabled { color: #777789; background-color: #1b1b28; }
            QLineEdit, QComboBox, QPlainTextEdit, QTableWidget { background-color: #181824; border: 1px solid #303044; border-radius: 6px; padding: 6px; color: #f2f2f5; }
            QTableWidget { gridline-color: #303044; }
            QHeaderView::section { background-color: #242436; color: #f2f2f5; padding: 7px; border: 0; }
            QProgressBar { background-color: #242436; border: 1px solid #303044; border-radius: 6px; text-align: center; height: 17px; }
            QProgressBar::chunk { background-color: #6f55dd; border-radius: 5px; }
            QCheckBox { spacing: 7px; }
            #PanelTitle { color: #ffffff; font-weight: 800; font-size: 12px; }
            #RuntimeStatus { color: #55dd88; font-weight: 700; }
        """)
