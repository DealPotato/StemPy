from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class HeaderWidget(QWidget):
    def __init__(self):
        super().__init__()

        title = QLabel("StemPy")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("TitleLabel")

        subtitle = QLabel("AI Stem Separation for Clone Hero")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("SubtitleLabel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(6)

        layout.addWidget(title)
        layout.addWidget(subtitle)