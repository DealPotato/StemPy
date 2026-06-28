import configparser
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from core.logger import logger


AUDIO_EXTENSIONS = {".ogg", ".opus", ".mp3", ".wav", ".flac", ".m4a"}
SOURCE_NAMES = {"song", "guitar"}
STEM_NAMES = {"drums", "bass", "vocals", "keys", "rhythm", "other"}
IGNORED_DIRECTORIES = {"StemPy Backup", "_stem_batcher_backup"}


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


def read_song_metadata(ini_path: Path) -> dict[str, str]:
    if not ini_path.exists():
        return {}

    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser.optionxform = str.lower

    try:
        with ini_path.open("r", encoding="utf-8-sig", errors="replace") as file:
            parser.read_file(file)
    except (OSError, configparser.Error) as ex:
        logger.warning(f"Could not read song.ini: {ini_path} ({ex})")
        return {}

    section = next(
        (name for name in parser.sections() if name.casefold() == "song"),
        None,
    )
    values: dict[str, str] = dict(parser.defaults())
    if section is not None:
        values.update(dict(parser.items(section)))
    return {str(key).casefold(): str(value).strip() for key, value in values.items()}


def guess_artist_title_from_folder(folder_name: str) -> tuple[str, str]:
    cleaned = folder_name.strip()
    cleaned = re.sub(r"^\s*\d+\s*[-._]?\s*", "", cleaned).strip()

    for separator in [" - ", " – ", " — "]:
        if separator in cleaned:
            artist, title = cleaned.split(separator, 1)
            return artist.strip(), title.strip()

    return "", cleaned


def _select_source(folder: Path, filenames: list[str]) -> tuple[Path | None, bool]:
    sources: list[Path] = []
    has_stems = False

    for filename in filenames:
        path = Path(filename)
        if path.suffix.casefold() not in AUDIO_EXTENSIONS:
            continue

        stem = path.stem.casefold()
        if stem in SOURCE_NAMES:
            sources.append(folder / filename)
        elif stem in STEM_NAMES:
            has_stems = True

    for preferred in ("guitar", "song"):
        for source in sources:
            if source.stem.casefold() == preferred:
                return source, has_stems

    return (sources[0] if sources else None), has_stems


def scan_clone_hero_folder(
    root_folder: str | Path,
    skip_already_processed: bool = True,
) -> ScanReport:
    root = Path(root_folder).expanduser().resolve()
    report = ScanReport()

    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {root}")

    logger.info(f"Scanning folder: {root}")

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in IGNORED_DIRECTORIES and not name.startswith(".stempy-staging-")
        ]
        folder = Path(dirpath)
        report.total_folders_scanned += 1

        if not any(name.casefold() == "song.ini" for name in filenames):
            continue

        try:
            source_audio, has_stems = _select_source(folder, filenames)
            if source_audio is None:
                report.missing_audio += 1
                continue

            if has_stems:
                report.already_processed += 1
                if skip_already_processed:
                    continue

            metadata = read_song_metadata(folder / "song.ini")
            guessed_artist, guessed_title = guess_artist_title_from_folder(folder.name)
            title = (
                metadata.get("name")
                or metadata.get("song")
                or metadata.get("title")
                or guessed_title
                or folder.name
            )
            artist = (
                metadata.get("artist")
                or metadata.get("artist_name")
                or metadata.get("band")
                or guessed_artist
                or "Unknown Artist"
            )

            report.ready_songs.append(
                SongItem(
                    folder=folder,
                    title=title.strip(),
                    artist=artist.strip(),
                    source_audio=source_audio,
                    source_type=source_audio.stem.casefold(),
                    status="Ready" if not has_stems else "Reprocess",
                )
            )
        except Exception as ex:
            report.failed.append(f"{folder} | {ex}")
            logger.error(f"Failed while scanning {folder}: {ex}")

    logger.success(f"Scan complete: {report.ready_count} songs ready")
    logger.info(f"Folders scanned: {report.total_folders_scanned}")
    logger.info(f"Already processed: {report.already_processed}")
    logger.info(f"Missing source audio: {report.missing_audio}")
    logger.info(f"Failed: {report.failed_count}")
    return report
