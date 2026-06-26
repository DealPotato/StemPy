from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.logger import logger
from core.runtime_check import run_runtime_check
from ui.advanced_ui import AdvancedPage
from ui.ez_ui import EZPage
from ui.widgets.header import HeaderWidget
from ui.widgets.log_panel import LogPanel
from ui.widgets.mode_switch import ModeSwitch
from ui.widgets.progress_panel import ProgressPanel
from ui.widgets.runtime_panel import RuntimePanel
from ui.widgets.stats_panel import StatsPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("StemPy")
        self.resize(1280, 820)

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
        self.run_startup_checks()

    def build_layout(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(28, 24, 28, 24)
        root_layout.setSpacing(16)

        root_layout.addWidget(self.header)
        root_layout.addWidget(self.mode_switch)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(14)

        sidebar_layout.addWidget(self.runtime_panel)
        sidebar_layout.addWidget(self.stats_panel)
        sidebar_layout.addWidget(self.progress_panel)
        sidebar_layout.addStretch()

        content_layout = QVBoxLayout()
        content_layout.setSpacing(16)
        content_layout.addWidget(self.pages, stretch=3)
        content_layout.addWidget(self.log_panel, stretch=1)

        body_layout.addWidget(sidebar, stretch=1)
        body_layout.addLayout(content_layout, stretch=4)

        root_layout.addLayout(body_layout, stretch=1)

        self.setCentralWidget(root)

    def connect_signals(self):
        self.mode_switch.mode_changed.connect(self.change_mode)
        self.ez_page.scan_requested.connect(self.scan_folder)

    def change_mode(self, mode: str):
        if mode == "ez":
            self.pages.setCurrentWidget(self.ez_page)
        else:
            self.pages.setCurrentWidget(self.advanced_page)

        logger.info(f"Switched to {mode.upper()} UI")

    def run_startup_checks(self):
        status = run_runtime_check()
        self.runtime_panel.update_status(status)

    def scan_folder(self, folder: str):
        from core.scanner import scan_clone_hero_folder

        logger.info(f"Scan requested: {folder}")

        report = scan_clone_hero_folder(folder)

        self.stats_panel.update_from_scan_report(report)
        self.ez_page.song_table.load_songs(report.ready_songs)

        logger.success(f"Loaded {report.ready_count} songs into table")
    
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #12121a;
                color: #f2f2f5;
                font-family: "Segoe UI Variable", "Segoe UI";
                font-size: 13px;
            }

            #TitleLabel {
                font-size: 34px;
                font-weight: 800;
            }

            #SubtitleLabel {
                color: #aaaabd;
                font-size: 15px;
            }

            #Sidebar {
                background-color: #181824;
                border: 1px solid #303044;
                border-radius: 16px;
            }

            QLabel {
                color: #f2f2f5;
            }

            QPushButton {
                background-color: #242436;
                border: 1px solid #3a3a52;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #2f2f46;
            }

            QPushButton:checked {
                background-color: #7c5cff;
                color: white;
                border: 1px solid #9b84ff;
            }

            QLineEdit,
            QComboBox,
            QPlainTextEdit,
            QTableWidget {
                background-color: #181824;
                border: 1px solid #303044;
                border-radius: 10px;
                padding: 8px;
                color: #f2f2f5;
            }

            QTableWidget {
                gridline-color: #303044;
            }

            QHeaderView::section {
                background-color: #242436;
                color: #f2f2f5;
                padding: 8px;
                border: 0px;
            }

            QProgressBar {
                background-color: #242436;
                border: 1px solid #303044;
                border-radius: 8px;
                text-align: center;
                height: 18px;
            }

            QProgressBar::chunk {
                background-color: #7c5cff;
                border-radius: 8px;
            }

            QCheckBox {
                spacing: 8px;
            }
            #PanelTitle {
            color: #ffffff;
            font-weight: 800;
            font-size: 12px;
         }

            #RuntimeStatus {
                color: #55dd88;
                font-weight: 700;
            }
        """)