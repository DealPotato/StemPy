from PySide6.QtWidgets import QTableWidget, QTableWidgetItem


class SongTable(QTableWidget):
    def __init__(self):
        super().__init__()

        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Select", "Song", "Artist", "Source", "Status"])

    def load_songs(self, songs):
        self.setRowCount(len(songs))

        for row, song in enumerate(songs):
            self.setItem(row, 0, QTableWidgetItem(""))
            self.setItem(row, 1, QTableWidgetItem(song.title))
            self.setItem(row, 2, QTableWidgetItem(song.artist))
            self.setItem(row, 3, QTableWidgetItem(song.source_audio.name))
            self.setItem(row, 4, QTableWidgetItem(song.status))