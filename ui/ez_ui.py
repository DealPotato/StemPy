from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.song_table import SongTable


class EZPage(QWidget):
    scan_requested = Signal(str)

    def __init__(self):
        super().__init__()

        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select Clone Hero songs folder...")

        self.browse_button = QPushButton("Browse")
        self.scan_button = QPushButton("Scan")
        self.selected_count_label = QLabel("0 selected")
        self.invert_selection_button = QPushButton("Invert")

        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_input)
        folder_row.addWidget(self.browse_button)
        folder_row.addWidget(self.scan_button)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by artist or song name...")

        self.refresh_button = QPushButton("Refresh List")
        self.select_all_button = QPushButton("Select All")
        self.clear_selection_button = QPushButton("Clear")

        selection_row = QHBoxLayout()
        selection_row.addWidget(self.selected_count_label)
        selection_row.addStretch()
        selection_row.addWidget(self.refresh_button)
        selection_row.addWidget(self.select_all_button)
        selection_row.addWidget(self.clear_selection_button)
        selection_row.addWidget(self.invert_selection_button)
        self.song_table = SongTable()

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Fast", "Balanced", "Quality"])

        self.same_format = QCheckBox("Same format as input")
        self.same_format.setChecked(True)

        self.skip_processed = QCheckBox("Skip already processed songs")
        self.skip_processed.setChecked(True)

        self.create_backup = QCheckBox("Create backup before processing")
        self.create_backup.setChecked(True)

        self.continue_on_error = QCheckBox("Continue on error")
        self.continue_on_error.setChecked(True)

        self.start_button = QPushButton("Start Processing")
        self.delete_backups_button = QPushButton("Delete Backups...")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("1. Select Clone Hero Songs Folder"))
        layout.addLayout(folder_row)

        layout.addWidget(QLabel("2. Search Songs"))
        layout.addWidget(self.search_input)

        layout.addWidget(QLabel("3. Select Songs"))
        layout.addLayout(selection_row)
        layout.addWidget(self.song_table, stretch=1)

        layout.addWidget(QLabel("4. Preset"))
        layout.addWidget(self.preset_combo)

        layout.addWidget(self.same_format)
        layout.addWidget(self.skip_processed)
        layout.addWidget(self.create_backup)
        layout.addWidget(self.continue_on_error)

        layout.addWidget(self.start_button)
        layout.addWidget(self.delete_backups_button)

        self.connect_signals()

    def connect_signals(self):
        self.browse_button.clicked.connect(self.browse_folder)
        self.scan_button.clicked.connect(self.request_scan)
        self.refresh_button.clicked.connect(self.request_scan)
        self.invert_selection_button.clicked.connect(self.song_table.invert_selection_visible)
        self.song_table.selection_count_changed.connect(self.update_selected_count)

        self.search_input.textChanged.connect(self.song_table.apply_filter)
        self.select_all_button.clicked.connect(self.song_table.select_all_visible)
        self.clear_selection_button.clicked.connect(self.song_table.clear_all_visible)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Clone Hero Songs Folder")

        if folder:
            self.folder_input.setText(folder)

    def request_scan(self):
        folder = self.folder_input.text().strip()

        if not folder:
            return

        self.scan_requested.emit(folder)
    
    def update_selected_count(self, count: int):
        self.selected_count_label.setText(f"{count} selected")
        self.start_button.setText(f"Start Processing ({count})" if count else "Start Processing")