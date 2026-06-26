from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class ProgressPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("PROGRESS")
        self.song_count = QLabel("0 / 0 songs")
        self.progress = QProgressBar()
        self.current_song = QLabel("Current Song: -")
        self.time = QLabel("Elapsed: 00:00:00 | Remaining: --:--:--")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.song_count)
        layout.addWidget(self.progress)
        layout.addWidget(self.current_song)
        layout.addWidget(self.time)
        layout.addStretch()

    def set_progress(self, current: int, total: int):
        self.song_count.setText(f"{current} / {total} songs")
        percent = int((current / total) * 100) if total else 0
        self.progress.setValue(percent)

    def set_current_song(self, artist: str, title: str):
        self.current_song.setText(f"Current Song: {artist} - {title}")