import sys
import os
import subprocess
import threading
import urllib.request
import time
import queue
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

# ==============================================================================
# 🔧 KONFIGURACJA
# ==============================================================================

SOFTWARE_LIST = [
    {"name": "Firefox",          "pkg": "org.mozilla.firefox",         "source": "flatpak", "checked": True},
    {"name": "Visual Studio Code", "pkg": "com.visualstudio.code",     "source": "flatpak", "checked": True},
    {"name": "Discord",          "pkg": "com.discordapp.Discord",      "source": "flatpak", "checked": True},
    {"name": "Steam",            "pkg": "com.valvesoftware.Steam",     "source": "flatpak", "checked": False},
    {"name": "Prism Launcher",   "pkg": "org.prismlauncher.PrismLauncher", "source": "flatpak", "checked": True},
    {"name": "Fish",             "pkg": "fish",                        "source": "pacman", "checked": True},
    {"name": "Starship",         "pkg": "starship",                    "source": "pacman", "checked": True},
    {"name": "JetBrains Mono Nerd", "pkg": "ttf-jetbrains-mono-nerd", "source": "pacman", "checked": True},
    {"name": "Bibata Cursor",    "pkg": "bibata-cursor-theme-bin",    "source": "aur", "checked": True},
]

DE_LIST = [
    {"name": "GNOME",             "pkg": "gnome",          "id": "gnome", "checked": False},
    {"name": "KDE Plasma",        "pkg": "plasma-meta",    "id": "kde", "checked": False},
    {"name": "Żadne (tylko programy)", "pkg": "",          "id": "none", "checked": True},
]

# Presety KDE (kopiowane z wcześniejszych wersji)
KDE_PRESETS = [
    {"id": "dock", "name": "✨ Layan Dock", "desc": "Pasek na górze, pływający dock na dole. Motyw Layan, BetterBlur, Rounded Corners."},
    {"id": "standard", "name": "🎨 Layan Standard", "desc": "Klasyczny pasek na dole. Motyw Layan + efekty."},
    {"id": "clean", "name": "🧹 Czysta Plasma", "desc": "Domyślny wygląd Arch Linux. Bez dodatków."},
]

# Skrypty JS dla KDE
JS_LAYOUT_DOCK = """
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) {
    allPanels[i].remove();
}
var topPanel = new Panel();
topPanel.location = "top";
topPanel.height = 30;
topPanel.addWidget("org.kde.plasma.kickoff");
topPanel.addWidget("org.kde.plasma.pager");
topPanel.addWidget("org.kde.plasma.panelspacer");
topPanel.addWidget("org.kde.plasma.clock");
topPanel.addWidget("org.kde.plasma.systemtray");
var bottomPanel = new Panel();
bottomPanel.location = "bottom";
bottomPanel.height = 48;
bottomPanel.lengthMode = "fit";
bottomPanel.hiding = "dodgewindows";
bottomPanel.floating = true;
bottomPanel.addWidget("org.kde.plasma.icontasks");
"""

JS_LAYOUT_STANDARD = """
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) {
    allPanels[i].remove();
}
var panel = new Panel();
panel.location = "bottom";
panel.height = 44;
panel.addWidget("org.kde.plasma.kickoff");
panel.addWidget("org.kde.plasma.pager");
panel.addWidget("org.kde.plasma.icontasks");
panel.addWidget("org.kde.plasma.panelspacer");
panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.clock");
"""

# ==============================================================================
# 🧠 BACKEND (INSTALATOR)
# ==============================================================================

class InstallWorker(threading.Thread):
    def __init__(self, password, queue, de_id, kde_preset, on_progress, on_log, on_finish):
        super().__init__()
        self.password = password
        self.queue = queue          # lista programów do zainstalowania (zaznaczone aplikacje)
        self.de_id = de_id          # 'gnome', 'kde', 'none'
        self.kde_preset = kde_preset # 'dock', 'standard', 'clean' (jeśli de_id == 'kde')
        self.on_progress = on_progress
        self.on_log = on_log
        self.on_finish = on_finish
        self.daemon = True
        self.stop_flag = False
        # Przybliżona liczba kroków: aktualizacja, yay (jeśli brak), flatpak, pakiety + konfiguracja DE
        self.total_steps = 5 + len(queue) + (10 if de_id == 'gnome' else 6 if de_id == 'kde' else 0)

    def log(self, text):
        """Wysyła log do GUI."""
        GLib.idle_add(lambda: self.on_log(text))

    def run_cmd(self, cmd_list, use_shell=False, check=True):
        """Uruchamia komendę, loguje wyjście, zwraca True/False."""
        if cmd_list[0] == "sudo":
            # Wstaw hasło przez stdin
            cmd_str = " ".join(cmd_list).replace("sudo", "sudo -S", 1)
            full_cmd = f"echo '{self.password}' | {cmd_str}"
            use_shell = True
        else:
            full_cmd = cmd_list if isinstance(cmd_list, str) else ' '.join(cmd_list)

        self.log(f"$ {full_cmd}")
        process = subprocess.Popen(
            full_cmd,
            shell=use_shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            executable='/bin/bash' if use_shell else None
        )

        for line in process.stdout:
            if self.stop_flag:
                process.terminate()
                break
            self.log(line.rstrip())
        process.wait()
        success = process.returncode == 0
        if not success and check:
            self.log(f"❌ Błąd: komenda zwróciła kod {process.returncode}")
        return success

    def install_pkg(self, source, pkg_name):
        """Instaluje pakiet w zależności od źródła."""
        if source == "flatpak":
            return self.run_cmd(["sudo", "flatpak", "install", "flathub", pkg_name, "-y"])
        elif source == "aur":
            # yay musi być zainstalowane
            return self.run_cmd(["yay", "-S", pkg_name, "--noconfirm", "--answerdiff=None", "--answerclean=All"])
        else:  # pacman
            return self.run_cmd(["sudo", "pacman", "-S", pkg_name, "--noconfirm", "--needed"])

    def ensure_yay(self):
        """Sprawdza czy yay jest, jeśli nie – instaluje."""
        if subprocess.run(["which", "yay"], capture_output=True).returncode == 0:
            return True
        self.log("yay nie znaleziono – instaluję...")
        # Zainstaluj base-devel i git jeśli potrzeba
        self.run_cmd(["sudo", "pacman", "-S", "--needed", "--noconfirm", "base-devel", "git"])
        # Klonuj i buduj yay
        self.run_cmd(["git", "clone", "https://aur.archlinux.org/yay.git", "/tmp/yay"])
        self.run_cmd(["makepkg", "-si", "--noconfirm"], cwd="/tmp/yay")
        self.run_cmd(["rm", "-rf", "/tmp/yay"])
        return True

    def configure_gnome(self):
        """Konfiguracja GNOME: rozszerzenia, motywy Colloid, tapeta, kursor, ikony."""
        self.log("🔧 Konfiguracja GNOME...")
        # Rozszerzenia z AUR
        gnome_extensions = [
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
            "gnome-shell-extension-archlinux-updates-indicator"
        ]
        for ext in gnome_extensions:
            self.install_pkg("aur", ext)

        # Motywy Colloid (GTK, ikony)
        self.log("🎨 Instalacja motywu Colloid GTK...")
        self.run_cmd(["git", "clone", "https://github.com/vinceliuice/Colloid-gtk-theme.git", "/tmp/Colloid-gtk-theme"])
        self.run_cmd(["bash", "/tmp/Colloid-gtk-theme/install.sh", "-t", "purple", "-s", "standard"])
        self.run_cmd(["rm", "-rf", "/tmp/Colloid-gtk-theme"])

        self.log("🎨 Instalacja ikon Colloid...")
        self.run_cmd(["git", "clone", "https://github.com/vinceliuice/Colloid-icon-theme.git", "/tmp/Colloid-icon-theme"])
        self.run_cmd(["bash", "/tmp/Colloid-icon-theme/install.sh", "-t", "purple"])
        self.run_cmd(["rm", "-rf", "/tmp/Colloid-icon-theme"])

        # Ustawienia: ikony, kursor, tapeta
        self.run_cmd(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "Colloid-purple"])
        self.run_cmd(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", "Bibata-Classic-Black"])

        # Pobierz tapetę
        wallpaper_url = "https://i.imgur.com/Y9X3VQz.jpeg"
        wallpaper_name = "tapeta_arch.jpg"
        download_path = os.path.expanduser(f"~/Pobrane/{wallpaper_name}")
        final_path = os.path.expanduser(f"~/Obrazy/{wallpaper_name}")
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        self.log("🌄 Pobieranie tapety...")
        self.run_cmd(["curl", "-L", wallpaper_url, "-o", download_path])
        self.run_cmd(["cp", download_path, final_path])
        self.run_cmd(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{final_path}"])
        self.run_cmd(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", f"file://{final_path}"])
        self.run_cmd(["gsettings", "set", "org.gnome.desktop.background", "picture-options", "zoom"])

        # Opcjonalnie rEFInd (jeśli istnieje katalog EFI)
        if os.path.exists("/boot/EFI/refind"):
            self.log("🖥️ Konfiguracja rEFInd...")
            root_uuid = subprocess.check_output(["findmnt", "-n", "-o", "UUID", "/"]).decode().strip()
            params = f"rw root=UUID={root_uuid} video=HDMI-A-1:d"
            # Sprawdź nvidie
            lspci = subprocess.check_output(["lspci"]).decode().lower()
            if "nvidia" in lspci:
                params += " nvidia-drm.modeset=1"
            # Microcode
            ucode = "initrd=\\intel-ucode.img"
            with open("/proc/cpuinfo") as f:
                if "amd" in f.read().lower():
                    ucode = "initrd=\\amd-ucode.img"
            config = f'"Standard Boot"  "{params} {ucode} initrd=\\initramfs-linux.img"\n'
            config += f'"Terminal Boot"  "{params} {ucode} initrd=\\initramfs-linux.img systemd.unit=multi-user.target"\n'
            with open("/tmp/refind_linux.conf", "w") as f:
                f.write(config)
            self.run_cmd(["sudo", "cp", "/tmp/refind_linux.conf", "/boot/EFI/refind/refind_linux.conf"])

        # Zmiana powłoki na fish (jeśli fish był zainstalowany)
        if any(item['pkg'] == 'fish' for item in self.queue):
            self.log("🐟 Ustawianie fish jako domyślnej powłoki...")
            self.run_cmd(["chsh", "-s", "/usr/bin/fish", os.environ.get('USER')])

        self.log("✅ Konfiguracja GNOME zakończona.")

    def configure_kde(self):
        """Konfiguracja KDE w zależności od wybranego preset."""
        self.log("🔧 Konfiguracja KDE Plasma...")
        if self.kde_preset == "clean":
            # Tylko domyślny wygląd
            self.apply_kde_layout(JS_LAYOUT_STANDARD)
            self.run_cmd(["lookandfeeltool", "-a", "org.kde.breeze.desktop"])
            self.run_cmd(["kwriteconfig6", "--file", "kwinrc", "--group", "Plugins", "--key", "betterblurEnabled", "false"])
            self.run_cmd(["kwriteconfig6", "--file", "kwinrc", "--group", "Plugins", "--key", "roundedcornersEnabled", "false"])
            return

        # Dla dock/standard: zainstaluj motywy
        aur_pkgs = [
            "layan-kde-git",
            "bibata-cursor-theme-bin",
            "papirus-icon-theme",
            "kwin-effects-better-blur-dx-git",
            "kwin-effect-rounded-corners-git"
        ]
        for pkg in aur_pkgs:
            self.install_pkg("aur", pkg)

        if self.kde_preset == "dock":
            self.apply_kde_layout(JS_LAYOUT_DOCK)
            theme_cmd = "lookandfeeltool -a com.github.vinceliuice.Layan"
        else:  # standard
            self.apply_kde_layout(JS_LAYOUT_STANDARD)
            theme_cmd = "lookandfeeltool -a com.github.vinceliuice.Layan"

        # Zastosuj motyw globalny i efekty
        self.run_cmd(theme_cmd.split())
        self.run_cmd(["kwriteconfig6", "--file", "kwinrc", "--group", "Plugins", "--key", "betterblurEnabled", "true"])
        self.run_cmd(["kwriteconfig6", "--file", "kwinrc", "--group", "Plugins", "--key", "roundedcornersEnabled", "true"])
        self.run_cmd(["kwriteconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", "Bibata-Classic-Black"])
        self.run_cmd(["kwriteconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorSize", "24"])
        # Przeładowanie KWin
        self.run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"])
        self.log("✅ Konfiguracja KDE zakończona.")

    def apply_kde_layout(self, js_script):
        """Zapisuje skrypt JS i wykonuje go przez qdbus."""
        script_path = "/tmp/plasma_layout.js"
        with open(script_path, "w") as f:
            f.write(js_script)
        self.run_cmd(["qdbus6", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", f'$(cat {script_path})'])

    def run(self):
        current_step = 0

        def progress(percent, msg):
            self.on_progress(percent, msg)

        # 1. Aktualizacja systemu
        progress(5, "Aktualizacja systemu...")
        self.run_cmd(["sudo", "pacman", "-Syu", "--noconfirm"])

        # 2. Instalacja podstawowych narzędzi (git, base-devel, flatpak)
        progress(10, "Instalacja narzędzi (git, base-devel, flatpak)...")
        self.run_cmd(["sudo", "pacman", "-S", "--needed", "--noconfirm", "git", "base-devel", "flatpak"])

        # 3. Upewnij się, że yay jest
        self.ensure_yay()

        # 4. Dodaj repozytorium flathub
        self.run_cmd(["sudo", "flatpak", "remote-add", "--if-not-exists", "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"])

        # 5. Instalacja wybranych programów
        for idx, item in enumerate(self.queue):
            percent = int((idx / len(self.queue)) * 40) + 20  # 20-60%
            progress(percent, f"Instalacja: {item['name']}...")
            self.install_pkg(item.get('source', 'pacman'), item['pkg'])
            current_step += 1

        # 6. Konfiguracja środowiska graficznego
        if self.de_id == 'gnome':
            progress(70, "Konfiguracja GNOME...")
            self.configure_gnome()
        elif self.de_id == 'kde':
            progress(70, "Konfiguracja KDE Plasma...")
            self.configure_kde()
        else:
            progress(70, "Brak dodatkowej konfiguracji środowiska.")

        # 7. Końcowe porządki (starship dla fish jeśli fish był zainstalowany)
        if any(item['pkg'] == 'fish' for item in self.queue) and self.de_id != 'gnome':
            # Jeśli GNOME już to zrobił, pomiń
            self.log("🐟 Ustawianie fish jako domyślnej powłoki...")
            self.run_cmd(["chsh", "-s", "/usr/bin/fish", os.environ.get('USER')])
            # Konfiguracja starship
            fish_config = os.path.expanduser("~/.config/fish/config.fish")
            os.makedirs(os.path.dirname(fish_config), exist_ok=True)
            with open(fish_config, "a") as f:
                f.write("\nstarship init fish | source\n")

        progress(100, "Instalacja zakończona!")
        GLib.idle_add(self.on_finish, True)

# ==============================================================================
# 🎨 GUI
# ==============================================================================

class InstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="RatInstall")
        self.set_default_size(950, 700)

        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self.load_css()

        self.selected_preset = "clean"
        self.selected_de = "none"

        self.stack = Adw.ViewStack()
        self.header = Adw.HeaderBar()
        self.header.set_show_end_title_buttons(True)
        self.header.set_show_start_title_buttons(False)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.header)
        main_box.append(self.stack)
        self.set_content(main_box)

        self.init_welcome()
        self.init_soft()
        self.init_de()
        self.init_kde_presets()
        self.init_progress()
        self.init_finish()

    def load_css(self):
        provider = Gtk.CssProvider()
        css = b"""
        .blue-btn { background-color: #3584e4; color: white; font-weight: bold; border-radius: 9999px; padding: 10px 40px; }
        .purple-btn { background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 9999px; padding: 10px 40px; }
        .purple-card { background-color: #313244; border-radius: 12px; padding: 20px; margin: 10px; }
        .preset-title { font-size: 18px; font-weight: bold; color: #cba6f7; }
        .violet-progress progress { background-color: #cba6f7; border-radius: 6px; min-height: 12px; }
        .violet-progress trough { background-color: #313244; border-radius: 6px; min-height: 12px; }
        .console-btn {
            background-color: #313244;
            color: #cdd6f4;
            border-radius: 9999px;
            padding: 8px 20px;
            font-weight: bold;
            border: none;
        }
        .console-btn:hover { background-color: #45475a; }
        .console-btn:checked { background-color: #585b70; }
        """
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # --- STRONY ---
    def init_welcome(self):
        page = Adw.StatusPage()
        page.set_title("Witaj w RatInstall")
        page.set_description("Wybierz aplikacje, środowisko i styl.")
        page.set_icon_name("system-software-install-symbolic")

        btn = Gtk.Button(label="Rozpocznij")
        btn.add_css_class("blue-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda x: self.stack.set_visible_child_name("software"))
        page.set_child(btn)
        self.stack.add_named(page, "welcome")

    def init_soft(self):
        page = Adw.PreferencesPage()
        page.set_title("Aplikacje")
        group = Adw.PreferencesGroup(title="Wybierz programy")
        self.soft_checks = {}
        for item in SOFTWARE_LIST:
            row = Adw.ActionRow(title=item['name'], subtitle=item['pkg'])
            check = Gtk.CheckButton()
            check.set_active(item['checked'])
            check.set_valign(Gtk.Align.CENTER)
            row.add_suffix(check)
            group.add(row)
            self.soft_checks[item['pkg']] = (check, item)
        page.add(group)

        btn = Gtk.Button(label="Dalej")
        btn.add_css_class("blue-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_margin_top(20)
        btn.connect("clicked", lambda x: self.stack.set_visible_child_name("desktop"))

        grp = Adw.PreferencesGroup()
        grp.add(btn)
        page.add(grp)
        self.stack.add_named(page, "software")

    def init_de(self):
        page = Adw.PreferencesPage()
        page.set_title("Środowisko")
        group = Adw.PreferencesGroup(title="Wybierz pulpit")
        self.de_radios = {}
        first_radio = None

        for item in DE_LIST:
            row = Adw.ActionRow(title=item['name'])
            radio = Gtk.CheckButton(group=first_radio)
            if not first_radio:
                first_radio = radio
            radio.set_active(item['checked'])
            radio.set_valign(Gtk.Align.CENTER)
            radio.connect("toggled", self.on_de_toggled, item['id'])

            row.add_suffix(radio)
            row.set_activatable_widget(radio)
            group.add(row)
            self.de_radios[item['id']] = (radio, item)

        page.add(group)

        btn = Gtk.Button(label="Dalej")
        btn.add_css_class("blue-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_margin_top(20)
        btn.connect("clicked", self.go_to_next)

        grp = Adw.PreferencesGroup()
        grp.add(btn)
        page.add(grp)
        self.stack.add_named(page, "desktop")

    def on_de_toggled(self, widget, de_id):
        if widget.get_active():
            self.selected_de = de_id

    def go_to_next(self, btn):
        if self.selected_de == "kde":
            self.stack.set_visible_child_name("kde_presets")
        else:
            self.on_install_clicked(btn)

    def init_kde_presets(self):
        page = Adw.PreferencesPage()
        page.set_title("Styl KDE Plasma")

        group = Adw.PreferencesGroup(title="Wybierz wygląd")
        page.add(group)

        self.preset_radios = {}
        r_group = None

        for preset in KDE_PRESETS:
            card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
            card.add_css_class("purple-card")

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            lbl_t = Gtk.Label(label=preset['name'], xalign=0)
            lbl_t.add_css_class("preset-title")
            lbl_d = Gtk.Label(label=preset['desc'], xalign=0)
            lbl_d.add_css_class("caption")
            vbox.append(lbl_t)
            vbox.append(lbl_d)

            radio = Gtk.CheckButton(group=r_group)
            if not r_group:
                r_group = radio
            radio.set_valign(Gtk.Align.CENTER)

            card.append(vbox)
            # odstęp
            img = Gtk.Image()
            card.append(img)
            img.set_hexpand(True)
            card.append(radio)

            group.add(card)
            self.preset_radios[preset['id']] = radio

        # Domyślnie pierwszy (dock) aktywny
        self.preset_radios["dock"].set_active(True)

        btn_group = Adw.PreferencesGroup()
        page.add(btn_group)

        btn = Gtk.Button(label="Zainstaluj wszystko")
        btn.add_css_class("purple-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_margin_top(20)
        btn.connect("clicked", self.on_install_clicked)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn)
        btn_group.add(btn_box)

        self.stack.add_named(page, "kde_presets")

    def init_progress(self):
        self.page_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.page_progress.set_valign(Gtk.Align.CENTER)
        self.page_progress.set_halign(Gtk.Align.CENTER)

        # Logo (opcjonalne)
        self.prog_logo = Gtk.Image()
        self.prog_logo.set_pixel_size(150)
        path = "/tmp/arch_logo.svg"
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve("https://archlinux.org/static/logos/archlinux-logo-dark-scalable.518881f04ca9.svg", path)
            except:
                pass
        if os.path.exists(path):
            self.prog_logo.set_from_paintable(Gdk.Texture.new_from_file(Gio.File.new_for_path(path)))
        else:
            self.prog_logo.set_from_icon_name("system-software-install-symbolic")

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.add_css_class("violet-progress")
        self.progress_bar.set_size_request(400, 20)

        self.lbl_status = Gtk.Label(label="Czekam...")
        self.lbl_status.add_css_class("title-2")

        # Przycisk do pokazania konsoli
        self.toggle_console_btn = Gtk.ToggleButton(label="Pokaż konsolę")
        self.toggle_console_btn.add_css_class("console-btn")
        self.toggle_console_btn.connect("toggled", self.on_toggle_console)

        # Revealer z TextView
        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_monospace(True)
        self.textview.set_wrap_mode(Gtk.WrapMode.CHAR)
        sw = Gtk.ScrolledWindow()
        sw.set_min_content_height(200)
        sw.set_child(self.textview)
        self.revealer.set_child(sw)

        self.page_progress.append(self.prog_logo)
        self.page_progress.append(self.progress_bar)
        self.page_progress.append(self.lbl_status)
        self.page_progress.append(self.toggle_console_btn)
        self.page_progress.append(self.revealer)

        self.stack.add_named(self.page_progress, "progress")

    def on_toggle_console(self, button):
        active = button.get_active()
        self.revealer.set_reveal_child(active)
        button.set_label("Ukryj konsolę" if active else "Pokaż konsolę")

    def init_finish(self):
        page = Adw.StatusPage()
        page.set_title("Gotowe!")
        page.set_icon_name("emblem-ok-symbolic")

        btn = Gtk.Button(label="Restart")
        btn.add_css_class("purple-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda x: subprocess.run(["systemctl", "reboot"]))

        page.set_child(btn)
        self.stack.add_named(page, "finish")

    def on_install_clicked(self, btn):
        # Zbierz zaznaczone programy
        queue = []
        for pkg, (chk, inf) in self.soft_checks.items():
            if chk.get_active():
                queue.append(inf)

        # Sprawdź, które środowisko wybrane
        de = "none"
        for de_id, (rad, inf) in self.de_radios.items():
            if rad.get_active():
                de = de_id
                break

        # Dla KDE: pobierz preset
        kde_preset = "clean"
        if de == "kde":
            for pid, radio in self.preset_radios.items():
                if radio.get_active():
                    kde_preset = pid
                    break

        self.ask_password(queue, de, kde_preset)

    def ask_password(self, queue, de, kde_preset):
        dialog = Adw.MessageDialog(transient_for=self, heading="Hasło", body="Wymagane uprawnienia administratora.")
        dialog.add_response("cancel", "Anuluj")
        dialog.add_response("ok", "Instaluj")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        entry = Gtk.PasswordEntry()
        entry.set_placeholder_text("Hasło sudo")
        entry.connect("activate", lambda w: dialog.response("ok"))
        box.append(entry)
        dialog.set_extra_child(box)

        def on_response(d, r):
            if r == "ok":
                pwd = entry.get_text()
                d.close()
                self.stack.set_visible_child_name("progress")
                # Czyścimy logi
                self.textview.get_buffer().set_text("")
                # Uruchamiamy wątek
                self.worker = InstallWorker(
                    password=pwd,
                    queue=queue,
                    de_id=de,
                    kde_preset=kde_preset,
                    on_progress=self.update_progress,
                    on_log=self.append_log,
                    on_finish=lambda success: GLib.idle_add(self.install_finished, success)
                )
                self.worker.start()
            else:
                d.close()

        dialog.connect("response", on_response)
        dialog.present()

    def update_progress(self, pct, txt):
        GLib.idle_add(lambda: (self.progress_bar.set_fraction(pct/100), self.lbl_status.set_text(txt)))

    def append_log(self, text):
        GLib.idle_add(self._append_log, text)

    def _append_log(self, text):
        buffer = self.textview.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, text + "\n")
        # Przewiń na dół
        self.textview.scroll_to_iter(buffer.get_end_iter(), 0.0, False, 0, 0)

    def install_finished(self, success):
        if success:
            self.stack.set_visible_child_name("finish")
        else:
            # Można dodać obsługę błędów
            toast = Adw.Toast.new("Instalacja zakończona z błędami – sprawdź logi.")
            self.overlay.add_toast(toast)

class InstallerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.rat.install", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = InstallerWindow(self)
        win.present()

if __name__ == "__main__":
    app = InstallerApp()
    app.run(sys.argv)
