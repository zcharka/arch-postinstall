import os

# --- FUNKCJE INSTALACYJNE GNOME ---

def install_gnome_deps(runner):
    runner("echo 'Instaluję narzędzia GNOME i zależności...'")

    # 1. Pakiety oficjalne (potrzebne do motywów i extensions)
    # gnome-shell-extensions jest kluczowe dla user-theme
    base_pkgs = [
        "gnome-tweaks",
        "gnome-browser-connector",
        "gnome-shell-extensions",
        "git",
        "curl",
        "wget"
    ]
    runner(f"sudo pacman -S --noconfirm --needed {' '.join(base_pkgs)}")

    runner("echo 'Instaluję rozszerzenia z AUR...'")

    # 2. Lista rozszerzeń z Twojego setup.sh
    aur_extensions = [
        "gnome-shell-extension-accent-icons-git",
        "gnome-shell-extension-appindicator",
        "gnome-shell-extension-blur-my-shell",
        "gnome-shell-extension-dash-to-dock",
        "gnome-shell-extension-ding",
        "gnome-shell-extension-gsconnect",
        "gnome-shell-extension-quick-settings-audio-panel",
        "gnome-shell-extension-rounded-window-corners-reborn-git",
        "gnome-shell-extension-user-theme",
        "gnome-shell-extension-removable-drive-menu",
        "gnome-shell-extension-archlinux-updates-indicator",
        # Dodajemy kursor z AUR, jeśli nie ma go w oficjalnych
        "bibata-cursor-theme-bin"
    ]

    pkgs_str = " ".join(aur_extensions)
    runner(f"yay -S --noconfirm --needed {pkgs_str}")

def install_colloid_themes(runner):
    """
    Klonuje i instaluje motywy Colloid bezpośrednio z GitHuba, tak jak w setup.sh
    """
    runner("echo 'Pobieranie i instalacja motywu GTK Colloid...'")

    # Używamy folderu tymczasowego
    tmp_dir = "/tmp/arch_postinstall_colloid"
    runner(f"mkdir -p {tmp_dir}")

    # 1. Motyw GTK
    cmds_gtk = [
        f"git clone https://github.com/vinceliuice/Colloid-gtk-theme.git {tmp_dir}/gtk",
        f"sh {tmp_dir}/gtk/install.sh -t purple -s standard",
        f"rm -rf {tmp_dir}/gtk"
    ]
    for cmd in cmds_gtk:
        runner(cmd)

    runner("echo 'Pobieranie i instalacja ikon Colloid...'")

    # 2. Ikony
    cmds_icons = [
        f"git clone https://github.com/vinceliuice/Colloid-icon-theme.git {tmp_dir}/icons",
        f"sh {tmp_dir}/icons/install.sh -t purple",
        f"rm -rf {tmp_dir}/icons"
    ]
    for cmd in cmds_icons:
        runner(cmd)

    runner(f"rm -rf {tmp_dir}")

def setup_wallpaper(runner):
    """
    Pobiera tapetę z Imgur i ustawia ją w GNOME
    """
    runner("echo 'Ustawiam tapetę...'")

    url = "https://i.imgur.com/Y9X3VQz.jpeg"
    dest_dir = os.path.expanduser("~/Obrazy") # Python rozwinie ~ do /home/user
    file_name = "tapeta_arch.jpg"
    full_path = os.path.join(dest_dir, file_name)

    # Tworzymy folder i pobieramy
    runner(f"mkdir -p {dest_dir}")
    runner(f"curl -L '{url}' -o '{full_path}'")

    # Ustawiamy w gsettings (file:// jest wymagane)
    uri_path = f"file://{full_path}"

    settings_cmds = [
        f"gsettings set org.gnome.desktop.background picture-uri '{uri_path}'",
        f"gsettings set org.gnome.desktop.background picture-uri-dark '{uri_path}'",
        "gsettings set org.gnome.desktop.background picture-options 'zoom'"
    ]
    for cmd in settings_cmds:
        runner(cmd)

def setup_appearance(runner):
    runner("echo 'Aplikuję wygląd Colloid (Purple)...'")

    # Najpierw musimy zainstalować motywy ręcznie z gita
    install_colloid_themes(runner)
    setup_wallpaper(runner)

    # Włączamy rozszerzenie User Themes (niezbędne do zmiany Shell Theme)
    runner("gnome-extensions enable user-theme@gnome-shell-extensions.gcampax.github.com")

    commands = [
        # GTK Theme
        "gsettings set org.gnome.desktop.interface gtk-theme 'Colloid-Purple-Dark'",
        # Shell Theme (wymaga user-theme extension)
        "gsettings set org.gnome.shell.extensions.user-theme name 'Colloid-Purple-Dark'",
        # Ikony
        "gsettings set org.gnome.desktop.interface icon-theme 'Colloid-Purple-Dark'",
        # Kursor
        "gsettings set org.gnome.desktop.interface cursor-theme 'Bibata-Classic-Black'",
        # Fonty (opcjonalnie, jeśli chcesz jak w setup.sh)
        # "gsettings set org.gnome.desktop.interface monospace-font-name 'JetBrainsMono Nerd Font 10'"
    ]

    for cmd in commands:
        # Używamy trybu user (bez sudo), runner w main_window powinien to obsługiwać
        runner(cmd)
