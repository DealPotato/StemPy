from dataclasses import dataclass


@dataclass
class RuntimeStatus:
    python_version: str
    ffmpeg_available: bool
    cuda_available: bool
    gpu_name: str
    vram_gb: float | None
    demucs_available: bool
    temp_folder_ok: bool
    write_access_ok: bool

    @property
    def ready(self) -> bool:
        return (
            self.ffmpeg_available
            and self.demucs_available
            and self.temp_folder_ok
            and self.write_access_ok
        )

    @property
    def device_label(self) -> str:
        if self.cuda_available:
            return f"CUDA ({self.gpu_name})"
        return "CPU"