import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.separator import SeparationPreset, Separator
from core.scanner import SongItem, scan_clone_hero_folder
from core.logger import logger


class ProcessingWorker(QThread):
    finished_processing = Signal(list)
    failed_processing = Signal(str)
    progress_changed = Signal(int, int, object)

    def __init__(self, songs: list[SongItem], preset: SeparationPreset):
        super().__init__()
        self.songs = songs
        self.preset = preset
        self.separator = Separator()

    def run(self):
        try:
            results = self.separator.process_batch(
                self.songs,
                self.preset,
                progress_callback=lambda current, total, song: self.progress_changed.emit(
                    current, total, song
                ),
            )
            self.finished_processing.emit(results)
        except Exception as ex:
            self.failed_processing.emit(str(ex))

    def cancel(self):
        self.separator.cancel()


class ScanWorker(QThread):
    finished_scan = Signal(object)
    failed_scan = Signal(str)

    def __init__(self, folder: str, skip_already_processed: bool):
        super().__init__()
        self.folder = folder
        self.skip_already_processed = skip_already_processed

    def run(self):
        try:
            report = scan_clone_hero_folder(
                self.folder,
                skip_already_processed=self.skip_already_processed,
            )
            self.finished_scan.emit(report)
        except Exception as ex:
            self.failed_scan.emit(str(ex))


class RuntimeSetupWorker(QThread):
    setup_finished = Signal(bool, str)

    def run(self):
        script = Path(__file__).resolve().parents[2] / "setup_runtime.py"
        command = [sys.executable, str(script), "--repair-current"]
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if process.stdout is not None:
                for raw_line in process.stdout:
                    line = raw_line.strip()
                    if line:
                        logger.info(f"Runtime setup: {line}")
            return_code = process.wait()
            if return_code != 0:
                self.setup_finished.emit(False, f"Setup exited with code {return_code}")
                return
            self.setup_finished.emit(True, "Runtime setup completed")
        except Exception as ex:
            self.setup_finished.emit(False, str(ex))
