import sys
import os
import subprocess
import threading
import urllib.request
import time
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
    {"name": "DaVinci Resolve",  "pkg": "davinci-resolve",             "source": "aur",     "checked": False},
]

# Lista podstawowych środowisk
DE_LIST = [
    {"name": "KDE Plasma 6",      "pkg": "plasma-meta",       "id": "kde"},
    {"name": "GNOME",             "pkg": "gnome",             "id": "gnome"},
    {"name": "Hyperland",         "pkg": "hyprland",          "id": "hypr"},
]

# ==============================================================================
# 🔮 SKRYPTY KONFIGURACYJNE KDE (JavaScript)
# ==============================================================================

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
bottomPanel.offset = 0;
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
        if cmd_list[0] == "sudo":
            cmd_str = " ".join(cmd_list).replace("sudo", "sudo -S")
            full_cmd = f"echo '{self.password}' | {cmd_str}"
            use_shell = True
        else:
            full_cmd = cmd_list

        try:
            subprocess.run(full_cmd, shell=use_shell, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False

    def install_pkg_string(self, source, pkg_name):
        if source == "flatpak":
            return self.run_cmd(["sudo", "flatpak", "install", "flathub", pkg_name, "-y"])
        elif source == "aur":
            return self.run_cmd(["yay", "-S", pkg_name, "--noconfirm", "--answerdiff", "None", "--answerclean", "None"])
        else:
            return self.run_cmd(["sudo", "pacman", "-S", pkg_name, "--noconfirm", "--needed"])

    def configure_kde_preset(self):
        if self.preset == "clean":
            return

        self.on_progress(90, "Pobieranie motywów (Layan, Bibata)...")
        themes = [
            "layan-kde-git",
            "bibata-cursor-theme-bin",
            "kwin-effects-better-blur-dx-git",
            "kwin-effect-rounded-corners-git"
        ]
        for theme in themes:
            self.install_pkg_string("aur", theme)

        self.on_progress(95, "Aplikowanie ustawień wyglądu...")

        js_script = JS_LAYOUT_DOCK if self.preset == "dock" else JS_LAYOUT_STANDARD

        script_path = "/tmp/plasma_layout.js"
        with open(script_path, "w") as f:
            f.write(js_script)

        autostart_dir = os.path.expanduser("~/.config/autostart")
        os.makedirs(autostart_dir, exist_ok=True)

        setup_script = f"""[Desktop Entry]
Type=Application
Name=Arch Setup Theme
Exec=sh -c 'qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat {script_path})"; kwriteconfig6 --file kwinrc --group Plugins --key betterblurEnabled true; kwriteconfig6 --file kwinrc --group Plugins --key roundedcornersEnabled true; lookandfeeltool -a com.github.vinceliuice.Layan; rm ~/.config/autostart/arch_setup_theme.desktop'
X-KDE-autostart-after=panel
"""
        with open(f"{autostart_dir}/arch_setup_theme.desktop", "w") as f:
            f.write(setup_script)

        try:
            subprocess.run(["kwriteconfig6", "--file", "kwinrc", "--group", "Plugins", "--key", "betterblurEnabled", "true"])
            subprocess.run(["kwriteconfig6", "--file", "kwinrc", "--group", "Plugins", "--key", "roundedcornersEnabled", "true"])
        except: pass

    def run(self):
        current_step = 0

        self.on_progress(5, "Aktualizacja systemu...")
        self.run_cmd(["sudo", "pacman", "-Sy"])
        self.run_cmd(["sudo", "pacman", "-S", "git", "base-devel", "flatpak", "--noconfirm", "--needed"])

        cmd = ["sudo", "flatpak", "remote-add", "--if-not-exists", "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"]
        self.run_cmd(cmd)

        for item in self.queue:
            percent = int((current_step / self.total_steps) * 80) + 10
            self.on_progress(percent, f"Instalacja: {item['name']}...")
            self.install_pkg_string(item.get('source', 'pacman'), item['pkg'])
            current_step += 1

        if self.preset != "clean":
            self.configure_kde_preset()

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
        self.init_presets()
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
        if widget.get_active() and de_id == "kde":
            self.is_kde_selected = True
        elif widget.get_active():
            self.is_kde_selected = False

    def go_to_presets_or_install(self, btn):
        if self.is_kde_selected:
            self.stack.set_visible_child_name("presets")
        else:
            self.on_install_clicked(btn)

    # --- POPRAWIONA FUNKCJA PRESETÓW ---
    def init_presets(self):
        page = Adw.PreferencesPage()
        page.set_title("Styl KDE Plasma")

        # Tworzymy grupę dla kart
        group = Adw.PreferencesGroup(title="Wybierz wygląd")
        page.add(group)

        self.preset_radios = {}
        r_group = None

        # PRESET 1
        p1 = self.create_preset_card("✨ Layan Dock (Twój styl)", "Pasek na górze, pływający dock na dole.\nMotyw Layan, BetterBlur, Rounded Corners.", "dock", r_group)
        r_group = p1[0]
        group.add(p1[1]) # Dodajemy kartę do grupy
        self.preset_radios["dock"] = p1[0]

        # PRESET 2
        p2 = self.create_preset_card("🎨 Layan Standard", "Klasyczny pasek na dole.\nMotyw Layan + efekty.", "standard", r_group)
        group.add(p2[1])
        self.preset_radios["standard"] = p2[0]

        # PRESET 3
        p3 = self.create_preset_card("🧹 Czysta Plasma", "Domyślny wygląd Arch Linux.\nBez dodatków.", "clean", r_group)
        group.add(p3[1])
        self.preset_radios["clean"] = p3[0]

        self.preset_radios["dock"].set_active(True)

        # Button Group
        btn_group = Adw.PreferencesGroup()
        page.add(btn_group)

        btn = Gtk.Button(label="Zainstaluj wszystko")
        btn.add_css_class("purple-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_margin_top(20)
        btn.connect("clicked", self.on_install_clicked)

        # Opakowanie dla przycisku
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn)

        btn_group.add(btn_box)

        self.stack.add_named(page, "presets")

    def create_preset_card(self, title, desc, id_name, group):
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        card.add_css_class("purple-card")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        lbl_t = Gtk.Label(label=title, xalign=0); lbl_t.add_css_class("preset-title")
        lbl_d = Gtk.Label(label=desc, xalign=0); lbl_d.add_css_class("caption")
        vbox.append(lbl_t); vbox.append(lbl_d)

        radio = Gtk.CheckButton(group=group)
        radio.set_valign(Gtk.Align.CENTER)

        card.append(vbox)
        img = Gtk.Image(); card.append(img); img.set_hexpand(True)
        card.append(radio)

        return (radio, card)

    def init_progress(self):
        self.page_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.page_progress.set_valign(Gtk.Align.CENTER)
        self.page_progress.set_halign(Gtk.Align.CENTER)

        # LOGO
        self.prog_logo = Gtk.Image()
        self.prog_logo.set_pixel_size(150)
        path = "/tmp/arch_logo.svg"
        if not os.path.exists(path):
            try: urllib.request.urlretrieve("https://archlinux.org/static/logos/archlinux-logo-dark-scalable.518881f04ca9.svg", path)
            except: pass
        if os.path.exists(path): self.prog_logo.set_from_paintable(Gdk.Texture.new_from_file(Gio.File.new_for_path(path)))
        else: self.prog_logo.set_from_icon_name("system-software-install-symbolic")

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.add_css_class("violet-progress")
        self.progress_bar.set_size_request(400, 20)

        self.lbl_status = Gtk.Label(label="Czekam...")
        self.lbl_status.add_css_class("title-2")

        self.page_progress.append(self.prog_logo)
        self.page_progress.append(self.progress_bar)
        self.page_progress.append(self.lbl_status)
        self.stack.add_named(self.page_progress, "progress")

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
        queue = []
        for pkg, (chk, inf) in self.soft_checks.items():
            if chk.get_active(): queue.append(inf)
        for pid, (rad, inf) in self.de_radios.items():
            if rad.get_active(): queue.append(inf)

        preset = "clean"
        if self.is_kde_selected:
            if self.preset_radios["dock"].get_active(): preset = "dock"
            elif self.preset_radios["standard"].get_active(): preset = "standard"

        self.ask_password(queue, preset)

    def ask_password(self, queue, preset):
        dialog = Adw.MessageDialog(transient_for=self, heading="Hasło", body="Wymagane sudo.")
        dialog.add_response("ok", "Instaluj")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        entry = Gtk.PasswordEntry()
        entry.connect("activate", lambda w: dialog.response("ok"))
        box.append(entry)
        dialog.set_extra_child(box)

        def on_response(d, r):
            if r == "ok":
                pwd = entry.get_text()
                d.close()
                self.stack.set_visible_child_name("progress")
                InstallWorker(pwd, queue, preset, self.update_prog, lambda x: self.stack.set_visible_child_name("finish")).start()
            else: d.close()

        dialog.connect("response", on_response)
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
