import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.config import MODEL_CATALOG_CACHE, MODELS_DIR
from core.logger import logger


@dataclass
class CatalogModel:
    filename: str
    architecture: str
    stems: list[str]
    friendly_name: str

    @property
    def family(self) -> str:
        arch = self.architecture.casefold()
        suffix = Path(self.filename).suffix.casefold()
        if "demucs" in arch or suffix in {".yaml", ".yml"}:
            return "demucs"
        if "vr" in arch or suffix == ".pth":
            return "vr_arch"
        if "mdxc" in arch or "roformer" in self.friendly_name.casefold() or suffix == ".ckpt":
            return "roformer"
        return "mdx"

    @property
    def download_dir(self) -> Path:
        return MODELS_DIR / self.family / "downloaded"

    @property
    def installed(self) -> bool:
        return any((MODELS_DIR / self.family).rglob(self.filename))


class ModelCatalogService:
    def __init__(self):
        self.audio_separator_exe = Path(sys.executable).parent / "audio-separator.exe"

    def load_cached(self) -> list[CatalogModel]:
        if not MODEL_CATALOG_CACHE.exists():
            return []
        try:
            data = json.loads(MODEL_CATALOG_CACHE.read_text(encoding="utf-8-sig"))
            return [CatalogModel(**item) for item in data]
        except (OSError, ValueError, TypeError):
            return []

    @staticmethod
    def installed_filenames() -> set[str]:
        if not MODELS_DIR.exists():
            return set()
        return {
            path.name
            for path in MODELS_DIR.rglob("*")
            if path.is_file()
        }

    def refresh(self) -> list[CatalogModel]:
        command = [
            str(self.audio_separator_exe),
            "--list_models",
            "--list_format=json",
        ]
        logger.info("Refreshing Audio Separator model catalog")
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip() or f"Model catalog failed with code {result.returncode}"
            )

        models = self.parse_catalog_output(result.stdout)
        MODEL_CATALOG_CACHE.parent.mkdir(parents=True, exist_ok=True)
        MODEL_CATALOG_CACHE.write_text(
            json.dumps([asdict(item) for item in models], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.success(f"Model catalog loaded: {len(models)} models")
        return models

    def download(self, model: CatalogModel, output_callback=None) -> Path:
        model.download_dir.mkdir(parents=True, exist_ok=True)
        command = [
            str(self.audio_separator_exe),
            "--model_filename",
            model.filename,
            "--model_file_dir",
            str(model.download_dir),
            "--download_model_only",
        ]
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
                if not line:
                    continue
                logger.info(line)
                if output_callback is not None:
                    output_callback(line)
        return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(f"Model download failed with code {return_code}")
        logger.success(f"Downloaded model: {model.filename}")
        return model.download_dir / model.filename

    @staticmethod
    def parse_catalog_output(output: str) -> list[CatalogModel]:
        decoder = json.JSONDecoder()
        payload: Any = None
        for index, character in enumerate(output):
            if character not in "[{":
                continue
            try:
                payload, _ = decoder.raw_decode(output[index:])
                break
            except ValueError:
                continue
        if payload is None:
            raise ValueError("Audio Separator returned no JSON model catalog")

        records = ModelCatalogService._flatten_records(payload)
        models: list[CatalogModel] = []
        seen: set[str] = set()
        for record in records:
            filename = str(
                ModelCatalogService._pick(record, "filename", "model_filename", "model filename")
                or ""
            ).strip()
            if not filename or filename in seen:
                continue
            seen.add(filename)
            architecture = str(
                ModelCatalogService._pick(record, "arch", "architecture") or "Unknown"
            ).strip()
            friendly_name = str(
                ModelCatalogService._pick(record, "friendly_name", "friendly name", "name")
                or filename
            ).strip()
            stems_value = (
                ModelCatalogService._pick(
                    record, "stems", "output_stems", "output stems", "output stems (sdr)"
                )
                or []
            )
            if isinstance(stems_value, str):
                stems = [
                    item.strip().split(" (")[0].casefold()
                    for item in stems_value.split(",")
                    if item.strip()
                ]
            elif isinstance(stems_value, dict):
                stems = [str(item).casefold() for item in stems_value]
            else:
                stems = [str(item).casefold() for item in stems_value]
            models.append(CatalogModel(filename, architecture, stems, friendly_name))
        return models

    @staticmethod
    def _pick(record: dict[str, Any], *names: str):
        normalized = {
            str(key).casefold().replace("_", " ").strip(): value
            for key, value in record.items()
        }
        for name in names:
            key = name.casefold().replace("_", " ").strip()
            if key in normalized:
                return normalized[key]
        return None

    @staticmethod
    def _flatten_records(
        value: Any,
        filename_hint: str = "",
        architecture_hint: str = "",
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if isinstance(value, list):
            for item in value:
                records.extend(
                    ModelCatalogService._flatten_records(
                        item, filename_hint, architecture_hint
                    )
                )
        elif isinstance(value, dict):
            normalized_keys = {
                str(key).casefold().replace("_", " ").strip() for key in value
            }
            has_filename = bool(normalized_keys & {"filename", "model filename"})
            looks_like_model = bool(
                normalized_keys
                & {
                    "arch",
                    "architecture",
                    "stems",
                    "output stems",
                    "output stems (sdr)",
                    "friendly name",
                }
            )
            if has_filename or (filename_hint and looks_like_model):
                record = dict(value)
                if not has_filename:
                    record["filename"] = filename_hint
                if not ModelCatalogService._pick(record, "arch", "architecture") and architecture_hint:
                    record["architecture"] = architecture_hint
                records.append(record)
                return records

            architecture_names = {"vr arch", "mdx", "mdxc", "demucs", "roformer"}
            for key, item in value.items():
                key_text = str(key)
                key_folded = key_text.casefold().replace("_", " ")
                next_architecture = (
                    key_text if key_folded in architecture_names else architecture_hint
                )
                is_filename = Path(key_text).suffix.casefold() in {
                    ".ckpt",
                    ".onnx",
                    ".pth",
                    ".th",
                    ".yaml",
                    ".yml",
                }
                records.extend(
                    ModelCatalogService._flatten_records(
                        item,
                        key_text if is_filename else filename_hint,
                        next_architecture,
                    )
                )
        return records
