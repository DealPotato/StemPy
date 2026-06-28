from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class RuntimePanel(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("RUNTIME CHECK")
        self.status = QLabel("● Checking...")
        self.python = QLabel("Python: -")
        self.ffmpeg = QLabel("FFmpeg: -")
        self.backend = QLabel("Backend: -")
        self.cuda = QLabel("Device: -")
        self.vram = QLabel("VRAM: -")
        self.temp = QLabel("Temp Folder: -")
        self.write = QLabel("Write Access: -")
        self.audio_separator = QLabel("Audio Separator: -")
        self.models = QLabel("Models Folder: -")
        self.presets = QLabel("Presets Folder: -")
        self.repair_button = QPushButton("Install / Repair Runtime")
        self.title.setObjectName("PanelTitle")
        self.status.setObjectName("RuntimeStatus")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(7)

        layout.addWidget(self.title)
        layout.addWidget(self.status)
        layout.addWidget(self.python)
        layout.addWidget(self.ffmpeg)
        layout.addWidget(self.backend)
        layout.addWidget(self.cuda)
        layout.addWidget(self.vram)
        layout.addWidget(self.temp)
        layout.addWidget(self.write)
        layout.addWidget(self.audio_separator)
        layout.addWidget(self.models)
        layout.addWidget(self.presets)
        layout.addWidget(self.repair_button)
        layout.addStretch()

    def update_status(self, runtime_status):
        self.status.setText("● Ready" if runtime_status.ready else "● Warning")

        self.python.setText(f"✓ Python {runtime_status.python_version}")
        self.ffmpeg.setText("✓ FFmpeg" if runtime_status.ffmpeg_available else "✕ FFmpeg missing")
        self.backend.setText("✓ Backend" if runtime_status.demucs_available else "✕ Backend missing")
        self.audio_separator.setText("✓ Audio Separator" if runtime_status.audio_separator_available else "✕ Audio Separator missing")
        self.models.setText("✓ Models Folder" if runtime_status.models_folder_ok else "✕ Models Folder missing")
        self.presets.setText("✓ Presets Folder" if runtime_status.presets_folder_ok else "✕ Presets Folder missing")

        if runtime_status.cuda_available:
            self.cuda.setText(f"✓ CUDA {runtime_status.gpu_name}")
            self.vram.setText(f"✓ VRAM {runtime_status.vram_gb} GB")
        else:
            self.cuda.setText("⚠ CPU Mode")
            self.vram.setText("VRAM: -")

        self.temp.setText("✓ Temp Folder" if runtime_status.temp_folder_ok else "✕ Temp Folder")
        self.write.setText("✓ Write Access" if runtime_status.write_access_ok else "✕ Write Access")
        self.repair_button.setVisible(not runtime_status.ready)
