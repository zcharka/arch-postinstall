import sys
import os
import subprocess
import threading
import shutil
import gi

# --- KONFIGURACJA ŚCIEŻEK DO IMPORTU ---
# Dodajemy folder nadrzędny do ścieżki, aby widzieć moduł 'postinstall'
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Próba importu modułów logiki (gnome.py, plasma.py)
try:
    from postinstall import gnome, plasma
except ImportError as e:
    print(f"⚠️ Ostrzeżenie: Nie można zaimportować modułów logiki ({e}). Używam atrap.")
    class Mock:
        def install_gnome_deps(self, r): pass
        def enable_extensions(self, r): pass
        def setup_appearance(self, r): pass
        def install_plasma_deps(self, r): pass
        def apply_custom_look(self, r): pass
        def apply_layout_preset(self, r): pass
    gnome = Mock()
    plasma = Mock()

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, Pango

# ==============================================================================
# 🔧 LISTA OPROGRAMOWANIA
# ==============================================================================

SOFTWARE_LIST = [
    # --- PRZEGLĄDARKI ---
    {"name": "Firefox",          "pkg": "org.mozilla.firefox",         "source": "flatpak", "checked": True},
    {"name": "Zen Browser",      "pkg": "io.github.zen_browser.zen",   "source": "flatpak", "checked": True},
    {"name": "Discord",          "pkg": "com.discordapp.Discord",      "source": "flatpak", "checked": True},

    # --- NARZĘDZIA ---
    {"name": "Visual Studio Code", "pkg": "com.visualstudio.code",     "source": "flatpak", "checked": True},
    {"name": "GNOME Tweaks",     "pkg": "gnome-tweaks",                "source": "pacman",  "checked": True},
    {"name": "SassC (Themes)",   "pkg": "sassc",                       "source": "pacman",  "checked": True},

    # --- LINEXIN (Petexy) ---
    {"name": "Linexin Repo",     "pkg": "https://github.com/Petexy/linexin-repo", "source": "git_script", "checked": True},
    {"name": "Linexin Center",   "pkg": "https://github.com/Petexy/Linexin-Center", "source": "git_script", "checked": True},

    # --- GAMING ---
    {"name": "Steam",            "pkg": "com.valvesoftware.Steam",     "source": "flatpak", "checked": True},
    {"name": "Lutris",           "pkg": "net.lutris.Lutris",           "source": "flatpak", "checked": False},
    {"name": "Prism Launcher",   "pkg": "org.prismlauncher.PrismLauncher", "source": "flatpak", "checked": True},

    # --- PETEXY INSTALLERS ---
    {"name": "DaVinci Resolve",  "pkg": "https://github.com/Petexy/DaVinci_Installer_For_Linux", "source": "git_script", "checked": False},
    {"name": "Affinity Suite",   "pkg": "https://github.com/Petexy/Affinity_Installer_For_Linux", "source": "git_script", "checked": False},
]

DE_LIST = [
    {"name": "KDE Plasma 6",      "pkg": "plasma-meta",       "id": "kde"},
    {"name": "GNOME",             "pkg": "gnome",             "id": "gnome"},
    {"name": "Hyprland",          "pkg": "hyprland",          "id": "hypr"},
]

# ==============================================================================
# 🧠 BACKEND (WORKER)
# ==============================================================================

class InstallWorker(threading.Thread):
    def __init__(self, password, queue, preset, de_id, on_progress, on_log, on_finish):
        super().__init__()
        self.password = password
        self.queue = queue
        self.preset = preset
        self.de_id = de_id
        self.on_progress = on_progress
        self.on_log = on_log
        self.on_finish = on_finish
        self.daemon = True
        self.total_steps = len(queue) + 8

    def run_cmd(self, cmd_input, use_shell=False, cwd=None):
        """Uruchamia komendę i loguje wyjście do konsoli GUI."""
        full_cmd = cmd_input

        # Obsługa sudo i konwersji listy na string
        if isinstance(cmd_input, list):
            if cmd_input[0] == "sudo":
                cmd_str = " ".join(cmd_input).replace("sudo", "sudo -S")
                full_cmd = f"echo '{self.password}' | {cmd_str}"
                use_shell = True
            elif use_shell:
                full_cmd = " ".join(cmd_input)
        elif isinstance(cmd_input, str):
            if "sudo" in cmd_input and "echo" not in cmd_input:
                 full_cmd = f"echo '{self.password}' | sudo -S {cmd_input.replace('sudo', '')}"
                 use_shell = True

        # Logowanie (ukrywamy hasło)
        log_msg = str(full_cmd).replace(self.password, "****")
        self.on_log(f"\n➜ {log_msg}\n")

        try:
            process = subprocess.Popen(
                full_cmd,
                shell=use_shell,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1 # Line buffered
            )

            # Czytanie wyjścia w czasie rzeczywistym
            for line in process.stdout:
                self.on_log(line)

            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.on_log(f"❌ Wyjątek procesu: {e}\n")
            return False

    def install_git_script(self, repo_url):
        repo_name = repo_url.split("/")[-1]
        tmp_dir = f"/tmp/{repo_name}"

        # 1. Czyszczenie
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)

        # 2. Klonowanie
        self.on_log(f"Klonowanie {repo_name}...\n")
        if not self.run_cmd(["git", "clone", repo_url, tmp_dir]):
            return False

        # 3. Szukanie skryptu instalacyjnego
        script = next((s for s in ["install.sh", "setup.sh", "main.sh", "installer.sh"] if os.path.exists(f"{tmp_dir}/{s}")), None)
        if not script:
            self.on_log("❌ Nie znaleziono pliku install.sh/setup.sh!\n")
            return False

        # 4. Nadanie uprawnień i uruchomienie (z sudo)
        self.run_cmd(["chmod", "+x", f"{tmp_dir}/{script}"])
        self.on_log(f"🚀 Uruchamianie {script}...\n")

        # Uruchamiamy wewnątrz folderu (cwd)
        return self.run_cmd(f"echo '{self.password}' | sudo -S ./{script}", cwd=tmp_dir, use_shell=True)

    def install_pkg_string(self, source, pkg_name):
        if source == "flatpak":
            return self.run_cmd(["flatpak", "install", "flathub", pkg_name, "-y"])
        elif source == "aur":
            # Yay z opcjami bez pytania
            return self.run_cmd(["yay", "-S", pkg_name, "--noconfirm", "--answerdiff=None", "--answerclean=None"])
        elif source == "git_script":
            return self.install_git_script(pkg_name)
        else:
            return self.run_cmd(["sudo", "pacman", "-S", pkg_name, "--noconfirm", "--needed"])

    def configure_preset(self):
        # Wywołanie logiki z zaimportowanych modułów
        if self.de_id == "gnome":
            self.on_log("\n🔵 Konfiguracja GNOME (Extensions & Colloid)...\n")
            gnome.install_gnome_deps(self.run_cmd)
            gnome.setup_appearance(self.run_cmd) # To instaluje motyw i tapetę
            gnome.enable_extensions(self.run_cmd) # To aktywuje wtyczki

        elif self.de_id == "kde":
            self.on_log("\n🔵 Konfiguracja KDE Plasma...\n")
            if self.preset != "clean":
                plasma.install_plasma_deps(self.run_cmd)
                plasma.apply_custom_look(self.run_cmd)
                if self.preset == "dock":
                    plasma.apply_layout_preset(self.run_cmd)

    def run(self):
        self.on_log("=== START INSTALACJI ===\n")

        # 1. Update systemu
        self.run_cmd(["sudo", "pacman", "-Sy"])

        # 2. Sprawdzenie YAY (jeśli brak)
        if not shutil.which("yay"):
             self.on_log("⚠️ Brak yay - instalowanie...\n")
             self.run_cmd("sudo pacman -S --needed git base-devel --noconfirm")
             self.run_cmd("git clone https://aur.archlinux.org/yay.git /tmp/yay && cd /tmp/yay && makepkg -si --noconfirm")

        # 3. Dodanie repo Flatpak
        self.run_cmd(["flatpak", "remote-add", "--if-not-exists", "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"])

        # 4. Instalacja z kolejki
        step = 0
        for item in self.queue:
            perc = int((step / self.total_steps) * 80) + 10
            self.on_progress(perc, f"Instalacja: {item['name']}")
            self.on_log(f"\n📦 Instaluję: {item['name']} ({item['source']})\n")

            if self.install_pkg_string(item['source'], item['pkg']):
                self.on_log("✅ Sukces\n")
            else:
                self.on_log("⚠️ Błąd instalacji\n")
            step += 1

        # 5. Presety
        self.on_log("\n🎨 Konfiguracja Wyglądu...\n")
        self.configure_preset()

        # 6. Koniec
        self.on_progress(100, "Gotowe!")
        self.on_log("\n=== ZAKOŃCZONO. Zalecany restart systemu. ===\n")
        GLib.idle_add(self.on_finish, True)

# ==============================================================================
# 🎨 GUI (OKNO APLIKACJI)
# ==============================================================================

class InstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Arch Setup")
        self.set_default_size(950, 750)
        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self.load_css()

        self.stack = Adw.ViewStack()
        self.header = Adw.HeaderBar()
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.append(self.header); self.box.append(self.stack)
        self.set_content(self.box)

        self.soft_checks = {}
        self.de_radios = {}
        self.preset_radios = {}
        self.is_kde_selected = False

        self.init_pages()

    def load_css(self):
        p = Gtk.CssProvider()
        p.load_from_data(b"""
        .console-view { background-color: #1e1e2e; color: #a6e3a1; font-family: 'Monospace'; padding: 10px; }
        .blue-btn { background-color: #3584e4; color: white; border-radius: 20px; padding: 5px 20px; font-weight: bold; }
        .purple-btn { background-color: #cba6f7; color: #111; border-radius: 20px; font-weight: bold; }
        .purple-card { background-color: #313244; border-radius: 12px; padding: 15px; margin: 5px; }
        .preset-title { font-size: 16px; font-weight: bold; color: #cba6f7; }
        .caption { font-size: 12px; color: #ccc; }
        """)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), p, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def init_pages(self):
        # --- 1. Welcome ---
        p1 = Adw.StatusPage(title="Arch Post-Install", icon_name="system-software-install-symbolic")
        b1 = Gtk.Button(label="Rozpocznij", css_classes=["blue-btn"], halign=Gtk.Align.CENTER)
        b1.connect("clicked", lambda x: self.stack.set_visible_child_name("software"))
        p1.set_child(b1)
        self.stack.add_named(p1, "welcome")

        # --- 2. Software ---
        p2 = Adw.PreferencesPage(title="Oprogramowanie")
        g2 = Adw.PreferencesGroup()
        for i in SOFTWARE_LIST:
            src = "Repo"
            if i['source'] == "flatpak": src = "Flatpak"
            elif i['source'] == "git_script": src = "GitHub"

            row = Adw.ActionRow(title=i['name'], subtitle=f"{i['pkg']} ({src})")
            chk = Gtk.CheckButton(active=i['checked'], valign=Gtk.Align.CENTER)
            row.add_suffix(chk)
            g2.add(row)
            self.soft_checks[i['pkg']] = (chk, i)
        p2.add(g2)
        b2 = Gtk.Button(label="Dalej", css_classes=["blue-btn"], halign=Gtk.Align.CENTER)
        b2.connect("clicked", lambda x: self.stack.set_visible_child_name("desktop"))
        p2.add(Adw.PreferencesGroup(header_suffix=b2))
        self.stack.add_named(p2, "software")

        # --- 3. Desktop Environment ---
        p3 = Adw.PreferencesPage(title="Środowisko")
        g3 = Adw.PreferencesGroup()
        rad_g = None
        for i in DE_LIST:
            rad = Gtk.CheckButton(group=rad_g, valign=Gtk.Align.CENTER)
            if not rad_g: rad_g = rad
            rad.connect("toggled", self.on_de, i['id'])
            row = Adw.ActionRow(title=i['name'])
            row.add_suffix(rad)
            g3.add(row)
            self.de_radios[i['id']] = (rad, i)
        p3.add(g3)
        b3 = Gtk.Button(label="Dalej", css_classes=["blue-btn"], halign=Gtk.Align.CENTER)
        b3.connect("clicked", self.go_preset)
        p3.add(Adw.PreferencesGroup(header_suffix=b3))
        self.stack.add_named(p3, "desktop")

        # --- 4. Presets (Style) ---
        p4 = Adw.PreferencesPage(title="Wygląd")
        g4 = Adw.PreferencesGroup()
        r_grp = None

        def add_card(t, d, id_n):
            nonlocal r_grp
            c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, css_classes=["purple-card"])
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            v.append(Gtk.Label(label=t, xalign=0, css_classes=["preset-title"]))
            v.append(Gtk.Label(label=d, xalign=0, css_classes=["caption"]))
            rad = Gtk.CheckButton(group=r_grp, valign=Gtk.Align.CENTER)
            if not r_grp: r_grp = rad
            c.append(v); c.append(Gtk.Image(hexpand=True)); c.append(rad)
            g4.add(c)
            self.preset_radios[id_n] = rad
            if id_n == "dock": rad.set_active(True)

        add_card("✨ Layan / Colloid", "Motyw, Dock, Blur, Ikony", "dock")
        add_card("🧹 Czysty System", "Brak modyfikacji wyglądu", "clean")

        p4.add(g4)
        b4 = Gtk.Button(label="Instaluj", css_classes=["purple-btn"], halign=Gtk.Align.CENTER)
        b4.connect("clicked", self.start_install)
        p4.add(Adw.PreferencesGroup(header_suffix=b4))
        self.stack.add_named(p4, "presets")

        # --- 5. Progress ---
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=20, margin_bottom=20, margin_start=20, margin_end=20)
        self.pbar = Gtk.ProgressBar(show_text=True)
        self.lbl = Gtk.Label(label="Oczekiwanie...", css_classes=["title-2"])

        # Konsola
        exp = Gtk.Expander(label="Pokaż konsolę", expanded=True, vexpand=True)
        sw = Gtk.ScrolledWindow(min_content_height=300)
        self.tv = Gtk.TextView(editable=False, cursor_visible=False, css_classes=["console-view"])
        self.buf = self.tv.get_buffer()
        sw.set_child(self.tv)
        exp.set_child(sw)

        box.append(self.pbar); box.append(self.lbl); box.append(exp)
        self.stack.add_named(box, "progress")

        # --- 6. Finish ---
        p6 = Adw.StatusPage(title="Zakończono!", icon_name="emblem-ok-symbolic")
        b6 = Gtk.Button(label="Restart", css_classes=["purple-btn"], halign=Gtk.Align.CENTER)
        b6.connect("clicked", lambda x: subprocess.run(["reboot"]))
        p6.set_child(b6)
        self.stack.add_named(p6, "finish")

    def on_de(self, w, id):
        if w.get_active(): self.is_kde_selected = (id == "kde")

    def go_preset(self, b):
        # Jeśli KDE lub GNOME - idź do presetów
        self.stack.set_visible_child_name("presets")

    def start_install(self, b):
        q = [i for pkg, (chk, i) in self.soft_checks.items() if chk.get_active()]

        de_id = "gnome" # Domyślnie
        for pid, (rad, i) in self.de_radios.items():
            if rad.get_active(): de_id = pid

        preset = "clean"
        if "dock" in self.preset_radios and self.preset_radios["dock"].get_active(): preset = "dock"

        self.ask_pass(q, preset, de_id)

    def ask_pass(self, q, preset, de_id):
        d = Adw.MessageDialog(transient_for=self, heading="Hasło sudo")
        d.add_response("ok", "Start")
        e = Gtk.PasswordEntry()
        d.set_extra_child(e)

        def on_response(d, r):
            if r == "ok":
                pwd = e.get_text()
                d.close()
                self.stack.set_visible_child_name("progress")
                InstallWorker(pwd, q, preset, de_id, self.upd, self.log, lambda x: self.stack.set_visible_child_name("finish")).start()
            else:
                d.close()

        d.connect("response", on_response)
        d.present()

    def upd(self, pct, txt):
        GLib.idle_add(lambda: (self.pbar.set_fraction(pct/100), self.lbl.set_text(txt)))

    def log(self, txt):
        def _l():
            self.buf.insert(self.buf.get_end_iter(), txt)
            # Autoscroll
            adj = self.tv.get_parent().get_vadjustment()
            adj.set_value(adj.get_upper())
        GLib.idle_add(_l)

class App(Adw.Application):
    def __init__(self): super().__init__(application_id="pl.arch.setup", flags=Gio.ApplicationFlags.FLAGS_NONE)
    def do_activate(self):
        win = self.props.active_window
        if not win: win = InstallerWindow(self)
        win.present()

if __name__ == "__main__":
    App().run(sys.argv)
