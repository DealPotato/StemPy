import json
import re
from dataclasses import asdict
from pathlib import Path

from core.config import PRESETS_DIR
from core.separator import SeparationPreset, StemModelConfig


BUILTIN_PRESET_NAMES = {"Fast", "Balanced", "Quality"}


class PresetStore:
    def __init__(self, root: Path = PRESETS_DIR):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def list_names(self) -> list[str]:
        names: list[str] = []
        for path in self.root.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                name = str(data.get("name", "")).strip()
                if name and name not in BUILTIN_PRESET_NAMES:
                    names.append(name)
            except (OSError, ValueError, TypeError):
                continue
        return sorted(set(names), key=str.casefold)

    def load(self, name: str) -> SeparationPreset:
        path = self._find_path(name)
        if path is None:
            raise FileNotFoundError(f"Preset not found: {name}")
        return self.load_file(path)

    def save(self, preset: SeparationPreset) -> Path:
        name = preset.name.strip()
        if not name:
            raise ValueError("Preset name cannot be empty")
        if name in BUILTIN_PRESET_NAMES:
            raise ValueError("Built-in presets cannot be overwritten")

        path = self.root / f"{self._slug(name)}.json"
        self._write(path, preset)
        return path

    def delete(self, name: str) -> bool:
        path = self._find_path(name)
        if path is None:
            return False
        path.unlink()
        return True

    def export(self, preset: SeparationPreset, path: str | Path) -> Path:
        destination = Path(path)
        self._write(destination, preset)
        return destination

    def import_file(self, path: str | Path) -> SeparationPreset:
        preset = self.load_file(Path(path))
        if preset.name in BUILTIN_PRESET_NAMES:
            preset.name = f"{preset.name} Custom"
        self.save(preset)
        return preset

    @staticmethod
    def load_file(path: Path) -> SeparationPreset:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        stems = [StemModelConfig(**item) for item in data.get("stems", [])]
        if not stems:
            raise ValueError("Preset contains no stem models")
        return SeparationPreset(
            name=str(data["name"]),
            stems=stems,
            device=str(data.get("device", "auto")),
            output_format=str(data.get("output_format", "same_as_input")),
            create_backup=bool(data.get("create_backup", True)),
            continue_on_error=bool(data.get("continue_on_error", True)),
            delete_backup_after_success=bool(
                data.get("delete_backup_after_success", False)
            ),
            use_autocast=bool(data.get("use_autocast", True)),
        )

    def _find_path(self, name: str) -> Path | None:
        for path in self.root.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                if str(data.get("name", "")).casefold() == name.casefold():
                    return path
            except (OSError, ValueError, TypeError):
                continue
        return None

    @staticmethod
    def _slug(name: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-._")
        return slug or "preset"

    @staticmethod
    def _write(path: Path, preset: SeparationPreset) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(preset)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        temp.replace(path)
