from dataclasses import dataclass, field

from models.song_item import SongItem


@dataclass
class ScanReport:
    ready_songs: list[SongItem] = field(default_factory=list)
    already_processed: int = 0
    missing_audio: int = 0
    failed: list[str] = field(default_factory=list)
    total_folders_scanned: int = 0

    @property
    def ready_count(self) -> int:
        return len(self.ready_songs)

    @property
    def failed_count(self) -> int:
        return len(self.failed)