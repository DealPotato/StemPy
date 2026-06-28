"""Create or repair StemPy's private Python runtime using only the standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent
VENV_DIR = APP_ROOT / ".venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
MARKER_PATH = VENV_DIR / ".stempy-runtime.json"
RUNTIME_VERSION = "2026.06.28.1"

BASE_PACKAGES = [
    "setuptools<82",
    "wheel",
    "packaging",
    "PySide6>=6.8,<7",
    "demucs==4.0.1",
]


def run(command: list[str], check: bool = True) -> int:
    print("\n>", subprocess.list2cmdline(command), flush=True)
    result = subprocess.run(command, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {command[0]}"
        )
    return result.returncode


def has_nvidia_gpu() -> bool:
    command = shutil.which("nvidia-smi")
    if command is None:
        return False
    return subprocess.run(
        [command, "-L"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def package_plan(gpu: bool) -> list[str]:
    separator_extra = "gpu" if gpu else "cpu"
    return [*BASE_PACKAGES, f"audio-separator[{separator_extra}]==0.44.2"]


def fingerprint(gpu: bool) -> str:
    payload = "\n".join([RUNTIME_VERSION, sys.platform, str(gpu), *package_plan(gpu)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def marker_matches(gpu: bool) -> bool:
    if not VENV_PYTHON.exists() or not MARKER_PATH.exists():
        return False
    try:
        data = json.loads(MARKER_PATH.read_text(encoding="utf-8"))
        return data.get("fingerprint") == fingerprint(gpu)
    except (OSError, ValueError, TypeError):
        return False


def create_venv() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            f"Python 3.12 is required to create the StemPy runtime; found "
            f"{sys.version_info.major}.{sys.version_info.minor}."
        )
    print(f"Creating private runtime: {VENV_DIR}", flush=True)
    run([sys.executable, "-m", "venv", str(VENV_DIR)])


def verify_python_runtime(python: Path) -> None:
    imports = "import PySide6, torch, torchaudio, demucs, audio_separator, onnxruntime"
    run([str(python), "-c", imports])


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg") is not None:
        print("FFmpeg found.", flush=True)
        return

    winget = shutil.which("winget")
    if os.name != "nt" or winget is None:
        raise RuntimeError(
            "FFmpeg is missing and winget is unavailable. Install FFmpeg, then run this setup again."
        )

    print("FFmpeg is missing. Installing Gyan.FFmpeg with winget...", flush=True)
    run(
        [
            winget,
            "install",
            "-e",
            "--id",
            "Gyan.FFmpeg",
            "--accept-source-agreements",
            "--accept-package-agreements",
            "--silent",
        ]
    )


def install_runtime(target_python: Path, gpu: bool) -> None:
    profile = "NVIDIA GPU" if gpu else "CPU"
    print(f"Installing StemPy dependencies for: {profile}", flush=True)
    run([str(target_python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(target_python), "-m", "pip", "install", *package_plan(gpu)])
    verify_python_runtime(target_python)
    ensure_ffmpeg()


def write_marker(gpu: bool) -> None:
    MARKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKER_PATH.write_text(
        json.dumps(
            {
                "runtime_version": RUNTIME_VERSION,
                "fingerprint": fingerprint(gpu),
                "gpu_profile": "nvidia" if gpu else "cpu",
                "installed_at": datetime.now().isoformat(timespec="seconds"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or repair StemPy runtime")
    parser.add_argument(
        "--repair-current",
        action="store_true",
        help="Repair the Python environment currently running this script.",
    )
    parser.add_argument("--force", action="store_true", help="Reinstall dependencies.")
    parser.add_argument("--plan", action="store_true", help="Print the install plan only.")
    args = parser.parse_args()

    os.chdir(APP_ROOT)
    gpu = has_nvidia_gpu()
    print(f"StemPy runtime profile: {'NVIDIA GPU' if gpu else 'CPU'}", flush=True)

    if args.plan:
        print("\n".join(package_plan(gpu)))
        return 0

    target_python = Path(sys.executable) if args.repair_current else VENV_PYTHON
    if not args.repair_current and not VENV_PYTHON.exists():
        create_venv()
        target_python = VENV_PYTHON

    if not args.force and not args.repair_current and marker_matches(gpu):
        print("StemPy runtime is already installed.", flush=True)
        return 0

    install_runtime(target_python, gpu)
    if target_python.resolve() == VENV_PYTHON.resolve():
        write_marker(gpu)

    for folder in (APP_ROOT / "data/logs", APP_ROOT / "data/temp", APP_ROOT / "data/presets", APP_ROOT / "models"):
        folder.mkdir(parents=True, exist_ok=True)

    print("\nStemPy runtime is ready.", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as ex:
        print(f"\nSETUP ERROR: {ex}", file=sys.stderr, flush=True)
        raise SystemExit(1)
