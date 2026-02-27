import subprocess
import os

def install_gnome_deps():
    print("Instaluję narzędzia i rozszerzenia GNOME...")
    # Pakiety z oficjalnych repo
    subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "gnome-tweaks", "gnome-browser-connector"], check=True)

    # Rozszerzenia z AUR przez yay
    extensions = [
        "gnome-shell-extension-accent-icons-git",
        "gnome-shell-extension-blur-my-shell",
        "gnome-shell-extension-dash-to-dock",
        "gnome-shell-extension-user-theme"
        # ... dopisz resztę ze swojej listy
    ]
    subprocess.run(["yay", "-S", "--noconfirm"] + extensions, check=True)

def setup_appearance():
    print("Konfiguruję wygląd GNOME...")
    # Ustawianie kursora i ikon
    commands = [
        ["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "Colloid-purple"],
        ["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", "Bibata-Classic-Black"],
        ["gsettings", "set", "org.gnome.desktop.background", "picture-options", "zoom"]
    ]
    for cmd in commands:
        subprocess.run(cmd)

def install_colloid_themes():
    # Logika klonowania i instalacji Colloid (git clone -> ./install.sh)
    # Python może to zrobić czyściej używając modułu 'shutil' do usuwania folderów
    pass
