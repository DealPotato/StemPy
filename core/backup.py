import json
import shutil
from datetime import datetime
from pathlib import Path

from core.logger import logger


BACKUP_FOLDER_NAME = "StemPy Backup"


def get_backup_folder(song_folder: Path) -> Path:
    return song_folder / BACKUP_FOLDER_NAME


def create_backup(source_audio: Path) -> Path:
    song_folder = source_audio.parent
    backup_folder = get_backup_folder(song_folder)
    backup_folder.mkdir(parents=True, exist_ok=True)

    backup_file = backup_folder / source_audio.name

    if backup_file.exists():
        logger.info(f"Backup already exists: {backup_file}")
        return backup_file

    shutil.copy2(source_audio, backup_file)

    info = {
        "source_file": source_audio.name,
        "source_path": str(source_audio),
        "backup_file": str(backup_file),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "app": "StemPy",
    }

    (backup_folder / "backup_info.json").write_text(
        json.dumps(info, indent=4),
        encoding="utf-8",
    )

    logger.success(f"Backup created: {backup_file}")
    return backup_file


def backup_exists(song_folder: Path) -> bool:
    return get_backup_folder(song_folder).exists()


def delete_backup(song_folder: Path) -> bool:
    backup_folder = get_backup_folder(song_folder)

    if not backup_folder.exists():
        return False

    shutil.rmtree(backup_folder)
    logger.success(f"Backup deleted: {backup_folder}")
    return True


def delete_backups_in_root(root_folder: str | Path) -> int:
    root = Path(root_folder)
    deleted = 0

    for backup_folder in root.rglob(BACKUP_FOLDER_NAME):
        if backup_folder.is_dir():
            shutil.rmtree(backup_folder)
            deleted += 1

    logger.success(f"Deleted {deleted} backup folders")
    return deleted