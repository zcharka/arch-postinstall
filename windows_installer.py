import sys
import os
import subprocess
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QProgressBar, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

def resource_path(relative_path):
    """ Pobiera ścieżkę do zasobów, działa dla dev i PyInstallera """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

SOFTWARE_TO_INSTALL = [
    {"name": "Firefox", "id": "Mozilla.Firefox"},
    {"name": "VS Code", "id": "Microsoft.VisualStudioCode"},
    {"name": "Discord", "id": "Discord.Discord"},
    {"name": "Steam",   "id": "Valve.Steam"},
]

class InstallWorker(threading.Thread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool)

    def run(self):
        total = len(SOFTWARE_TO_INSTALL)
        for i, app in enumerate(SOFTWARE_TO_INSTALL):
            cmd = f"winget install --id {app['id']} --silent --accept-source-agreements --accept-package-agreements"
            self.progress_signal.emit(int((i / total) * 100), f"Instalowanie: {app['name']}...")
            subprocess.run(cmd, shell=True)

        self.progress_signal.emit(100, "Zakończono!")
        self.finished_signal.emit(True)

class WindowsInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RatPresets Windows")
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: #1e1e2e; color: white;")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.init_welcome_screen()
        self.init_progress_screen()

    def init_welcome_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # LOGO Z POPRAWNĄ ŚCIEŻKĄ
        self.logo_lbl = QLabel()
        pixmap = QPixmap(resource_path("src/ui/logo.png"))
        if not pixmap.isNull():
            self.logo_lbl.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.logo_lbl.setText("RatPresets")

        self.start_btn = QPushButton("Begin Installation")
        self.start_btn.setFixedSize(300, 60)
        self.start_btn.setStyleSheet("background-color: #a371f7; border-radius: 30px; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_installation)

        layout.addWidget(self.logo_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(page)

    def init_progress_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.status_lbl = QLabel("Inicjalizacja...")
        self.pbar = QProgressBar()
        layout.addWidget(self.status_lbl)
        layout.addWidget(self.pbar)
        self.stack.addWidget(page)

    def start_installation(self):
        self.stack.setCurrentIndex(1)
        self.worker = InstallWorker()
        self.worker.progress_signal.connect(self.update_ui)
        self.worker.finished_signal.connect(lambda: self.status_lbl.setText("Gotowe!"))
        self.worker.start()

    def update_ui(self, val, text):
        self.pbar.setValue(val)
        self.status_lbl.setText(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WindowsInstaller()
    window.show()
    sys.exit(app.exec())
