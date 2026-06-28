import importlib
import platform
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from core.logger import logger


@dataclass
class RuntimeStatus:
    python_version: str
    ffmpeg_available: bool
    demucs_available: bool
    audio_separator_available: bool
    cuda_available: bool
    gpu_name: str
    vram_gb: float | None
    temp_folder_ok: bool
    write_access_ok: bool
    models_folder_ok: bool
    presets_folder_ok: bool

    @property
    def ready(self) -> bool:
        return (
            self.ffmpeg_available
            and self.demucs_available
            and self.audio_separator_available
            and self.temp_folder_ok
            and self.write_access_ok
            and self.models_folder_ok
            and self.presets_folder_ok
        )

    @property
    def device_label(self) -> str:
        if self.cuda_available:
            return f"CUDA ({self.gpu_name})"
        return "CPU"


def check_write_access(folder: Path) -> bool:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        test_file = folder / ".stempy_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def check_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def check_cuda() -> tuple[bool, str, float | None]:
    try:
        torch = importlib.import_module("torch")

        if not torch.cuda.is_available():
            return False, "", None

        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)

        return True, gpu_name, round(vram_gb, 1)

    except Exception:
        return False, "", None


def check_required_folder(folder: Path) -> bool:
    return folder.exists() and folder.is_dir()


def run_runtime_check() -> RuntimeStatus:
    logger.info("Running runtime check...")

    cuda_available, gpu_name, vram_gb = check_cuda()

    status = RuntimeStatus(
        python_version=platform.python_version(),
        ffmpeg_available=shutil.which("ffmpeg") is not None,
        demucs_available=check_import("demucs"),
        audio_separator_available=check_import("audio_separator"),
        cuda_available=cuda_available,
        gpu_name=gpu_name,
        vram_gb=vram_gb,
        temp_folder_ok=check_write_access(Path(tempfile.gettempdir()) / "StemPy"),
        write_access_ok=check_write_access(Path("data")),
        models_folder_ok=check_required_folder(Path("models")),
        presets_folder_ok=check_required_folder(Path("data/presets")),
    )

    if status.ffmpeg_available:
        logger.success("FFmpeg found")
    else:
        logger.error("FFmpeg missing")

    if status.demucs_available:
        logger.success("Demucs found")
    else:
        logger.error("Demucs missing")

    if status.audio_separator_available:
        logger.success("Audio Separator found")
    else:
        logger.error("Audio Separator missing")

    if status.cuda_available:
        logger.success(f"CUDA available: {status.gpu_name} ({status.vram_gb} GB)")
    else:
        logger.warning("CUDA not available, CPU mode will be used")

    if status.ready:
        logger.success(f"Runtime ready - Device: {status.device_label}")
    else:
        logger.warning("Runtime check completed with warnings")

    return status