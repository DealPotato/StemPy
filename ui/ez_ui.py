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
from PySide6.QtCore import Signal
from ui.widgets.song_table import SongTable


class EZPage(QWidget):
    scan_requested = Signal(str)
    def __init__(self):
        super().__init__()

        self.folder_input = QLineEdit()
        self.browse_button = QPushButton("Browse")
        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.request_scan)

        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_input)
        folder_row.addWidget(self.browse_button)
        folder_row.addWidget(self.scan_button)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by artist or song name...")

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
        layout.addWidget(self.song_table)
        layout.addWidget(QLabel("4. Preset"))
        layout.addWidget(self.preset_combo)
        layout.addWidget(self.same_format)
        layout.addWidget(self.skip_processed)
        layout.addWidget(self.create_backup)
        layout.addWidget(self.continue_on_error)
        layout.addWidget(self.start_button)
        layout.addWidget(self.delete_backups_button)

        self.browse_button.clicked.connect(self.browse_folder)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Clone Hero Songs Folder")
        if folder:
            self.folder_input.setText(folder)
    
    def request_scan(self):
        folder = self.folder_input.text().strip()

        if not folder:
            return

        self.scan_requested.emit(folder)