import sys
import os
import subprocess
import time

# --- 1. MAGICZNA SEKCJA: AUTO-INSTALACJA ZALEŻNOŚCI ---
def install_dependencies():
    """Sprawdza i instaluje PyQt6 oraz Requests na czystym Archu."""
    try:
        import PyQt6
        import requests
    except ImportError:
        print("--- WYKRYTO BRAK BIBLIOTEK (PyQt6/Requests) ---")
        print("--- Rozpoczynam automatyczną instalację... ---")
        try:
            subprocess.check_call(["sudo", "pacman", "-S", "--needed", "--noconfirm", "python-pyqt6", "python-requests"])
            print("--- Zainstalowano pomyślnie! Restartowanie aplikacji... ---")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except subprocess.CalledProcessError as e:
            print(f"BŁĄD INSTALACJI: {e}")
            input("Naciśnij Enter, aby zamknąć...")
            sys.exit(1)

if not getattr(sys, 'frozen', False):
    install_dependencies()

# --- 2. NAPRAWA ŚCIEŻEK IMPORTU ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(src_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# --- IMPORTY ---
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QStackedWidget, QProgressBar,
                             QTextEdit, QInputDialog, QLineEdit, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor
import requests

# --- 3. IMPORT LOGIKI ---
try:
    from src.postinstall import plasma
    BACKEND_LOADED = True
except ImportError:
    try:
        from postinstall import plasma
        BACKEND_LOADED = True
    except ImportError as e:
        print(f"CRITICAL ERROR: Nie znaleziono backendu: {e}")
        BACKEND_LOADED = False
        plasma = None

# --- STYLE CSS (BEZPOŚREDNIO W PLIKU) ---
STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    color: #cdd6f4;
}
QLabel#Title {
    font-size: 26px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 10px;
}
QLabel#SuccessLabel {
    font-size: 28px;
    font-weight: bold;
    color: #a6e3a1;
}
QPushButton#PrimaryBtn {
    background-color: #cba6f7;
    color: #1e1e2e;
    font-weight: bold;
    font-size: 16px;
    border-radius: 20px;
    padding: 12px 30px;
    border: none;
}
QPushButton#PrimaryBtn:hover { background-color: #d8b4fe; }
QPushButton#PrimaryBtn:pressed { background-color: #b492e0; }
QProgressBar {
    background-color: #313244;
    border-radius: 10px;
    height: 12px;
    text-align: center;
    border: none;
}
QProgressBar::chunk {
    background-color: #cba6f7;
    border-radius: 10px;
}
QTextEdit {
    background-color: #11111b;
    color: #a6adc8;
    border: 1px solid #313244;
    border-radius: 12px;
    padding: 10px;
}
"""

# --- KLASA ROBOCZA ---
class InstallWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, password):
        super().__init__()
        self.password = password

    def run_cmd(self, command, use_shell=True):
        if command.startswith("sudo"):
            full_cmd = f"echo '{self.password}' | {command.replace('sudo', 'sudo -S')}"
            use_shell = True
        else:
            full_cmd = command

        self.log_signal.emit(f"$ {command}")

        try:
            process = subprocess.Popen(
                full_cmd,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in process.stdout:
                self.log_signal.emit(line.strip())
            process.wait()
            if process.returncode != 0:
                self.log_signal.emit(f"[OSTRZEŻENIE] Kod wyjścia: {process.returncode}")
        except Exception as e:
            self.log_signal.emit(f"[BŁĄD] {e}")
            raise e

    def run(self):
        try:
            self.log_signal.emit("--- Rozpoczynam instalację ---")
            self.progress_signal.emit(5)

            if not BACKEND_LOADED:
                self.error_signal.emit("BŁĄD KRYTYCZNY: Brak modułów src.postinstall!")
                return

            self.log_signal.emit("Aktualizacja repozytoriów...")
            self.run_cmd("sudo pacman -Sy")
            self.progress_signal.emit(15)

            if plasma:
                plasma.install_plasma_deps(self.run_cmd)
                self.progress_signal.emit(50)
                plasma.apply_custom_look(self.run_cmd)
                self.progress_signal.emit(75)
                plasma.apply_layout_preset(self.run_cmd)
                self.progress_signal.emit(90)

            self.progress_signal.emit(100)
            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))

# --- GŁÓWNE OKNO ---
class ModernInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arch Setup")
        self.setFixedSize(500, 650)
        self.setStyleSheet(STYLESHEET)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainContainer")
        self.central_widget.setStyleSheet("QWidget#MainContainer { background-color: #1e1e2e; border-radius: 15px; }")

        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.init_start_page()
        self.init_install_page()
        self.init_finish_page()

    def get_arch_logo(self):
        url = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Arch_Linux_logo.svg/1024px-Arch_Linux_logo.svg.png"
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                pix = QPixmap()
                pix.loadFromData(r.content)
                return pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        except:
            return None

    def init_start_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        logo = QLabel()
        pix = self.get_arch_logo()
        if pix: logo.setPixmap(pix)
        else:
            logo.setText("ARCH SETUP")
            logo.setObjectName("Title")

        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        title = QLabel("Konfigurator Systemu")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        btn = QPushButton("Rozpocznij instalację")
        btn.setObjectName("PrimaryBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.ask_password)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0,0,0,100))
        shadow.setOffset(0, 5)
        btn.setGraphicsEffect(shadow)

        layout.addWidget(btn)
        self.stack.addWidget(page)

    def init_install_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_lbl = QLabel("Przygotowywanie...")
        layout.addWidget(self.status_lbl)

        self.prog_bar = QProgressBar()
        self.prog_bar.setValue(0)
        layout.addWidget(self.prog_bar)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.hide()
        layout.addWidget(self.console)

        self.btn_details = QPushButton("Pokaż szczegóły")
        self.btn_details.setCheckable(True)
        self.btn_details.setStyleSheet("background: transparent; color: #a6adc8; border: 1px solid #45475a;")
        self.btn_details.clicked.connect(self.toggle_console)
        layout.addWidget(self.btn_details)

        self.stack.addWidget(page)

    def init_finish_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel("Gotowe!")
        lbl.setObjectName("SuccessLabel")
        layout.addWidget(lbl)

        btn = QPushButton("Zakończ")
        btn.setObjectName("PrimaryBtn")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)
        self.stack.addWidget(page)

    def ask_password(self):
        pwd, ok = QInputDialog.getText(self, "Sudo", "Podaj hasło administratora:", QLineEdit.EchoMode.Password)
        if ok and pwd:
            self.stack.setCurrentIndex(1)
            self.start_install(pwd)

    def start_install(self, pwd):
        self.worker = InstallWorker(pwd)
        self.worker.progress_signal.connect(self.prog_bar.setValue)
        self.worker.log_signal.connect(self.log_msg)
        self.worker.finished_signal.connect(lambda: self.stack.setCurrentIndex(2))
        self.worker.start()

    def log_msg(self, text):
        self.console.append(text)
        if not text.startswith("$"):
            self.status_lbl.setText(text[:50] + "...")

    def toggle_console(self):
        if self.btn_details.isChecked():
            self.console.show()
            self.btn_details.setText("Ukryj")
        else:
            self.console.hide()
            self.btn_details.setText("Pokaż")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ModernInstaller()
    win.show()
    sys.exit(app.exec())
