from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AdvancedPage(QWidget):
    def __init__(self):
        super().__init__()

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Built-in Fast", "Built-in Balanced", "Built-in Quality"])

        self.save_button = QPushButton("Save")
        self.save_as_button = QPushButton("Save As...")
        self.delete_button = QPushButton("Delete")
        self.import_button = QPushButton("Import...")
        self.export_button = QPushButton("Export...")

        self.vocals = QCheckBox("Vocals")
        self.drums = QCheckBox("Drums")
        self.guitar = QCheckBox("Guitar")
        self.rhythm = QCheckBox("Rhythm")
        self.keys = QCheckBox("Keys")
        self.other = QCheckBox("Other")

        for checkbox in [self.vocals, self.drums, self.guitar, self.rhythm, self.other]:
            checkbox.setChecked(True)

        self.device_combo = QComboBox()
        self.device_combo.addItems(["Auto", "CUDA", "CPU"])

        self.output_format = QComboBox()
        self.output_format.addItems(["Same as input", "OPUS", "OGG", "WAV", "MP3"])

        self.create_backup = QCheckBox("Create backup before processing")
        self.skip_processed = QCheckBox("Skip already processed songs")
        self.continue_on_error = QCheckBox("Continue on error")
        self.delete_backup_after_success = QCheckBox("Delete backup after successful processing")
        self.delete_backups_button = QPushButton("Delete Backups...")

        layout = QVBoxLayout(self)

        preset_grid = QGridLayout()
        preset_grid.addWidget(QLabel("Preset"), 0, 0)
        preset_grid.addWidget(self.preset_combo, 0, 1)
        preset_grid.addWidget(self.save_button, 0, 2)
        preset_grid.addWidget(self.save_as_button, 0, 3)
        preset_grid.addWidget(self.delete_button, 0, 4)
        preset_grid.addWidget(self.import_button, 0, 5)
        preset_grid.addWidget(self.export_button, 0, 6)

        layout.addLayout(preset_grid)

        layout.addWidget(QLabel("Stem Selection"))
        layout.addWidget(self.vocals)
        layout.addWidget(self.drums)
        layout.addWidget(self.guitar)
        layout.addWidget(self.rhythm)
        layout.addWidget(self.keys)
        layout.addWidget(self.other)

        layout.addWidget(QLabel("Device"))
        layout.addWidget(self.device_combo)

        layout.addWidget(QLabel("Output Format"))
        layout.addWidget(self.output_format)

        layout.addWidget(self.create_backup)
        layout.addWidget(self.skip_processed)
        layout.addWidget(self.continue_on_error)
        layout.addWidget(self.delete_backup_after_success)
        layout.addWidget(self.delete_backups_button)

        layout.addStretch()