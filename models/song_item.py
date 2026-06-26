from dataclasses import dataclass
from pathlib import Path


@dataclass
class SongItem:
    folder: Path
    title: str
    artist: str
    source_audio: Path
    source_type: str
    status: str = "Ready"
    reason: str = ""
    selected: bool = False