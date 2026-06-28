from PySide6.QtCore import QElapsedTimer, QTimer
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class ProgressPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("PROGRESS")
        self.song_count = QLabel("0 / 0 songs")
        self.progress = QProgressBar()
        self.current_song = QLabel("Current Song: -")
        self.time = QLabel("Elapsed: 00:00:00")
        self.elapsed_timer = QElapsedTimer()
        self.display_timer = QTimer(self)
        self.display_timer.setInterval(1000)
        self.display_timer.timeout.connect(self.update_elapsed)
        self.total_songs = 0

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.song_count)
        layout.addWidget(self.progress)
        layout.addWidget(self.current_song)
        layout.addWidget(self.time)
        layout.addStretch()

    def set_progress(self, current: int, total: int):
        self.total_songs = total
        self.song_count.setText(f"{current} / {total} songs")
        completed = max(0, current - 1) if self.display_timer.isActive() else current
        percent = int((completed / total) * 100) if total else 0
        self.progress.setValue(percent)

    def set_current_song(self, artist: str, title: str):
        self.current_song.setText(f"Current Song: {artist} - {title}")

    def start(self, total: int):
        self.total_songs = total
        self.song_count.setText(f"0 / {total} songs")
        self.progress.setValue(0)
        self.current_song.setText("Current Song: -")
        self.time.setText("Elapsed: 00:00:00")
        self.elapsed_timer.start()
        self.display_timer.start()

    def finish(self, completed: bool = True):
        self.update_elapsed()
        self.display_timer.stop()
        if completed and self.total_songs:
            self.song_count.setText(f"{self.total_songs} / {self.total_songs} songs")
            self.progress.setValue(100)

    def update_elapsed(self):
        if not self.elapsed_timer.isValid():
            return
        total_seconds = self.elapsed_timer.elapsed() // 1000
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time.setText(f"Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}")
