from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class ModeSwitch(QWidget):
    mode_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.ez_button = QPushButton("EZ UI")
        self.advanced_button = QPushButton("Advanced UI")

        self.ez_button.setCheckable(True)
        self.advanced_button.setCheckable(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.ez_button)
        layout.addWidget(self.advanced_button)

        self.ez_button.clicked.connect(lambda: self.set_mode("ez"))
        self.advanced_button.clicked.connect(lambda: self.set_mode("advanced"))

        self.set_mode("ez")

    def set_mode(self, mode: str):
        is_ez = mode == "ez"

        self.ez_button.setChecked(is_ez)
        self.advanced_button.setChecked(not is_ez)

        self.mode_changed.emit(mode)