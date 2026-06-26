import platform
import shutil
import tempfile
import importlib
from pathlib import Path

from models.runtime_status import RuntimeStatus
from core.logger import logger


def check_write_access(folder: Path) -> bool:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        test_file = folder / ".stempy_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def check_demucs_available() -> bool:
    return shutil.which("demucs") is not None


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

def run_runtime_check() -> RuntimeStatus:
    logger.info("Running runtime check...")

    python_version = platform.python_version()
    ffmpeg_available = shutil.which("ffmpeg") is not None
    demucs_available = check_demucs_available()
    cuda_available, gpu_name, vram_gb = check_cuda()

    temp_folder = Path(tempfile.gettempdir()) / "StemPy"
    temp_folder_ok = check_write_access(temp_folder)
    write_access_ok = check_write_access(Path("data"))

    status = RuntimeStatus(
        python_version=python_version,
        ffmpeg_available=ffmpeg_available,
        cuda_available=cuda_available,
        gpu_name=gpu_name,
        vram_gb=vram_gb,
        demucs_available=demucs_available,
        temp_folder_ok=temp_folder_ok,
        write_access_ok=write_access_ok,
    )

    if status.ready:
        logger.success(f"Runtime ready - Device: {status.device_label}")
    else:
        logger.warning("Runtime check completed with warnings")

    return status