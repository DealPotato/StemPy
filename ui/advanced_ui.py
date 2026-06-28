from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.model_registry import AIModel, ModelRegistry
from core.model_catalog import ModelCatalogService
from core.presets import PresetStore
from core.separator import SeparationPreset, StemModelConfig
from ui.model_browser import ModelBrowserDialog
from ui.widgets.song_table import SongTable


STEM_ROWS = [
    ("guitar", "Guitar"),
    ("rhythm", "Rhythm / Bass"),
    ("drums", "Drums"),
    ("vocals", "Vocals"),
    ("keys", "Keys / Piano"),
    ("song", "Backing / Other"),
]


class AdvancedPage(QWidget):
    scan_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.registry = ModelRegistry()
        self.preset_store = PresetStore()
        self.model_combos: dict[str, QComboBox] = {}
        self.stem_checks: dict[str, QCheckBox] = {}

        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select Clone Hero songs folder...")
        self.browse_button = QPushButton("Browse")
        self.scan_button = QPushButton("Scan")
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_input, stretch=1)
        folder_row.addWidget(self.browse_button)
        folder_row.addWidget(self.scan_button)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs...")
        self.selected_count_label = QLabel("0 selected")
        self.select_all_button = QPushButton("Select All")
        self.clear_selection_button = QPushButton("Clear")
        self.invert_selection_button = QPushButton("Invert")
        selection_row = QHBoxLayout()
        selection_row.addWidget(self.selected_count_label)
        selection_row.addStretch()
        selection_row.addWidget(self.select_all_button)
        selection_row.addWidget(self.clear_selection_button)
        selection_row.addWidget(self.invert_selection_button)
        self.song_table = SongTable()

        self.preset_combo = QComboBox()
        self.save_button = QPushButton("Save")
        self.save_as_button = QPushButton("Save As...")
        self.delete_button = QPushButton("Delete")
        self.import_button = QPushButton("Import...")
        self.export_button = QPushButton("Export...")
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Preset"))
        preset_row.addWidget(self.preset_combo, stretch=1)
        preset_row.addWidget(self.save_button)
        preset_row.addWidget(self.save_as_button)
        preset_row.addWidget(self.delete_button)
        preset_row.addWidget(self.import_button)
        preset_row.addWidget(self.export_button)

        model_group = QGroupBox("Stem Models")
        model_grid = QGridLayout(model_group)
        model_grid.addWidget(QLabel("Enabled"), 0, 0)
        model_grid.addWidget(QLabel("Clone Hero stem"), 0, 1)
        model_grid.addWidget(QLabel("AI model"), 0, 2)
        for row, (stem, label) in enumerate(STEM_ROWS, start=1):
            enabled = QCheckBox()
            enabled.setChecked(True)
            combo = QComboBox()
            combo.setMinimumContentsLength(32)
            self.stem_checks[stem] = enabled
            self.model_combos[stem] = combo
            model_grid.addWidget(enabled, row, 0)
            model_grid.addWidget(QLabel(label), row, 1)
            model_grid.addWidget(combo, row, 2)

        self.model_browser_button = QPushButton("Browse & Download Models...")
        model_grid.addWidget(self.model_browser_button, len(STEM_ROWS) + 1, 2)

        self.device_combo = QComboBox()
        self.device_combo.addItems(["Auto", "CUDA", "CPU"])
        self.output_format = QComboBox()
        self.output_format.addItems(["Same as input", "OGG", "OPUS", "FLAC", "WAV", "MP3"])
        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Device"))
        options_row.addWidget(self.device_combo)
        options_row.addWidget(QLabel("Output format"))
        options_row.addWidget(self.output_format)
        options_row.addStretch()

        self.create_backup = QCheckBox("Create backup before processing")
        self.create_backup.setChecked(True)
        self.skip_processed = QCheckBox("Skip already processed songs")
        self.skip_processed.setChecked(True)
        self.continue_on_error = QCheckBox("Continue on error")
        self.continue_on_error.setChecked(True)
        self.delete_backup_after_success = QCheckBox("Delete backup after success")
        self.use_autocast = QCheckBox("Use CUDA autocast (faster)")
        self.use_autocast.setChecked(True)
        self.delete_backups_button = QPushButton("Delete Backups...")
        flags_row = QHBoxLayout()
        for widget in (
            self.create_backup,
            self.skip_processed,
            self.continue_on_error,
            self.delete_backup_after_success,
            self.use_autocast,
        ):
            flags_row.addWidget(widget)
        flags_row.addStretch()
        flags_row.addWidget(self.delete_backups_button)

        self.start_button = QPushButton("Start Processing")

        layout = QVBoxLayout(self)
        layout.addLayout(folder_row)
        layout.addWidget(self.search_input)
        layout.addLayout(selection_row)
        layout.addWidget(self.song_table, stretch=2)
        layout.addLayout(preset_row)
        layout.addWidget(model_group)
        layout.addLayout(options_row)
        layout.addLayout(flags_row)
        layout.addWidget(self.start_button)

        self.connect_signals()
        self.refresh_presets()
        self.refresh_models()

    def connect_signals(self):
        self.browse_button.clicked.connect(self.browse_folder)
        self.scan_button.clicked.connect(self.request_scan)
        self.search_input.textChanged.connect(self.song_table.apply_filter)
        self.select_all_button.clicked.connect(self.song_table.select_all_visible)
        self.clear_selection_button.clicked.connect(self.song_table.clear_all_visible)
        self.invert_selection_button.clicked.connect(self.song_table.invert_selection_visible)
        self.song_table.selection_count_changed.connect(self.update_selected_count)
        self.model_browser_button.clicked.connect(self.open_model_browser)
        self.preset_combo.currentTextChanged.connect(self.load_selected_preset)
        self.save_button.clicked.connect(self.save_preset)
        self.save_as_button.clicked.connect(self.save_preset_as)
        self.delete_button.clicked.connect(self.delete_preset)
        self.import_button.clicked.connect(self.import_preset)
        self.export_button.clicked.connect(self.export_preset)

    def refresh_models(self):
        models = self.registry.scan()
        catalog = {
            model.filename: model for model in ModelCatalogService().load_cached()
        }
        for stem, combo in self.model_combos.items():
            selected = combo.currentData() or {}
            selected_name = selected.get("model_name", "") if isinstance(selected, dict) else ""
            combo.blockSignals(True)
            combo.clear()
            for model in models:
                catalog_model = catalog.get(model.name)
                if catalog_model is not None and not self._supports_stem(catalog_model.stems, stem):
                    continue
                label = (
                    f"{catalog_model.friendly_name} [{model.name}]"
                    if catalog_model is not None
                    else model.display_name
                )
                combo.addItem(label, self._model_data(model))
            combo.blockSignals(False)
            index = next(
                (
                    index
                    for index in range(combo.count())
                    if combo.itemData(index).get("model_name") == selected_name
                ),
                -1,
            )
            if index >= 0:
                combo.setCurrentIndex(index)
            elif selected_name:
                combo.setCurrentIndex(-1)

    @staticmethod
    def _supports_stem(model_stems: list[str], target: str) -> bool:
        if not model_stems:
            return True
        aliases = {
            "guitar": {"guitar"},
            "rhythm": {"bass", "rhythm"},
            "drums": {"drums"},
            "vocals": {"vocals"},
            "keys": {"piano", "keys"},
            "song": {"other", "instrumental", "song"},
        }[target]
        return any(
            alias in model_stem.casefold()
            for alias in aliases
            for model_stem in model_stems
        )

    @staticmethod
    def _model_data(model: AIModel) -> dict[str, str]:
        return {
            "model_family": model.family,
            "model_name": model.name,
            "model_dir": str(model.path.parent.resolve()),
        }

    def build_preset(self, name: str | None = None) -> SeparationPreset:
        stems: list[StemModelConfig] = []
        for stem, _label in STEM_ROWS:
            if not self.stem_checks[stem].isChecked():
                continue
            data = self.model_combos[stem].currentData()
            if not isinstance(data, dict):
                raise ValueError(f"Select an installed model for {stem}")
            stems.append(StemModelConfig(stem=stem, enabled=True, **data))
        if not stems:
            raise ValueError("Enable at least one stem")

        output = self.output_format.currentText().casefold().replace(" ", "_")
        return SeparationPreset(
            name=name or self.preset_combo.currentText() or "Custom",
            stems=stems,
            device=self.device_combo.currentText().casefold(),
            output_format=output,
            create_backup=self.create_backup.isChecked(),
            continue_on_error=self.continue_on_error.isChecked(),
            delete_backup_after_success=self.delete_backup_after_success.isChecked(),
            use_autocast=self.use_autocast.isChecked(),
        )

    def export_model_state(self) -> dict[str, dict]:
        state: dict[str, dict] = {}
        for stem, _label in STEM_ROWS:
            data = self.model_combos[stem].currentData()
            state[stem] = {
                "enabled": self.stem_checks[stem].isChecked(),
                **(data if isinstance(data, dict) else {}),
            }
        return state

    def apply_model_state(self, state: dict[str, dict]):
        for stem, values in state.items():
            if stem not in self.model_combos or not isinstance(values, dict):
                continue
            self.stem_checks[stem].setChecked(bool(values.get("enabled", False)))
            model_name = str(values.get("model_name", ""))
            combo = self.model_combos[stem]
            found = False
            for index in range(combo.count()):
                data = combo.itemData(index)
                if isinstance(data, dict) and data.get("model_name") == model_name:
                    combo.setCurrentIndex(index)
                    found = True
                    break
            if model_name and not found:
                combo.setCurrentIndex(-1)

    def apply_preset(self, preset: SeparationPreset):
        by_stem = {config.stem: config for config in preset.stems}
        for stem, _label in STEM_ROWS:
            config = by_stem.get(stem)
            self.stem_checks[stem].setChecked(config is not None and config.enabled)
            if config is None:
                continue
            combo = self.model_combos[stem]
            found = False
            for index in range(combo.count()):
                data = combo.itemData(index)
                if data and data.get("model_name") == config.model_name:
                    combo.setCurrentIndex(index)
                    found = True
                    break
            if not found:
                combo.setCurrentIndex(-1)
        self._set_combo_text(self.device_combo, preset.device)
        self._set_combo_text(self.output_format, preset.output_format.replace("_", " "))
        self.create_backup.setChecked(preset.create_backup)
        self.continue_on_error.setChecked(preset.continue_on_error)
        self.delete_backup_after_success.setChecked(preset.delete_backup_after_success)
        self.use_autocast.setChecked(preset.use_autocast)

    @staticmethod
    def _set_combo_text(combo: QComboBox, value: str):
        index = combo.findText(value, flags=Qt.MatchFixedString)
        if index >= 0:
            combo.setCurrentIndex(index)

    def refresh_presets(self, select: str | None = None):
        current = select or self.preset_combo.currentText() or "Custom"
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("Custom")
        self.preset_combo.addItems(self.preset_store.list_names())
        index = self.preset_combo.findText(current)
        self.preset_combo.setCurrentIndex(max(0, index))
        self.preset_combo.blockSignals(False)

    def load_selected_preset(self, name: str):
        if not name or name == "Custom":
            return
        try:
            self.apply_preset(self.preset_store.load(name))
        except Exception as ex:
            QMessageBox.critical(self, "Preset", str(ex))

    def save_preset(self):
        name = self.preset_combo.currentText()
        if name == "Custom":
            self.save_preset_as()
            return
        try:
            self.preset_store.save(self.build_preset(name))
        except Exception as ex:
            QMessageBox.critical(self, "Preset", str(ex))

    def save_preset_as(self):
        name, accepted = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if not accepted or not name.strip():
            return
        try:
            self.preset_store.save(self.build_preset(name.strip()))
            self.refresh_presets(name.strip())
        except Exception as ex:
            QMessageBox.critical(self, "Preset", str(ex))

    def delete_preset(self):
        name = self.preset_combo.currentText()
        if name == "Custom":
            return
        if QMessageBox.question(self, "Delete Preset", f"Delete '{name}'?") != QMessageBox.Yes:
            return
        self.preset_store.delete(name)
        self.refresh_presets("Custom")

    def import_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Preset", "", "JSON (*.json)")
        if not path:
            return
        try:
            preset = self.preset_store.import_file(path)
            self.refresh_presets(preset.name)
            self.apply_preset(preset)
        except Exception as ex:
            QMessageBox.critical(self, "Preset", str(ex))

    def export_preset(self):
        name = self.preset_combo.currentText()
        try:
            preset = self.build_preset(name)
        except Exception as ex:
            QMessageBox.critical(self, "Preset", str(ex))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Preset", f"{name}.json", "JSON (*.json)"
        )
        if path:
            self.preset_store.export(preset, path)

    def open_model_browser(self):
        dialog = ModelBrowserDialog(self)
        dialog.models_changed.connect(self.refresh_models)
        dialog.exec()
        self.refresh_models()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Clone Hero Songs Folder")
        if folder:
            self.folder_input.setText(folder)

    def request_scan(self):
        folder = self.folder_input.text().strip()
        if folder:
            self.scan_requested.emit(folder)

    def update_selected_count(self, count: int):
        self.selected_count_label.setText(f"{count} selected")
        self.start_button.setText(f"Start Processing ({count})" if count else "Start Processing")
