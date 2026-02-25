import sys
import os
import subprocess
import threading
import urllib.request
import time
import shutil
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

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
]

# ==============================================================================
# 🧠 BACKEND (INSTALATOR)
# ==============================================================================

class InstallWorker(threading.Thread):
    def __init__(self, password, queue, preset, on_progress, on_finish):
        super().__init__()
        self.password = password
        self.queue = queue
        self.preset = preset
        self.on_progress = on_progress
        self.on_finish = on_finish
        self.daemon = True
        self.total_steps = len(queue) + 6

    def run_cmd(self, cmd_list, use_shell=False):
        # Obsługa sudo z hasłem
        if cmd_list[0] == "sudo":
            cmd_str = " ".join(cmd_list).replace("sudo", "sudo -S")
            full_cmd = f"echo '{self.password}' | {cmd_str}"
            use_shell = True
        else:
            full_cmd = cmd_list

        try:
            # Uruchamiamy proces
            subprocess.run(full_cmd, shell=use_shell, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Błąd komendy: {full_cmd} -> {e}")
            return False

    def install_git_script(self, repo_url):
        """
        Klonuje repozytorium i uruchamia install.sh / setup.sh
        """
        repo_name = repo_url.split("/")[-1]
        tmp_dir = f"/tmp/{repo_name}"

        # 1. Czyszczenie starego folderu
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)

        # 2. Klonowanie
        if not self.run_cmd(["git", "clone", repo_url, tmp_dir]):
            return False

        # 3. Szukanie skryptu instalacyjnego
        script_files = ["install.sh", "setup.sh", "main.sh", "installer.sh"]
        script_to_run = None

        for s in script_files:
            if os.path.exists(f"{tmp_dir}/{s}"):
                script_to_run = s
                break

        if not script_to_run:
            print(f"Nie znaleziono skryptu instalacyjnego w {repo_name}")
            return False

        # 4. Nadanie uprawnień i uruchomienie
        # Ważne: Petexy skrypty często wymagają roota, więc używamy sudo
        self.run_cmd(["chmod", "+x", f"{tmp_dir}/{script_to_run}"])

        # Uruchamiamy skrypt wewnątrz folderu (cwd)
        cmd = f"echo '{self.password}' | sudo -S ./{script_to_run}"
        try:
            subprocess.run(cmd, shell=True, check=True, cwd=tmp_dir)
            return True
        except Exception as e:
            print(f"Błąd instalacji {repo_name}: {e}")
            return False

    def install_pkg_string(self, source, pkg_name):
        if source == "flatpak":
            return self.run_cmd(["sudo", "flatpak", "install", "flathub", pkg_name, "-y"])
        elif source == "aur":
            return self.run_cmd(["yay", "-S", pkg_name, "--noconfirm", "--answerdiff", "None", "--answerclean", "None"])
        elif source == "git_script":
            return self.install_git_script(pkg_name) # pkg_name to tutaj URL
        else:
            return self.run_cmd(["sudo", "pacman", "-S", pkg_name, "--noconfirm", "--needed"])

    def configure_preset(self):
        # Tutaj wywołujesz funkcje z plasma.py / gnome.py w zależności od wyboru
        # Ta część kodu zależy od tego, jak importujesz te moduły w main_window
        pass

    def run(self):
        current_step = 0

        self.on_progress(5, "Aktualizacja systemu...")
        self.run_cmd(["sudo", "pacman", "-Sy"])

        # Upewniamy się, że git jest zainstalowany
        self.run_cmd(["sudo", "pacman", "-S", "git", "base-devel", "flatpak", "wget", "--noconfirm", "--needed"])

        cmd = ["sudo", "flatpak", "remote-add", "--if-not-exists", "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"]
        self.run_cmd(cmd)

        for item in self.queue:
            percent = int((current_step / self.total_steps) * 80) + 10
            self.on_progress(percent, f"Instalacja: {item['name']}...")
            self.install_pkg_string(item.get('source', 'pacman'), item['pkg'])
            current_step += 1

        if self.preset != "clean":
            self.configure_preset() # Tu powinna być logika importu (np. z gnome.py)

        self.on_progress(100, "Finalizowanie...")
        GLib.idle_add(self.on_finish, True)

# ==============================================================================
# 🎨 GUI
# ==============================================================================

class InstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Arch Setup")
        self.set_default_size(950, 700)

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
        self.init_presets() # Zakładam, że ta metoda jest zdefiniowana tak jak wcześniej
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
        """
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # --- STRONY (Welcome, Soft, DE, Presets, Progress, Finish) ---
    # Te metody są identyczne jak w poprzednich wersjach,
    # skopiuj je z poprzedniego main_window.py jeśli ich tu brakuje.
    # Wklejam kluczową metodę init_soft z nową listą:

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
            # Dodajemy informację o źródle do podtytułu
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

    # (Tu wklej resztę metod: init_de, init_presets, create_preset_card, init_progress, init_finish, on_install_clicked, ask_password, update_prog)
    # Są one takie same jak w poprzednich krokach, ale ważne by InstallWorker był zaktualizowany (ten powyżej).

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

        # Karty presetów (skrócone dla czytelności)
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

    def init_progress(self):
        self.page_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30, valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
        self.progress_bar = Gtk.ProgressBar(css_classes=["violet-progress"], width_request=400)
        self.lbl_status = Gtk.Label(label="Czekam...", css_classes=["title-2"])
        self.page_progress.append(self.progress_bar)
        self.page_progress.append(self.lbl_status)
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
                pwd = entry.get_text(); d.close(); self.stack.set_visible_child_name("progress")
                InstallWorker(pwd, queue, preset, self.update_prog, lambda x: self.stack.set_visible_child_name("finish")).start()
            else: d.close()
        dialog.connect("response", on_res)
        dialog.present()

    def update_prog(self, pct, txt):
        GLib.idle_add(lambda: (self.progress_bar.set_fraction(pct/100), self.lbl_status.set_text(txt)))

class InstallerApp(Adw.Application):
    def __init__(self): super().__init__(application_id="com.arch.setup", flags=Gio.ApplicationFlags.FLAGS_NONE)
    def do_activate(self):
        win = self.props.active_window
        if not win: win = InstallerWindow(self)
        win.present()

if __name__ == "__main__":
    app = InstallerApp()
    app.run(sys.argv)
