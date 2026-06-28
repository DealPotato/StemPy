from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QPushButton, QPlainTextEdit, QVBoxLayout, QHBoxLayout, QWidget


class LogPanel(QWidget):
    log_received = Signal(object)

    def __init__(self):
        super().__init__()

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.document().setMaximumBlockCount(2000)

        self.clear_button = QPushButton("Clear Log")
        self.open_button = QPushButton("Open Log Folder")

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self.clear_button)
        button_row.addWidget(self.open_button)

        layout = QVBoxLayout(self)
        layout.addLayout(button_row)
        layout.addWidget(self.log_box)

        self.clear_button.clicked.connect(self.log_box.clear)
        self.log_received.connect(self._append_log)

    def append_log(self, entry):
        # Logger callbacks can run in a processing thread. Emitting a Qt signal
        # queues the actual widget update on the GUI thread.
        self.log_received.emit(entry)

    @Slot(object)
    def _append_log(self, entry):
        self.log_box.appendPlainText(entry.format())
