import subprocess
import os
import sys

# --- WAŻNE DLA PYINSTALLERA ---
def resource_path(relative_path):
    """ Zwraca absolutną ścieżkę do zasobu, działającą zarówno w Dev jak i w PyInstaller """
    try:
        # PyInstaller tworzy folder tymczasowy w _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- FUNKCJE INSTALACYJNE ---

def install_plasma_deps(runner):
    """
    runner: funkcja przyjmująca treść komendy (np. self.run_cmd z GUI)
    """
    runner("echo 'Instaluję dodatki dla KDE Plasma (Themes, Effects)...'")

    # Lista pakietów z AUR
    aur_packages = [
        "layan-kde-git",                    # Motyw Layan
        "tela-circle-icon-theme-git",       # Ikony
        "kwin-effects-better-blur-dx-git",  # Blur
        "kwin-effect-rounded-window-corners-git", # Zaokrąglone rogi
        "bibata-cursor-theme-bin"           # Kursor
    ]

    # Instalacja (zakładamy, że yay jest skonfigurowany)
    # Używamy join, żeby stworzyć jeden długi string
    packages_str = " ".join(aur_packages)
    runner(f"yay -S --noconfirm {packages_str}")

def apply_custom_look(runner):
    runner("echo 'Aplikuję wygląd Layan i efekty...'")

    # 1. Ustawienie Motywu Globalnego
    # Próbujemy, ale nie przerywamy w razie błędu (try/except obsłużone w runnerze GUI lub ignorowane tutaj)
    runner("plasma-apply-lookandfeel -a org.kde.layan.desktop || echo 'Ostrzeżenie: Nie udało się narzucić motywu globalnego'")

    # 2. Ustawienie Kursora
    runner("kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme Bibata-Classic-Black")
    runner("kwriteconfig6 --file kcminputrc --group Mouse --key cursorSize 24")

    # 3. Włączenie efektów KWin
    kwinrc_cmds = [
        "kwriteconfig6 --file kwinrc --group Plugins --key betterblurEnabled true",
        "kwriteconfig6 --file kwinrc --group Plugins --key rounded-window-cornersEnabled true",
        # Przeładowanie KWin
        "qdbus6 org.kde.KWin /KWin reconfigure"
    ]
    for cmd in kwinrc_cmds:
        runner(cmd)

def apply_layout_preset(runner):
    runner("echo 'Ustawiam układ paneli (Dock + Top Bar)...'")

    # --- TU BYŁ BŁĄD: Teraz używamy poprawnie resource_path ---
    # Szukamy pliku js wewnątrz paczki programu
    script_path = resource_path(os.path.join("src", "layouts", "custom_dock.js"))

    if os.path.exists(script_path):
        # Wczytujemy treść skryptu do zmiennej, aby uniknąć problemów ze ścieżkami w shellu
        try:
            with open(script_path, 'r') as f:
                script_content = f.read()

            # Escape'owanie cudzysłowów dla basha jest trudne,
            # więc bezpieczniej jest zapisać skrypt w tmp i go wykonać
            runner(f"cp '{script_path}' /tmp/layout_script.js")
            runner("qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript \"$(cat /tmp/layout_script.js)\"")

        except Exception as e:
            runner(f"echo 'Błąd odczytu skryptu layoutu: {e}'")
    else:
        runner(f"echo 'Błąd: Nie znaleziono pliku layoutu pod ścieżką: {script_path}'")
