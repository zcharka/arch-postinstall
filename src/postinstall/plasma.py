import os
import sys

# --- ROZWIĄZYWANIE ŚCIEŻEK ---
def get_resource_path(relative_path):
    """
    Znajduje plik relatywnie do lokalizacji TEGO pliku (plasma.py).
    Działa to lepiej niż szukanie w '.' (katalogu roboczym).

    Struktura w /opt/arch-postinstall:
      /opt/arch-postinstall/src/postinstall/plasma.py
      /opt/arch-postinstall/src/layouts/custom_dock.js
    """
    # Pobieramy ścieżkę do folderu, w którym jest ten plik (postinstall)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Wychodzimy jeden poziom wyżej (do src) i wchodzimy w żądaną ścieżkę
    # relative_path powinno być np. "layouts/custom_dock.js"
    return os.path.join(current_dir, "..", relative_path)

# --- FUNKCJE INSTALACYJNE ---

def install_plasma_deps(runner):
    runner("echo 'Instaluję dodatki dla KDE Plasma (Themes, Effects)...'")

    # Lista pakietów z AUR (identyczna jak w Twoim setup.sh dla KDE)
    aur_packages = [
        "layan-kde-git",                    # Motyw Layan
        "tela-circle-icon-theme-git",       # Ikony
        "kwin-effects-better-blur-dx-git",  # Blur
        "kwin-effect-rounded-window-corners-git", # Zaokrąglone rogi
        "bibata-cursor-theme-bin"           # Kursor
    ]

    packages_str = " ".join(aur_packages)
    runner(f"yay -S --noconfirm --needed {packages_str}")

def apply_custom_look(runner):
    runner("echo 'Aplikuję wygląd Layan i efekty...'")

    # 1. Ustawienie Motywu Globalnego
    runner("plasma-apply-lookandfeel -a org.kde.layan.desktop || echo 'Ostrzeżenie: Nie udało się narzucić motywu globalnego'")

    # 2. Ustawienie Kursora
    runner("kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme Bibata-Classic-Black")
    runner("kwriteconfig6 --file kcminputrc --group Mouse --key cursorSize 24")

    # 3. Włączenie efektów KWin
    kwinrc_cmds = [
        "kwriteconfig6 --file kwinrc --group Plugins --key betterblurEnabled true",
        "kwriteconfig6 --file kwinrc --group Plugins --key rounded-window-cornersEnabled true",
        "qdbus6 org.kde.KWin /KWin reconfigure"
    ]
    for cmd in kwinrc_cmds:
        runner(cmd)

def apply_layout_preset(runner):
    runner("echo 'Ustawiam układ paneli (Dock + Top Bar)...'")

    # Szukamy skryptu w folderze layouts (obok postinstall)
    script_path = get_resource_path("layouts/custom_dock.js")

    if os.path.exists(script_path):
        try:
            # Kopiujemy skrypt do /tmp, aby uniknąć problemów z uprawnieniami/znakami specjalnymi
            runner(f"cp '{script_path}' /tmp/layout_script.js")
            runner("qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript \"$(cat /tmp/layout_script.js)\"")
        except Exception as e:
            runner(f"echo 'Błąd wykonywania skryptu layoutu: {e}'")
    else:
        runner(f"echo 'Błąd: Nie znaleziono pliku layoutu: {script_path}'")
