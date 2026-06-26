import configparser
import re
from pathlib import Path

from core.logger import logger
from models.scan_report import ScanReport
from models.song_item import SongItem


AUDIO_EXTENSIONS = {".ogg", ".opus", ".mp3", ".wav", ".flac", ".m4a"}
SOURCE_NAMES = {"song", "guitar"}
STEM_NAMES = {"drums", "bass", "vocals", "keys", "rhythm", "other"}


def read_ini_value(ini_path: Path, key: str) -> str:
    if not ini_path.exists():
        return ""

    parser = configparser.ConfigParser()
    parser.optionxform = str.lower

    try:
        parser.read(ini_path, encoding="utf-8")

        if parser.has_section("song") and parser.has_option("song", key.lower()):
            return parser.get("song", key.lower()).strip()

        if parser.has_option("DEFAULT", key.lower()):
            return parser.get("DEFAULT", key.lower()).strip()

    except Exception as ex:
        logger.warning(f"Could not read song.ini: {ini_path} ({ex})")

    return ""


def find_audio_by_names(folder: Path, names: set[str]) -> list[Path]:
    found: list[Path] = []

    try:
        for file in folder.iterdir():
            if not file.is_file():
                continue

            if file.suffix.lower() not in AUDIO_EXTENSIONS:
                continue

            if file.stem.lower() in names:
                found.append(file)
    except Exception as ex:
        logger.warning(f"Could not scan folder: {folder} ({ex})")

    return found


def has_existing_stems(folder: Path) -> bool:
    return len(find_audio_by_names(folder, STEM_NAMES)) > 0


def find_source_audio(folder: Path) -> Path | None:
    sources = find_audio_by_names(folder, SOURCE_NAMES)

    if not sources:
        return None

    for preferred_name in ["guitar", "song"]:
        for source in sources:
            if source.stem.lower() == preferred_name:
                return source

    return sources[0]


def guess_artist_title_from_folder(folder_name: str) -> tuple[str, str]:
    cleaned = folder_name.strip()
    cleaned = re.sub(r"^\s*\d+\s*[-._]?\s*", "", cleaned).strip()

    for separator in [" - ", " – ", " — "]:
        if separator in cleaned:
            artist, title = cleaned.split(separator, 1)
            return artist.strip(), title.strip()

    return "", cleaned


def scan_clone_hero_folder(root_folder: str | Path) -> ScanReport:
    root = Path(root_folder)
    report = ScanReport()

    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {root}")

    logger.info(f"Scanning folder: {root}")

    for folder in root.rglob("*"):
        if not folder.is_dir():
            continue

        report.total_folders_scanned += 1

        try:
            source_audio = find_source_audio(folder)

            if source_audio is None:
                report.missing_audio += 1
                continue

            if has_existing_stems(folder):
                report.already_processed += 1
                continue

            ini_path = folder / "song.ini"

            raw_title = (
                read_ini_value(ini_path, "name")
                or read_ini_value(ini_path, "song")
                or read_ini_value(ini_path, "title")
                or ""
            ).strip()

            raw_artist = (
                read_ini_value(ini_path, "artist")
                or read_ini_value(ini_path, "artist_name")
                or read_ini_value(ini_path, "band")
                or ""
            ).strip()

            guessed_artist, guessed_title = guess_artist_title_from_folder(folder.name)

            artist = raw_artist or guessed_artist or "Unknown Artist"
            title = raw_title or guessed_title or folder.name

            report.ready_songs.append(
                SongItem(
                    folder=folder,
                    title=title,
                    artist=artist,
                    source_audio=source_audio,
                    source_type=source_audio.stem.lower(),
                    status="Ready",
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