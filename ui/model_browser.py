from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.model_catalog import CatalogModel, ModelCatalogService


class CatalogWorker(QThread):
    loaded = Signal(list)
    failed = Signal(str)

    def __init__(self, service: ModelCatalogService):
        super().__init__()
        self.service = service

    def run(self):
        try:
            self.loaded.emit(self.service.refresh())
        except Exception as ex:
            self.failed.emit(str(ex))


class DownloadWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, service: ModelCatalogService, model: CatalogModel):
        super().__init__()
        self.service = service
        self.model = model

    def run(self):
        try:
            self.service.download(self.model)
            self.completed.emit(self.model)
        except Exception as ex:
            self.failed.emit(str(ex))


class ModelBrowserDialog(QDialog):
    models_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Browser")
        self.resize(1040, 640)

        self.service = ModelCatalogService()
        self.models: list[CatalogModel] = self.service.load_cached()
        self.installed_names = self.service.installed_filenames()
        self.visible_models: list[CatalogModel] = []
        self.worker = None

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search model name, filename, architecture...")
        self.stem_filter = QComboBox()
        self.stem_filter.addItems(
            ["All stems", "Guitar", "Bass", "Drums", "Vocals", "Piano", "Other", "Instrumental"]
        )
        self.refresh_button = QPushButton("Refresh Catalog")

        filters = QHBoxLayout()
        filters.addWidget(self.search_input, stretch=1)
        filters.addWidget(self.stem_filter)
        filters.addWidget(self.refresh_button)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Installed", "Filename", "Architecture", "Output stems", "Friendly name"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

        self.status_label = QLabel()
        self.download_button = QPushButton("Download Selected")
        self.close_button = QPushButton("Close")
        actions = QHBoxLayout()
        actions.addWidget(self.status_label, stretch=1)
        actions.addWidget(self.download_button)
        actions.addWidget(self.close_button)

        layout = QVBoxLayout(self)
        layout.addLayout(filters)
        layout.addWidget(self.table, stretch=1)
        layout.addLayout(actions)

        self.search_input.textChanged.connect(self.apply_filter)
        self.stem_filter.currentTextChanged.connect(self.apply_filter)
        self.refresh_button.clicked.connect(self.refresh_catalog)
        self.download_button.clicked.connect(self.download_selected)
        self.close_button.clicked.connect(self.accept)
        self.table.itemDoubleClicked.connect(lambda _item: self.download_selected())

        self.apply_filter()
        if not self.models:
            self.refresh_catalog()

    def refresh_catalog(self):
        if self.worker is not None and self.worker.isRunning():
            return
        self.set_busy(True, "Loading model catalog...")
        self.worker = CatalogWorker(self.service)
        self.worker.loaded.connect(self.on_catalog_loaded)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.clear_worker)
        self.worker.start()

    def download_selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.visible_models):
            QMessageBox.information(self, "Model Browser", "Select a model first.")
            return
        model = self.visible_models[row]
        if model.filename in self.installed_names:
            QMessageBox.information(self, "Model Browser", "This model is already installed.")
            return

        self.set_busy(True, f"Downloading {model.filename}...")
        self.worker = DownloadWorker(self.service, model)
        self.worker.completed.connect(self.on_downloaded)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.clear_worker)
        self.worker.start()

    def on_catalog_loaded(self, models: list):
        self.models = models
        self.apply_filter()
        self.set_busy(False, f"{len(models)} models available")

    def on_downloaded(self, model: CatalogModel):
        self.installed_names = self.service.installed_filenames()
        self.apply_filter()
        self.set_busy(False, f"Installed {model.filename}")
        self.models_changed.emit()

    def on_failed(self, message: str):
        self.set_busy(False, "Operation failed")
        QMessageBox.critical(self, "Model Browser", message)

    def clear_worker(self):
        worker = self.worker
        self.worker = None
        if worker is not None:
            worker.deleteLater()

    def reject(self):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(
                self,
                "Model Browser",
                "Wait for the current catalog or download operation to finish.",
            )
            return
        super().reject()

    def apply_filter(self, *_args):
        query = self.search_input.text().strip().casefold()
        stem = self.stem_filter.currentText().replace("All stems", "").casefold()
        self.visible_models = [
            model
            for model in self.models
            if (
                not query
                or query in model.filename.casefold()
                or query in model.friendly_name.casefold()
                or query in model.architecture.casefold()
            )
            and (not stem or any(stem in item for item in model.stems))
        ]

        self.table.setRowCount(len(self.visible_models))
        for row, model in enumerate(self.visible_models):
            values = [
                "Yes" if model.filename in self.installed_names else "No",
                model.filename,
                model.architecture,
                ", ".join(model.stems),
                model.friendly_name,
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.status_label.setText(f"{len(self.visible_models)} models shown")

    def set_busy(self, busy: bool, message: str):
        self.refresh_button.setEnabled(not busy)
        self.download_button.setEnabled(not busy)
        self.close_button.setEnabled(not busy)
        self.status_label.setText(message)
