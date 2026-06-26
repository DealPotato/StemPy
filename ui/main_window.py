from PySide6.QtWidgets import QLabel, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("StemPy")
        self.resize(1200, 800)

        label = QLabel("Hello StemPy")
        label.setMargin(20)

        self.setCentralWidget(label)