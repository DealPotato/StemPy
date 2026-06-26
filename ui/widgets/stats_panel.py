from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StatsPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("STATS")
        self.found = QLabel("Songs Found: 0")
        self.ready = QLabel("Ready to Process: 0")
        self.processed = QLabel("Already Processed: 0")
        self.failed = QLabel("Failed: 0")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.found)
        layout.addWidget(self.ready)
        layout.addWidget(self.processed)
        layout.addWidget(self.failed)
        layout.addStretch()

    def update_from_scan_report(self, report):
        self.found.setText(f"Songs Found: {report.total_folders_scanned}")
        self.ready.setText(f"Ready to Process: {report.ready_count}")
        self.processed.setText(f"Already Processed: {report.already_processed}")
        self.failed.setText(f"Failed: {report.failed_count}")