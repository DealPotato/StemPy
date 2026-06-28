import faulthandler
import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
os.chdir(APP_DIR)

from PySide6.QtWidgets import QApplication

from core.logger import logger
from core.scanner import scan_clone_hero_folder
from core.scanner import SongItem, ScanReport
from ui.main_window import MainWindow

from core.model_registry import ModelRegistry
from core.separator import Separator


def install_crash_logging():
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    crash_file = (log_dir / f"crash_{timestamp}.log").open(
        "a", encoding="utf-8", buffering=1
    )

    faulthandler.enable(crash_file, all_threads=True)

    def log_exception(exc_type, exc_value, exc_traceback):
        traceback.print_exception(
            exc_type,
            exc_value,
            exc_traceback,
            file=crash_file,
        )
        crash_file.flush()

    sys.excepthook = log_exception

    def log_thread_exception(args):
        log_exception(args.exc_type, args.exc_value, args.exc_traceback)

    threading.excepthook = log_thread_exception
    return crash_file

class StemPyApp:
    def __init__(self):
        self.last_scan_folder: Path | None = None
        self.last_scan_report: ScanReport | None = None
        self.model_registry = ModelRegistry()
        self.models = self.model_registry.scan()
        self.separator = Separator()

    def scan_folder(self, folder: str | Path) -> ScanReport:
        folder_path = Path(folder)

        logger.info(f"Scan requested: {folder_path}")

        report = scan_clone_hero_folder(folder_path)

        self.last_scan_folder = folder_path
        self.last_scan_report = report

        return report


def main():
    crash_file = install_crash_logging()

    try:
        qt_app = QApplication(sys.argv)

        stempy_app = StemPyApp()
        window = MainWindow(app_controller=stempy_app)

        window.show()

        return qt_app.exec()
    finally:
        faulthandler.disable()
        crash_file.close()


if __name__ == "__main__":
    sys.exit(main())
