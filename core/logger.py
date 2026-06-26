from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


@dataclass
class LogEntry:
    time: str
    level: str
    message: str

    def format(self) -> str:
        return f"[{self.time}] {self.level:<7} {self.message}"


class AppLogger:
    def __init__(self, log_dir: str | Path = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = self.log_dir / f"stempy_{timestamp}.log"

        self.listeners: list[Callable[[LogEntry], None]] = []

    def add_listener(self, listener: Callable[[LogEntry], None]) -> None:
        self.listeners.append(listener)

    def _write(self, level: str, message: str) -> None:
        entry = LogEntry(
            time=datetime.now().strftime("%H:%M:%S"),
            level=level.upper(),
            message=message,
        )

        line = entry.format()
        print(line)

        try:
            with self.log_file.open("a", encoding="utf-8") as file:
                file.write(line + "\n")
        except Exception:
            pass

        for listener in self.listeners:
            try:
                listener(entry)
            except Exception:
                pass

    def info(self, message: str) -> None:
        self._write("INFO", message)

    def success(self, message: str) -> None:
        self._write("OK", message)

    def warning(self, message: str) -> None:
        self._write("WARN", message)

    def error(self, message: str) -> None:
        self._write("ERROR", message)

    def debug(self, message: str) -> None:
        self._write("DEBUG", message)


logger = AppLogger()