import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QStackedWidget, QProgressBar,
                             QTextEdit, QInputDialog, QLineEdit, QListWidget, QListWidgetItem,
                             QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QColor, QFont

# --- 1. BEZPIECZNE IMPORTY BACKENDU ---
try:
    from src.postinstall import plasma, system, gnome
    BACKEND_LOADED = True
except ImportError:
    try:
        from postinstall import plasma, system, gnome
        BACKEND_LOADED = True
    except ImportError:
        BACKEND_LOADED = False
        print("Backend not loaded - running in UI demo mode")

# --- 2. LOGIKA INSTALACJI (WORKER) ---
class InstallWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, password, tasks):
        super().__init__()
        self.password = password
        self.tasks = tasks  # Lista zadań do wykonania

    def run_cmd(self, command, use_shell=True):
        # 1. Automatyczne odpowiedzi dla YAY
        if "yay" in command and "--answer" not in command:
            command = command.replace("yay", "yay --answerdiff All --answerclean All --noconfirm")

        # 2. Automatyczne pomijanie zainstalowanych pakietów (PACMAN)
        if "pacman -S" in command and "--needed" not in command:
             # Wstawiamy --needed po 'pacman -S' lub 'pacman -Sy'
             if "-S" in command:
                 command = command.replace("-S", "-S --needed")
             elif "-Sy" in command:
                 command = command.replace("-Sy", "-Sy --needed")
             elif "-Syu" in command:
                 command = command.replace("-Syu", "-Syu --needed")

        # 3. Obsługa SUDO
        if command.startswith("sudo"):
            full_cmd = f"echo '{self.password}' | {command.replace('sudo', 'sudo -S')}"
            use_shell = True
        else:
            full_cmd = command

        self.log_signal.emit(f"➜ {command}")

        try:
            process = subprocess.Popen(
                full_cmd,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            for line in process.stdout:
                self.log_signal.emit(line.strip())
            process.wait()
            if process.returncode != 0:
                self.log_signal.emit(f"[!] Kod wyjścia: {process.returncode}")
        except Exception as e:
            self.error_signal.emit(str(e))

    def run(self):
        try:
            self.log_signal.emit("--- Rozpoczynam instalację ---")
            total_steps = len(self.tasks)

            for index, task_func in enumerate(self.tasks):
                progress = int((index / total_steps) * 100)
                self.progress_signal.emit(progress)
                # Wykonaj funkcję z logiki, przekazując self.run_cmd
                if callable(task_func):
                    task_func(self.run_cmd)

            self.progress_signal.emit(100)
            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))

# --- 3. UI W STYLU LINEXIN CENTER (SIDEBAR) ---
class ModernInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arch Post-Install")
        self.resize(900, 600)
        self.setup_styles()

        # Główny kontener
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- LEWY PANEL (SIDEBAR) ---
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        self.sidebar.currentRowChanged.connect(self.change_page)
        main_layout.addWidget(self.sidebar)

        # --- PRAWY PANEL (CONTENT) ---
        content_container = QWidget()
        content_container.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages)
        main_layout.addWidget(content_container)

        # Inicjalizacja stron
        self.init_home_page()
        self.init_plasma_page()
        self.init_console_page()

        # Dodawanie pozycji do menu
        self.add_menu_item("Start", "home")
        self.add_menu_item("KDE Plasma", "monitor")
        self.add_menu_item("Logi Instalacji", "terminal")

        self.sidebar.setCurrentRow(0)

    def setup_styles(self):
        # Styl inspirowany Linexin Center (Adwaita Dark / Catppuccin)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; color: #cdd6f4; }
            QWidget#ContentArea { background-color: #1e1e2e; }

            /* Sidebar Styling */
            QListWidget#Sidebar {
                background-color: #181825;
                border: none;
                outline: none;
                padding-top: 20px;
            }
            QListWidget#Sidebar::item {
                height: 50px;
                padding-left: 15px;
                color: #a6adc8;
                border-left: 3px solid transparent;
            }
            QListWidget#Sidebar::item:selected {
                background-color: #313244;
                color: #ffffff;
                border-left: 3px solid #cba6f7;
            }
            QListWidget#Sidebar::item:hover {
                background-color: #1e1e2e;
            }

            /* Buttons */
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                border: 1px solid #45475a;
            }
            QPushButton:hover {
                background-color: #45475a;
                border: 1px solid #585b70;
            }
            QPushButton#PrimaryBtn {
                background-color: #cba6f7;
                color: #1e1e2e;
                font-weight: bold;
                border: none;
            }
            QPushButton#PrimaryBtn:hover { background-color: #d8b4fe; }

            /* Text & Console */
            QLabel { font-size: 14px; }
            QLabel#Header { font-size: 24px; font-weight: bold; color: #ffffff; margin-bottom: 10px; }
            QTextEdit {
                background-color: #11111b;
                color: #a6e3a1;
                border-radius: 10px;
                border: 1px solid #313244;
                font-family: 'Consolas', 'Monospace';
            }
            QProgressBar {
                background-color: #313244;
                border-radius: 5px;
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #cba6f7;
                border-radius: 5px;
            }
        """)

    def add_menu_item(self, name, icon_name=None):
        item = QListWidgetItem(name)
        # Tu można by dodać ikony (QIcon), jeśli masz pliki
        item.setSizeHint(QSize(0, 50))
        font = QFont()
        font.setPointSize(11)
        item.setFont(font)
        self.sidebar.addItem(item)

    def change_page(self, index):
        self.pages.setCurrentIndex(index)

    # --- STRONA 1: HOME ---
    def init_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        header = QLabel("Witaj w Instalatorze Arch")
        header.setObjectName("Header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel("Wybierz moduł z menu po lewej stronie, aby rozpocząć konfigurację.\nTen program zainstaluje motywy, ikony i skonfiguruje system.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #a6adc8;")

        layout.addStretch()
        layout.addWidget(header)
        layout.addWidget(desc)
        layout.addStretch()

        self.pages.addWidget(page)

    # --- STRONA 2: PLASMA CONFIG ---
    def init_plasma_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        header = QLabel("Konfiguracja KDE Plasma")
        header.setObjectName("Header")

        info = QLabel("Zostaną zainstalowane:\n- Motyw Layan\n- Ikony Tela Circle\n- Kursor Bibata Classic\n- Efekty Kwin")
        info.setStyleSheet("background-color: #313244; padding: 15px; border-radius: 10px;")

        btn_install = QPushButton("Zainstaluj i Konfiguruj")
        btn_install.setObjectName("PrimaryBtn")
        btn_install.clicked.connect(lambda: self.start_installation("plasma"))

        layout.addWidget(header)
        layout.addWidget(info)
        layout.addStretch()
        layout.addWidget(btn_install)

        self.pages.addWidget(page)

    # --- STRONA 3: KONSOLA (LOGI) ---
    def init_console_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.status_label = QLabel("Oczekiwanie na zadania...")
        self.status_label.setObjectName("Header")

        self.progress = QProgressBar()
        self.progress.setValue(0)

        self.console = QTextEdit()
        self.console.setReadOnly(True)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.console)

        self.pages.addWidget(page)

    # --- LOGIKA STARTU ---
    def start_installation(self, module_type):
        pwd, ok = QInputDialog.getText(self, "Uprawnienia Root", "Podaj hasło administratora (sudo):", QLineEdit.EchoMode.Password)
        if not ok or not pwd:
            return

        # Przełącz na zakładkę konsoli (ostatnią)
        self.sidebar.setCurrentRow(self.sidebar.count() - 1)
        self.console.clear()

        tasks = []

        # Definiowanie zadań w zależności od wyboru
        if module_type == "plasma" and BACKEND_LOADED:
            # Używamy lambdy, żeby przekazać run_cmd później w workerze
            tasks.append(lambda cmd_runner: plasma.install_plasma_deps(cmd_runner))
            tasks.append(lambda cmd_runner: plasma.apply_custom_look(cmd_runner))
            tasks.append(lambda cmd_runner: plasma.apply_layout_preset(cmd_runner))

        self.worker = InstallWorker(pwd, tasks)
        self.worker.log_signal.connect(self.console.append)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(lambda: self.status_label.setText("Zakończono pomyślnie!"))
        self.worker.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernInstaller()
    window.show()
    sys.exit(app.exec())
