from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


class SongTable(QTableWidget):
    selection_count_changed = Signal(int)
    def __init__(self):
        super().__init__()

        self.all_songs = []
        self.visible_songs = []

        self.itemChanged.connect(self.on_item_changed)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Select", "Song", "Artist", "Source", "Status"])

        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.verticalHeader().setVisible(False)

    def load_songs(self, songs):
        self.all_songs = list(songs)
        self.apply_filter("")

    def apply_filter(self, text: str):
        query = text.strip().lower()

        if not query:
            self.visible_songs = self.all_songs
        else:
            self.visible_songs = [
                song for song in self.all_songs
                if query in song.title.lower()
                or query in song.artist.lower()
                or query in song.source_audio.name.lower()
            ]

        self.refresh_table()

    def refresh_table(self):
        self.blockSignals(True)
        self.setSortingEnabled(False)

        self.setRowCount(len(self.visible_songs))

        for row, song in enumerate(self.visible_songs):
            select_item = QTableWidgetItem()
            select_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            select_item.setCheckState(Qt.Checked if getattr(song, "selected", False) else Qt.Unchecked)

            self.setItem(row, 0, select_item)
            self.setItem(row, 1, QTableWidgetItem(song.title))
            self.setItem(row, 2, QTableWidgetItem(song.artist))
            self.setItem(row, 3, QTableWidgetItem(song.source_audio.name))
            self.setItem(row, 4, QTableWidgetItem(song.status))

        self.setSortingEnabled(True)
        self.blockSignals(False)

        self.selection_count_changed.emit(self.selected_count())

    def select_all_visible(self):
        for song in self.visible_songs:
            song.selected = True

        self.refresh_table()

    def clear_all_visible(self):
        for song in self.visible_songs:
            song.selected = False

        self.refresh_table()
    
    def get_selected_songs(self):
        self.sync_selection_from_table()
        return [song for song in self.all_songs if getattr(song, "selected", False)]

    def sync_selection_from_table(self):
        for row, song in enumerate(self.visible_songs):
            item = self.item(row, 0)
            song.selected = item.checkState() == Qt.Checked if item else False
    
    def on_item_changed(self, item):
        if item.column() != 0:
            return

        row = item.row()

        if row < 0 or row >= len(self.visible_songs):
            return

        self.visible_songs[row].selected = item.checkState() == Qt.Checked
        self.selection_count_changed.emit(self.selected_count())

    def selected_count(self) -> int:
        return len(self.get_selected_songs())

    def invert_selection_visible(self):
        for song in self.visible_songs:
            song.selected = not getattr(song, "selected", False)

        self.refresh_table()