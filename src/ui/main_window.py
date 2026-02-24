import sys
import os
import subprocess
import threading
import urllib.request
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

# ==============================================================================
# 🔧 KONFIGURACJA - EDYTUJ TE LISTY
# ==============================================================================

# Źródła: "flatpak", "aur", "pacman"
SOFTWARE_LIST = [
    # Przeglądarki
    {"name": "Firefox",          "pkg": "org.mozilla.firefox",         "source": "flatpak", "checked": True},
    {"name": "Zen Browser",      "pkg": "io.github.zen_browser.zen",   "source": "flatpak", "checked": False},

    # Narzędzia
    {"name": "Visual Studio Code", "pkg": "com.visualstudio.code",     "source": "flatpak", "checked": True},
    {"name": "Prism Launcher",   "pkg": "org.prismlauncher.PrismLauncher", "source": "flatpak", "checked": False},
    {"name": "Steam",            "pkg": "com.valvesoftware.Steam",     "source": "flatpak", "checked": False},
    {"name": "Discord",          "pkg": "com.discordapp.Discord",      "source": "flatpak", "checked": True},
    {"name": "OBS Studio",       "pkg": "com.obsproject.Studio",       "source": "flatpak", "checked": False},
    {"name": "AnyDesk",          "pkg": "com.anydesk.Anydesk",         "source": "flatpak", "checked": False},

    # WYJĄTEK (AUR)
    {"name": "DaVinci Resolve",  "pkg": "davinci-resolve",             "source": "aur",     "checked": False},
]

# Środowiska graficzne (zostawiamy pacman)
DE_LIST = [
    {"name": "KDE Plasma (Full)", "pkg": "plasma-meta",       "source": "pacman"},
    {"name": "GNOME (Full)",      "pkg": "gnome",             "source": "pacman"},
    {"name": "Cinnamon",          "pkg": "cinnamon",          "source": "pacman"},
    {"name": "i3 Window Manager", "pkg": "i3-wm",             "source": "pacman"},
]

# ==============================================================================
# 🧠 LOGIKA INSTALACJI (BACKEND)
# ==============================================================================

class InstallWorker(threading.Thread):
    def __init__(self, password, queue, on_progress, on_finish):
        super().__init__()
        self.password = password
        self.queue = queue          # Lista pakietów do zainstalowania
        self.on_progress = on_progress
        self.on_finish = on_finish
        self.daemon = True
        # +3 kroki ekstra: Update, Git/Base, Flatpak Setup
        self.total_steps = len(queue) + 3

    def run_cmd(self, cmd_list, use_shell=False):
        """Uruchamia komendę z sudo"""
        if cmd_list[0] == "sudo":
            # Przekazanie hasła do sudo -S
            cmd_str = " ".join(cmd_list).replace("sudo", "sudo -S")
            full_cmd = f"echo '{self.password}' | {cmd_str}"
            use_shell = True
        else:
            full_cmd = cmd_list

        try:
            # Używamy subprocess.run i ignorujemy wyjście (chyba że błąd)
            subprocess.run(
                full_cmd,
                shell=use_shell,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE # Zbieramy błędy w razie czego
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Błąd komendy: {full_cmd}")
            return False

    def setup_flatpak(self):
        """Instaluje flatpak i dodaje repozytorium Flathub"""
        # 1. Instalacja pakietu flatpak przez pacmana
        if not self.run_cmd(["sudo", "pacman", "-S", "flatpak", "--noconfirm", "--needed"]):
            return False

        # 2. Dodanie repozytorium Flathub (system-wide)
        # Nie wymaga sudo jeśli robimy --user, ale dla instalatora systemowego lepiej dać sudo
        # flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
        cmd = ["sudo", "flatpak", "remote-add", "--if-not-exists", "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"]
        return self.run_cmd(cmd)

    def install_pkg(self, pkg_info):
        """Rozdziela instalację na Pacman / Yay / Flatpak"""
        pkg = pkg_info['pkg']
        source = pkg_info.get('source', 'pacman') # Domyślnie pacman

        if source == "flatpak":
            # Instalacja Flatpak (bez potwierdzeń -y)
            # Używamy sudo, żeby instalować systemowo (dla wszystkich użytkowników)
            cmd = ["sudo", "flatpak", "install", "flathub", pkg, "-y"]

        elif source == "aur":
            # Instalacja YAY
            cmd = ["yay", "-S", pkg, "--noconfirm", "--answerdiff", "None", "--answerclean", "None"]

        else:
            # Instalacja PACMAN (domyślna)
            cmd = ["sudo", "pacman", "-S", pkg, "--noconfirm", "--needed"]

        return self.run_cmd(cmd)

    def run(self):
        current_step = 0

        # 1. Update repozytoriów
        self.on_progress(0, "Aktualizacja repozytoriów (Pacman)...")
        self.run_cmd(["sudo", "pacman", "-Sy"])
        current_step += 1

        # 2. Instalacja Git/Base-devel (wymagane do AUR)
        self.on_progress(10, "Przygotowanie AUR (Git, Base-devel)...")
        self.run_cmd(["sudo", "pacman", "-S", "git", "base-devel", "--noconfirm", "--needed"])
        current_step += 1

        # 3. Konfiguracja Flatpak
        self.on_progress(15, "Konfiguracja Flatpak i Flathub...")
        if not self.setup_flatpak():
            print("Nie udało się skonfigurować Flatpaka!")
        current_step += 1

        # 4. Instalacja z kolejki
        success = True
        for item in self.queue:
            percent = int((current_step / self.total_steps) * 100)

            # Ładny opis co się dzieje
            source_name = item.get('source', 'pacman').upper()
            self.on_progress(percent, f"Instalowanie [{source_name}]: {item['name']}...")

            if not self.install_pkg(item):
                print(f"Błąd instalacji: {item['name']}")
                success = False

            current_step += 1

        self.on_progress(100, "Finalizowanie...")
        GLib.idle_add(self.on_finish, success)

# ==============================================================================
# 🎨 INTERFEJS UŻYTKOWNIKA (GUI)
# ==============================================================================

class InstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Arch Setup")
        self.set_default_size(900, 650)
        self.load_css()

        # Przechowywanie stanu
        self.selected_software = []
        self.selected_de = []

        # Główny kontener nawigacji
        self.stack = Adw.ViewStack()

        # Pasek tytułu
        self.header = Adw.HeaderBar()
        self.header.set_show_end_title_buttons(True)
        self.header.set_show_start_title_buttons(False)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.header)
        main_box.append(self.stack)
        self.set_content(main_box)

        # Inicjalizacja stron
        self.init_welcome_page()
        self.init_software_page()
        self.init_de_page()
        self.init_progress_page()
        self.init_finish_page()

    def load_css(self):
        """Style CSS"""
        provider = Gtk.CssProvider()
        css = b"""
        .blue-btn {
            background-color: #3584e4;
            color: white;
            font-weight: bold;
            border-radius: 9999px;
            padding: 10px 40px;
        }
        .blue-btn:hover { background-color: #1c71d8; }

        .purple-btn {
            background-color: #cba6f7;
            color: #1e1e2e;
            font-weight: bold;
            border-radius: 9999px;
            padding: 10px 40px;
        }
        .purple-btn:hover { background-color: #b492e0; }

        .violet-progress progress {
            background-color: #cba6f7;
            border-radius: 6px;
            min-height: 12px;
        }
        .violet-progress trough {
            background-color: #313244;
            border-radius: 6px;
            min-height: 12px;
        }
        """
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def get_arch_logo(self):
        path = "/tmp/arch_logo.svg"
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve("https://archlinux.org/static/logos/archlinux-logo-dark-scalable.518881f04ca9.svg", path)
            except: pass

        if os.path.exists(path):
            return Gdk.Texture.new_from_file(Gio.File.new_for_path(path))
        return None

    # --- STRONA 1: POWITANIE ---
    def init_welcome_page(self):
        page = Adw.StatusPage()
        page.set_title("Witaj w Instalatorze")
        page.set_description("Skonfiguruj swój system Arch Linux krok po kroku.")

        logo = self.get_arch_logo()
        if logo: page.set_paintable(logo)
        else: page.set_icon_name("system-software-install-symbolic")

        btn = Gtk.Button(label="Rozpocznij")
        btn.add_css_class("blue-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda x: self.stack.set_visible_child_name("software"))

        page.set_child(btn)
        self.stack.add_named(page, "welcome")

    # --- STRONA 2: WYBÓR SOFTU ---
    def init_software_page(self):
        page = Adw.PreferencesPage()
        page.set_title("Wybór Oprogramowania")

        group = Adw.PreferencesGroup(title="Aplikacje (Flatpak & AUR)")

        self.soft_checks = {}

        for item in SOFTWARE_LIST:
            # Podpisujemy czy to Flatpak czy AUR
            src_label = item.get('source', 'pacman').upper()
            row = Adw.ActionRow(title=item['name'], subtitle=f"Źródło: {src_label} ({item['pkg']})")

            check = Gtk.CheckButton()
            check.set_active(item['checked'])
            check.set_valign(Gtk.Align.CENTER)

            row.add_suffix(check)
            row.set_activatable_widget(check)

            group.add(row)
            self.soft_checks[item['pkg']] = (check, item)

        page.add(group)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(20)
        btn_box.set_margin_bottom(20)

        btn = Gtk.Button(label="Dalej")
        btn.add_css_class("blue-btn")
        btn.connect("clicked", lambda x: self.stack.set_visible_child_name("desktop"))

        btn_box.append(btn)
        page.add(btn_box)

        self.stack.add_named(page, "software")

    # --- STRONA 3: WYBÓR DE ---
    def init_de_page(self):
        page = Adw.PreferencesPage()
        page.set_title("Środowisko Graficzne")

        group = Adw.PreferencesGroup(title="Środowisko Pulpitu")

        self.de_checks = {}

        for item in DE_LIST:
            row = Adw.ActionRow(title=item['name'])
            check = Gtk.CheckButton()
            check.set_valign(Gtk.Align.CENTER)

            row.add_suffix(check)
            row.set_activatable_widget(check)

            group.add(row)
            self.de_checks[item['pkg']] = (check, item)

        page.add(group)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(20)

        btn = Gtk.Button(label="Zainstaluj")
        btn.add_css_class("blue-btn")
        btn.connect("clicked", self.on_install_clicked)

        btn_box.append(btn)
        page.add(btn_box)

        self.stack.add_named(page, "desktop")

    # --- STRONA 4: PROGRESS ---
    def init_progress_page(self):
        self.page_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.page_progress.set_valign(Gtk.Align.CENTER)
        self.page_progress.set_halign(Gtk.Align.CENTER)
        self.page_progress.set_hexpand(True)
        self.page_progress.set_vexpand(True)

        self.prog_logo = Gtk.Image()
        self.prog_logo.set_pixel_size(150)
        texture = self.get_arch_logo()
        if texture: self.prog_logo.set_paintable(texture)
        else: self.prog_logo.set_icon_name("system-software-install-symbolic")

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.add_css_class("violet-progress")
        self.progress_bar.set_size_request(400, 20)

        self.progress_label = Gtk.Label(label="0%")
        self.progress_label.add_css_class("title-2")

        self.status_text = Gtk.Label(label="Inicjalizacja...")
        self.status_text.add_css_class("caption")

        self.page_progress.append(self.prog_logo)
        self.page_progress.append(self.progress_bar)
        self.page_progress.append(self.progress_label)
        self.page_progress.append(self.status_text)

        self.stack.add_named(self.page_progress, "progress")

    # --- STRONA 5: FINISH ---
    def init_finish_page(self):
        self.page_finish = Adw.StatusPage()
        self.stack.add_named(self.page_finish, "finish")

    # --- LOGIKA ---
    def on_install_clicked(self, btn):
        install_queue = []

        # Soft
        for pkg, (check, info) in self.soft_checks.items():
            if check.get_active():
                install_queue.append(info)

        # DE
        for pkg, (check, info) in self.de_checks.items():
            if check.get_active():
                install_queue.append(info)

        self.ask_password(install_queue)

    def ask_password(self, queue):
        dialog = Adw.MessageDialog(transient_for=self, heading="Autoryzacja", body="Wymagane hasło sudo.")
        dialog.add_response("cancel", "Anuluj")
        dialog.add_response("ok", "Instaluj")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pwd_entry = Gtk.PasswordEntry()
        self.pwd_entry.set_property("placeholder-text", "Hasło")
        self.pwd_entry.connect("activate", lambda w: dialog.response("ok"))
        box.append(self.pwd_entry)
        dialog.set_extra_child(box)

        dialog.connect("response", lambda d, r: self.start_install(d, r, queue))
        dialog.present()

    def start_install(self, dialog, response, queue):
        if response != "ok":
            dialog.close()
            return

        pwd = self.pwd_entry.get_text()
        dialog.close()

        self.stack.set_visible_child_name("progress")

        worker = InstallWorker(pwd, queue, self.update_progress, self.finish_install)
        worker.start()

    def update_progress(self, percent, text):
        def _update():
            self.progress_bar.set_fraction(percent / 100)
            self.progress_label.set_text(f"{percent}%")
            self.status_text.set_text(text)
            return False
        GLib.idle_add(_update)

    def finish_install(self, success):
        self.stack.set_visible_child_name("finish")

        if success:
            self.page_finish.set_title("Instalacja Ukończona")
            self.page_finish.set_icon_name("emblem-ok-symbolic")
            self.page_finish.set_description("Wszystkie pakiety zostały zainstalowane.")

            btn = Gtk.Button(label="Uruchom ponownie")
            btn.add_css_class("purple-btn")
            btn.set_halign(Gtk.Align.CENTER)
            btn.connect("clicked", self.reboot_system)
            self.page_finish.set_child(btn)
        else:
            self.page_finish.set_title("Wystąpił Błąd")
            self.page_finish.set_icon_name("dialog-error-symbolic")
            self.page_finish.set_description("Sprawdź połączenie z internetem.")

            btn = Gtk.Button(label="Zamknij program")
            btn.add_css_class("purple-btn")
            btn.set_halign(Gtk.Align.CENTER)
            btn.connect("clicked", lambda x: self.close())
            self.page_finish.set_child(btn)

    def reboot_system(self, btn):
        subprocess.run(["systemctl", "reboot"])

class InstallerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.arch.wizard", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win: win = InstallerWindow(self)
        win.present()

if __name__ == "__main__":
    app = InstallerApp()
    app.run(sys.argv)
