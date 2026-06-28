from dataclasses import dataclass
from pathlib import Path

from core.config import MODELS_DIR
from core.logger import logger


MODEL_ROOT = MODELS_DIR

MODEL_FAMILIES = {
    "demucs": "Demucs",
    "mdx": "MDX",
    "roformer": "RoFormer",
    "vr_arch": "VR Arch",
}

MODEL_EXTENSIONS = {
    ".th",
    ".pth",
    ".ckpt",
    ".onnx",
    ".safetensors",
    ".yaml",
    ".yml",
}


@dataclass
class AIModel:
    family: str
    family_label: str
    name: str
    path: Path
    builtin: bool

    @property
    def display_name(self) -> str:
        prefix = "Built-in" if self.builtin else "Custom"
        return f"{prefix}: {self.name}"


class ModelRegistry:
    def __init__(self, root: str | Path = MODEL_ROOT):
        self.root = Path(root)
        self.models: list[AIModel] = []

    def scan(self) -> list[AIModel]:
        logger.info("Scanning AI models...")
        self.models.clear()

        for family, family_label in MODEL_FAMILIES.items():
            family_folder = self.root / family

            if not family_folder.exists():
                logger.warning(f"Model folder missing: {family_folder}")
                continue

            self._scan_family(family, family_label, family_folder)

        logger.success(f"Model scan complete: {len(self.models)} models found")

        for family, label in MODEL_FAMILIES.items():
            logger.info(f"{label}: {len(self.get_models(family))}")

        return self.models

    def _scan_family(self, family: str, family_label: str, family_folder: Path) -> None:
        for path in family_folder.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() not in MODEL_EXTENSIONS:
                continue
            if family == "demucs" and path.suffix.casefold() not in {".yaml", ".yml"}:
                continue
            if family != "demucs" and path.suffix.casefold() in {".yaml", ".yml", ".th"}:
                continue

            builtin = "builtin" in [part.lower() for part in path.parts]

            self.models.append(
                AIModel(
                    family=family,
                    family_label=family_label,
                    name=path.name,
                    path=path,
                    builtin=builtin,
                )
            )

    def get_all_models(self) -> list[AIModel]:
        return self.models

    def get_models(self, family: str) -> list[AIModel]:
        return [model for model in self.models if model.family == family]

    def get_model(self, family: str, name: str) -> AIModel | None:
        for model in self.models:
            if model.family == family and model.name == name:
                return model
        return None
