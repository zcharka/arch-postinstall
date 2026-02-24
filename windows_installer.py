import sys
import subprocess
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QProgressBar, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap

# --- KONFIGURACJA PAKIETÓW WINDOWS (Winget) ---
SOFTWARE_TO_INSTALL = [
    {"name": "Firefox", "id": "Mozilla.Firefox"},
    {"name": "VS Code", "id": "Microsoft.VisualStudioCode"},
    {"name": "Discord", "id": "Discord.Discord"},
    {"name": "Steam",   "id": "Valve.Steam"},
]

class InstallWorker(threading.Thread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

    def run(self):
        total = len(SOFTWARE_TO_INSTALL)
        for i, app in enumerate(SOFTWARE_TO_INSTALL):
            # Używamy winget - wbudowanego menedżera pakietów Windows
            cmd = f"winget install --id {app['id']} --silent --accept-source-agreements --accept-package-agreements"

            progress = int((i / total) * 100)
            self.progress_signal.emit(progress, f"Instalowanie: {app['name']}...")

            try:
                subprocess.run(cmd, shell=True, check=True)
            except:
                pass # Kontynuuj nawet przy błędzie jednego pakietu

        self.progress_signal.emit(100, "Zakończono!")
        self.finished_signal.emit(True)

class WindowsInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linexin Windows Post-Install")
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: #1e1e2e; color: white; font-family: 'Segoe UI', sans-serif;")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.init_welcome_screen()
        self.init_progress_screen()

    def init_welcome_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)

        welcome_lbl = QLabel("Welcome to")
        welcome_lbl.setStyleSheet("font-size: 32px; font-weight: bold;")
        welcome_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # LOGO (Upewnij się, że masz plik logo.png w folderze)
        self.logo_lbl = QLabel()
        pixmap = QPixmap("src/ui/logo.png") # Ścieżka do Twojego logo
        if not pixmap.isNull():
            self.logo_lbl.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.logo_lbl.setText("LINEXIN")
            self.logo_lbl.setStyleSheet("font-size: 60px; font-weight: 800; color: #cba6f7;")
        self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # FIOLETOWY PRZYCISK (Styl ze screena)
        self.start_btn = QPushButton("Begin Installation")
        self.start_btn.setFixedSize(300, 60)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #a371f7;
                color: white;
                border-radius: 30px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b48dfa;
            }
        """)
        self.start_btn.clicked.connect(self.start_installation)

        layout.addStretch()
        layout.addWidget(welcome_lbl)
        layout.addWidget(self.logo_lbl)
        layout.addStretch()
        layout.addWidget(self.start_btn)
        layout.addSpacing(40)

        self.stack.addWidget(page)

    def init_progress_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_lbl = QLabel("Inicjalizacja...")
        self.status_lbl.setStyleSheet("font-size: 20px; margin-bottom: 20px;")

        self.pbar = QProgressBar()
        self.pbar.setFixedSize(500, 20)
        self.pbar.setStyleSheet("""
            QProgressBar {
                background-color: #313244;
                border-radius: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #cba6f7;
                border-radius: 10px;
            }
        """)

        layout.addWidget(self.status_lbl)
        layout.addWidget(self.pbar)
        self.stack.addWidget(page)

    def start_installation(self):
        self.stack.setCurrentIndex(1)
        self.worker = InstallWorker()
        self.worker.progress_signal.connect(self.update_ui)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def update_ui(self, val, text):
        self.pbar.setValue(val)
        self.status_lbl.setText(text)

    def on_finished(self):
        self.status_lbl.setText("✅ Instalacja ukończona! Możesz zamknąć okno.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WindowsInstaller()
    window.show()
    sys.exit(app.exec())
