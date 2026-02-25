import os

def install_gnome_deps(runner):
    runner("echo '--- INSTALACJA NARZĘDZI GNOME ---'")

    # 1. Podstawowe narzędzia i zależności do budowania
    # sassc jest krytyczny dla motywów GTK!
    runner("sudo pacman -S --noconfirm --needed gnome-tweaks gnome-browser-connector gnome-shell-extensions git base-devel sassc wget curl")

    runner("echo '--- INSTALACJA ROZSZERZEŃ Z AUR (YAY) ---'")

    # Twoja pełna lista rozszerzeń + motywy
    extensions = [
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
        # Kursor i motywy
        "bibata-cursor-theme-bin"
    ]

    # Instalacja yay (jednym ciągiem)
    pkg_str = " ".join(extensions)
    runner(f"yay -S --noconfirm --needed --answerdiff=None --answerclean=None {pkg_str}")

def enable_extensions(runner):
    runner("echo '--- AKTYWACJA ROZSZERZEŃ ---'")

    # Lista UUID rozszerzeń odpowiadająca paczkom powyżej.
    # GNOME wymaga podania ID, aby je włączyć z konsoli.
    uuids = [
        "user-theme@gnome-shell-extensions.gcampax.github.com",
        "dash-to-dock@micxgx.gmail.com",
        "blur-my-shell@aunetx",
        "appindicatorsupport@rgcjonas.gmail.com",
        "gsconnect@andyholmes.github.io",
        "ding@rastersoft.com", # Desktop Icons NG
        "quick-settings-audio-panel@rayzeq.github.io",
        "rounded-window-corners@fxgn",
        "drive-menu@gnome-shell-extensions.gcampax.github.com",
        "arch-update@fernandovan", # ID dla archlinux-updates-indicator
        "accent-icons@deminder" # ID dla accent-icons (może się różnić zależnie od forka)
    ]

    for uuid in uuids:
        # Uruchamiamy bez sudo (jako użytkownik), aby zmienić ustawienia dla sesji
        # Ignorujemy błędy, jeśli UUID jest inny lub rozszerzenie się jeszcze nie załadowało
        runner(f"gnome-extensions enable {uuid} || true")

def setup_appearance(runner):
    runner("echo '--- KONFIGURACJA WYGLĄDU (COLLOID) ---'")

    # 1. Pobieranie i instalacja Colloid GTK (Git)
    runner("rm -rf /tmp/colloid-gtk /tmp/colloid-icon") # Czyszczenie
    runner("git clone https://github.com/vinceliuice/Colloid-gtk-theme.git /tmp/colloid-gtk")
    runner("sh /tmp/colloid-gtk/install.sh -t purple -s standard")

    # 2. Pobieranie i instalacja Colloid Icons (Git)
    runner("git clone https://github.com/vinceliuice/Colloid-icon-theme.git /tmp/colloid-icon")
    runner("sh /tmp/colloid-icon/install.sh -t purple")

    # 3. Pobieranie tapety
    runner("mkdir -p ~/Obrazy")
    runner("curl -L 'https://i.imgur.com/Y9X3VQz.jpeg' -o ~/Obrazy/wallpaper.jpg")

    # 4. Aplikowanie ustawień (gsettings)
    cmds = [
        # Motyw i Ikony
        "gsettings set org.gnome.desktop.interface gtk-theme 'Colloid-Purple-Dark'",
        "gsettings set org.gnome.desktop.interface icon-theme 'Colloid-Purple-Dark'",
        "gsettings set org.gnome.desktop.interface cursor-theme 'Bibata-Classic-Black'",

        # Tapeta
        "gsettings set org.gnome.desktop.background picture-uri 'file://$HOME/Obrazy/wallpaper.jpg'",
        "gsettings set org.gnome.desktop.background picture-uri-dark 'file://$HOME/Obrazy/wallpaper.jpg'",
        "gsettings set org.gnome.desktop.background picture-options 'zoom'",

        # Aktywacja User Themes (niezbędne do zmiany Shell Theme)
        "gnome-extensions enable user-theme@gnome-shell-extensions.gcampax.github.com",
        "gsettings set org.gnome.shell.extensions.user-theme name 'Colloid-Purple-Dark'",

        # Ustawienia okien (przycisk minimalizacji/maksymalizacji)
        "gsettings set org.gnome.desktop.wm.preferences button-layout 'appmenu:minimize,maximize,close'"
    ]

    for cmd in cmds:
        runner(cmd)

    # 5. Aktywacja reszty rozszerzeń na koniec
    enable_extensions(runner)
