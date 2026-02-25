import sys
import os
import subprocess
import threading
import shutil
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, Pango

# ==============================================================================
# 🔧 KONFIGURACJA OPROGRAMOWANIA
# ==============================================================================

SOFTWARE_LIST = [
    # --- PRZEGLĄDARKI I KOMUNIKACJA ---
    {"name": "Firefox",          "pkg": "org.mozilla.firefox",         "source": "flatpak", "checked": True},
    {"name": "Zen Browser",      "pkg": "io.github.zen_browser.zen",   "source": "flatpak", "checked": True},
    {"name": "Discord",          "pkg": "com.discordapp.Discord",      "source": "flatpak", "checked": True},

    # --- NARZĘDZIA SYSTEMOWE ---
    {"name": "Visual Studio Code", "pkg": "com.visualstudio.code",     "source": "flatpak", "checked": True},
    {"name": "GNOME Extensions", "pkg": "org.gnome.Extensions",        "source": "flatpak", "checked": True},
    {"name": "GNOME Tweaks",     "pkg": "gnome-tweaks",                "source": "pacman",  "checked": True},

    # --- LINEXIN (Petexy) ---
    {"name": "Linexin Repo",     "pkg": "https://github.com/Petexy/linexin-repo", "source": "git_script", "checked": True},
    {"name": "Linexin Center",   "pkg": "https://github.com/Petexy/Linexin-Center", "source": "git_script", "checked": True},

    # --- GAMING & MEDIA ---
    {"name": "Steam",            "pkg": "com.valvesoftware.Steam",     "source": "flatpak", "checked": True},
    {"name": "Lutris",           "pkg": "net.lutris.Lutris",           "source": "flatpak", "checked": False},
    {"name": "Prism Launcher",   "pkg": "org.prismlauncher.PrismLauncher", "source": "flatpak", "checked": True},

    # --- INSTALATORY Z GITHUB (Petexy) ---
    {"name": "DaVinci Resolve (Petexy)", "pkg": "https://github.com/Petexy/DaVinci_Installer_For_Linux", "source": "git_script", "checked": False},
    {"name": "Affinity Suite (Petexy)",  "pkg": "https://github.com/Petexy/Affinity_Installer_For_Linux", "source": "git_script", "checked": False},
]

DE_LIST = [
    {"name": "KDE Plasma 6",      "pkg": "plasma-meta",       "id": "kde"},
    {"name": "GNOME",             "pkg": "gnome",             "id": "gnome"},
    {"name": "Hyprland",          "pkg": "hyprland",          "id": "hypr"},
    {"name": "Cosmic",          "pkg": "cosmic",          "id": "cosmic"},
]

# ==============================================================================
# 🧠 BACKEND (INSTALATOR)
# ==============================================================================

class InstallWorker(threading.Thread):
    def __init__(self, password, queue, preset, on_progress, on_log, on_finish):
        super().__init__()
        self.password = password
        self.queue = queue
        self.preset = preset
        self.on_progress = on_progress
        self.on_log = on_log  # Callback do logowania tekstu
        self.on_finish = on_finish
        self.daemon = True
        self.total_steps = len(queue) + 6

    def run_cmd(self, cmd_list, use_shell=False, cwd=None):
        """
        Uruchamia komendę i przesyła wyjście (stdout/stderr) do konsoli w czasie rzeczywistym.
        """
        # Obsługa sudo
        if cmd_list[0] == "sudo":
            cmd_str = " ".join(cmd_list).replace("sudo", "sudo -S")
            full_cmd = f"echo '{self.password}' | {cmd_str}"
            use_shell = True
        else:
            full_cmd = cmd_list
            # Jeśli lista, łączymy dla shell=True (łatwiejsze logowanie)
            if isinstance(full_cmd, list):
                full_cmd = " ".join(full_cmd)
                use_shell = True

        self.on_log(f"\n➜ Wykonuję: {full_cmd}\n")

        try:
            # Używamy Popen, aby czytać wyjście na żywo
            process = subprocess.Popen(
                full_cmd,
                shell=use_shell,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Łączymy błędy z normalnym wyjściem
                text=True,
                bufsize=1 # Line buffered
            )

            # Czytanie linijka po linijce
            for line in process.stdout:
                self.on_log(line)

            process.wait()

            if process.returncode != 0:
                self.on_log(f"\n❌ Błąd (kod {process.returncode})\n")
                return False

            return True

        except Exception as e:
            self.on_log(f"\n❌ Krytyczny błąd procesu: {e}\n")
            return False

    def install_git_script(self, repo_url):
        repo_name = repo_url.split("/")[-1]
        tmp_dir = f"/tmp/{repo_name}"

        self.on_log(f"--- Instalator GitHub: {repo_name} ---\n")

        if os.path.exists(tmp_dir):
            self.on_log(f"Czyszczenie starego folderu: {tmp_dir}\n")
            shutil.rmtree(tmp_dir, ignore_errors=True)

        self.on_log(f"Klonowanie {repo_url}...\n")
        # Tu używamy run_cmd, więc logi z gita polecą do konsoli
        if not self.run_cmd(["git", "clone", repo_url, tmp_dir]):
            return False

        script_files = ["install.sh", "setup.sh", "main.sh", "installer.sh"]
        script_to_run = None

        for s in script_files:
            if os.path.exists(f"{tmp_dir}/{s}"):
                script_to_run = s
                break

        if not script_to_run:
            self.on_log("❌ Nie znaleziono skryptu instalacyjnego!\n")
            return False

        self.on_log(f"Uruchamianie skryptu: {script_to_run}...\n")
        self.run_cmd(["chmod", "+x", f"{tmp_dir}/{script_to_run}"])

        # Uruchomienie skryptu (run_cmd obsłuży sudo i logi)
        cmd = ["sudo", f"./{script_to_run}"]
        return self.run_cmd(cmd, cwd=tmp_dir)

    def install_pkg_string(self, source, pkg_name):
        if source == "flatpak":
            return self.run_cmd(["sudo", "flatpak", "install", "flathub", pkg_name, "-y"])
        elif source == "aur":
            # Yay wymaga specyficznych flag, żeby nie pytać użytkownika
            return self.run_cmd(["yay", "-S", pkg_name, "--noconfirm", "--answerdiff", "None", "--answerclean", "None"])
        elif source == "git_script":
            return self.install_git_script(pkg_name)
        else:
            return self.run_cmd(["sudo", "pacman", "-S", pkg_name, "--noconfirm", "--needed"])

    def configure_preset(self):
        # Placeholder na importy z gnome.py / plasma.py
        pass

    def run(self):
        current_step = 0
        self.on_log("--- ROZPOCZĘCIE INSTALACJI ---\n")

        self.on_progress(5, "Aktualizacja systemu...")
        self.run_cmd(["sudo", "pacman", "-Sy"])
        self.run_cmd(["sudo", "pacman", "-S", "git", "base-devel", "flatpak", "wget", "--noconfirm", "--needed"])

        self.on_progress(10, "Konfiguracja Flatpak...")
        cmd = ["sudo", "flatpak", "remote-add", "--if-not-exists", "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"]
        self.run_cmd(cmd)

        for item in self.queue:
            percent = int((current_step / self.total_steps) * 80) + 10
            self.on_progress(percent, f"Instalacja: {item['name']}...")
            self.on_log(f"\n--- Instalowanie pakietu: {item['name']} ---\n")

            success = self.install_pkg_string(item.get('source', 'pacman'), item['pkg'])
            if success:
                self.on_log("✅ Sukces.\n")
            else:
                self.on_log("⚠️ Ostrzeżenie: Coś poszło nie tak.\n")

            current_step += 1

        if self.preset != "clean":
            self.on_log("\n--- Konfiguracja Presetu ---\n")
            self.configure_preset()

        self.on_progress(100, "Finalizowanie...")
        self.on_log("\n--- ZAKOŃCZONO ---\n")
        GLib.idle_add(self.on_finish, True)

# ==============================================================================
# 🎨 GUI
# ==============================================================================

class InstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Arch Setup")
        self.set_default_size(950, 750) # Zwiększyłem lekko wysokość

        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self.load_css()

        self.selected_preset = "clean"
        self.is_kde_selected = False

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
        self.init_presets()
        self.init_progress()
        self.init_finish()

    def load_css(self):
        provider = Gtk.CssProvider()
        # Dodano klasę .console-view
        css = b"""
        .blue-btn { background-color: #3584e4; color: white; font-weight: bold; border-radius: 9999px; padding: 10px 40px; }
        .purple-btn { background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 9999px; padding: 10px 40px; }
        .purple-card { background-color: #313244; border-radius: 12px; padding: 20px; margin: 10px; }
        .preset-title { font-size: 18px; font-weight: bold; color: #cba6f7; }
        .violet-progress progress { background-color: #cba6f7; border-radius: 6px; min-height: 12px; }
        .violet-progress trough { background-color: #313244; border-radius: 6px; min-height: 12px; }

        .console-view {
            background-color: #11111b;
            color: #a6e3a1;
            font-family: 'JetBrains Mono', 'Monospace';
            font-size: 11px;
            padding: 10px;
        }
        """
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # --- STRONY ---

    def init_welcome(self):
        page = Adw.StatusPage()
        page.set_title("Witaj w Instalatorze")
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
            src_label = " (Flatpak)" if item['source'] == "flatpak" else " (Repo)"
            if item['source'] == "git_script": src_label = " (Instalator GitHub)"
            row = Adw.ActionRow(title=item['name'], subtitle=item['pkg'] + src_label)
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
        grp = Adw.PreferencesGroup(); grp.add(btn); page.add(grp)
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
            if not first_radio: first_radio = radio
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
        btn.connect("clicked", self.go_to_presets_or_install)
        grp = Adw.PreferencesGroup(); grp.add(btn); page.add(grp)
        self.stack.add_named(page, "desktop")

    def on_de_toggled(self, widget, de_id):
        if widget.get_active() and de_id == "kde": self.is_kde_selected = True
        elif widget.get_active(): self.is_kde_selected = False

    def go_to_presets_or_install(self, btn):
        if self.is_kde_selected: self.stack.set_visible_child_name("presets")
        else: self.on_install_clicked(btn)

    def init_presets(self):
        page = Adw.PreferencesPage()
        page.set_title("Styl KDE Plasma")
        group = Adw.PreferencesGroup(title="Wybierz wygląd")
        page.add(group)
        self.preset_radios = {}
        r_group = None
        p1 = self.create_preset_card("✨ Layan Dock", "Dock, Blur, Rounded Corners.", "dock", r_group)
        r_group = p1[0]; group.add(p1[1]); self.preset_radios["dock"] = p1[0]
        p3 = self.create_preset_card("🧹 Czysta Plasma", "Domyślny wygląd.", "clean", r_group)
        group.add(p3[1]); self.preset_radios["clean"] = p3[0]
        self.preset_radios["dock"].set_active(True)
        btn = Gtk.Button(label="Zainstaluj wszystko")
        btn.add_css_class("purple-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_margin_top(20)
        btn.connect("clicked", self.on_install_clicked)
        grp = Adw.PreferencesGroup(); grp.add(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.CENTER).append(btn) or btn)
        grp.add(btn)
        page.add(grp)
        self.stack.add_named(page, "presets")

    def create_preset_card(self, title, desc, id_name, group):
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        card.add_css_class("purple-card")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        vbox.append(Gtk.Label(label=title, xalign=0, css_classes=["preset-title"]))
        vbox.append(Gtk.Label(label=desc, xalign=0, css_classes=["caption"]))
        radio = Gtk.CheckButton(group=group)
        radio.set_valign(Gtk.Align.CENTER)
        card.append(vbox)
        img = Gtk.Image(); card.append(img); img.set_hexpand(True)
        card.append(radio)
        return (radio, card)

    # --- PROGRESS Z KONSOLĄ ---
    def init_progress(self):
        self.page_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.page_progress.set_valign(Gtk.Align.FILL) # FILL żeby zająć miejsce
        self.page_progress.set_halign(Gtk.Align.FILL)
        self.page_progress.set_margin_top(50)
        self.page_progress.set_margin_bottom(50)
        self.page_progress.set_margin_start(50)
        self.page_progress.set_margin_end(50)

        # 1. Górna część: Pasek postępu i status
        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        top_box.set_valign(Gtk.Align.CENTER)
        top_box.set_halign(Gtk.Align.CENTER)

        self.progress_bar = Gtk.ProgressBar(css_classes=["violet-progress"], width_request=400)
        self.lbl_status = Gtk.Label(label="Inicjalizacja...", css_classes=["title-2"])

        top_box.append(self.progress_bar)
        top_box.append(self.lbl_status)
        self.page_progress.append(top_box)

        # 2. Dolna część: Expander z konsolą
        self.expander = Gtk.Expander(label="Pokaż konsolę")
        self.expander.set_vexpand(True) # Żeby zajmował resztę miejsca

        # Okno przewijane
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(300)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        # Widok tekstowy (Logi)
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.add_css_class("console-view")

        # Buffer do tekstu
        self.log_buffer = self.log_view.get_buffer()

        scrolled.set_child(self.log_view)
        self.expander.set_child(scrolled)

        self.page_progress.append(self.expander)

        self.stack.add_named(self.page_progress, "progress")

    def init_finish(self):
        page = Adw.StatusPage(title="Gotowe!", icon_name="emblem-ok-symbolic")
        btn = Gtk.Button(label="Restart", css_classes=["purple-btn"], halign=Gtk.Align.CENTER)
        btn.connect("clicked", lambda x: subprocess.run(["systemctl", "reboot"]))
        page.set_child(btn)
        self.stack.add_named(page, "finish")

    def on_install_clicked(self, btn):
        queue = []
        for pkg, (chk, inf) in self.soft_checks.items():
            if chk.get_active(): queue.append(inf)
        for pid, (rad, inf) in self.de_radios.items():
            if rad.get_active(): queue.append(inf)
        preset = "dock" if self.is_kde_selected and self.preset_radios["dock"].get_active() else "clean"
        self.ask_password(queue, preset)

    def ask_password(self, queue, preset):
        dialog = Adw.MessageDialog(transient_for=self, heading="Hasło", body="Wymagane sudo.")
        dialog.add_response("ok", "Instaluj")
        entry = Gtk.PasswordEntry()
        entry.connect("activate", lambda w: dialog.response("ok"))
        dialog.set_extra_child(entry)

        def on_res(d, r):
            if r == "ok":
                pwd = entry.get_text()
                d.close()
                self.stack.set_visible_child_name("progress")
                # Przekazujemy self.append_log jako callback
                InstallWorker(pwd, queue, preset, self.update_prog, self.append_log, lambda x: self.stack.set_visible_child_name("finish")).start()
            else:
                d.close()

        dialog.connect("response", on_res)
        dialog.present()

    def update_prog(self, pct, txt):
        GLib.idle_add(lambda: (self.progress_bar.set_fraction(pct/100), self.lbl_status.set_text(txt)))

    def append_log(self, text):
        """Dodaje tekst do konsoli w sposób bezpieczny dla wątków"""
        def _update():
            end_iter = self.log_buffer.get_end_iter()
            self.log_buffer.insert(end_iter, text)
            # Autoscroll
            adj = self.log_view.get_parent().get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())
            return False
        GLib.idle_add(_update)

class InstallerApp(Adw.Application):
    def __init__(self): super().__init__(application_id="com.arch.setup", flags=Gio.ApplicationFlags.FLAGS_NONE)
    def do_activate(self):
        win = self.props.active_window
        if not win: win = InstallerWindow(self)
        win.present()

if __name__ == "__main__":
    app = InstallerApp()
    app.run(sys.argv)
