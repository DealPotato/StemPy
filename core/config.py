import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = APP_ROOT / "data"
MODELS_DIR = APP_ROOT / "models"
PRESETS_DIR = DATA_DIR / "presets"
SETTINGS_PATH = DATA_DIR / "settings.json"
MODEL_CATALOG_CACHE = DATA_DIR / "model_catalog.json"


@dataclass
class AppSettings:
    theme: str = "dark"
    ui_mode: str = "ez"
    songs_folder: str = ""

    ez_preset: str = "Balanced"
    advanced_preset: str = "Custom"
    output_format: str = "same_as_input"
    device: str = "auto"

    create_backup: bool = True
    skip_already_processed: bool = True
    continue_on_error: bool = True
    delete_backup_after_success: bool = False
    use_autocast: bool = True
    advanced_models: dict[str, dict] = field(default_factory=dict)

    window_width: int = 1280
    window_height: int = 820
    window_maximized: bool = False


def load_settings() -> AppSettings:
    if not SETTINGS_PATH.exists() or SETTINGS_PATH.stat().st_size == 0:
        settings = AppSettings()
        save_settings(settings)
        return settings

    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8-sig"))
        known_fields = {item.name for item in fields(AppSettings)}
        filtered = {key: value for key, value in data.items() if key in known_fields}
        return AppSettings(**filtered)
    except (OSError, ValueError, TypeError):
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = SETTINGS_PATH.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(asdict(settings), indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    temp_path.replace(SETTINGS_PATH)
