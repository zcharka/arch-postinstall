import sys
import os
import subprocess
import threading
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

# ==============================================================================
# 🔮 PRESETY
# ==============================================================================

PRESETS = [
    {
        "id": "layan_dock",
        "name": "Layan Dock",
        "desc": "Styl MacOS. Pasek na górze, pływający dok na dole.\nMotyw Layan + Efekty.",
        "icon": "user-desktop-symbolic",
        "pkgs": ["layan-kde-git", "bibata-cursor-theme-bin", "kwin-effects-better-blur-dx-git", "kwin-effect-rounded-corners-git"],
        "script": "dock"
    },
    {
        "id": "layan_std",
        "name": "Layan Standard",
        "desc": "Klasyczny układ z nowoczesnym motywem Layan.",
        "icon": "view-app-grid-symbolic",
        "pkgs": ["layan-kde-git", "bibata-cursor-theme-bin"],
        "script": "standard"
    },
    {
        "id": "clean",
        "name": "Czysta Plasma",
        "desc": "Przywraca domyślny wygląd Arch Linux.",
        "icon": "edit-delete-symbolic",
        "pkgs": [],
        "script": "none"
    }
]

# SKRYPTY JS DLA KDE
JS_DOCK = """
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) { allPanels[i].remove(); }
var topPanel = new Panel();
topPanel.location = "top";
topPanel.height = 30;
topPanel.addWidget("org.kde.plasma.kickoff");
topPanel.addWidget("org.kde.plasma.panelspacer");
topPanel.addWidget("org.kde.plasma.clock");
topPanel.addWidget("org.kde.plasma.panelspacer");
topPanel.addWidget("org.kde.plasma.systemtray");

var bottomPanel = new Panel();
bottomPanel.location = "bottom";
bottomPanel.height = 52;
bottomPanel.lengthMode = "fit";
bottomPanel.hiding = "dodgewindows";
bottomPanel.floating = true;
bottomPanel.addWidget("org.kde.plasma.icontasks");
"""

JS_STD = """
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) { allPanels[i].remove(); }
var panel = new Panel();
panel.location = "bottom";
panel.height = 44;
panel.addWidget("org.kde.plasma.kickoff");
panel.addWidget("org.kde.plasma.icontasks");
panel.addWidget("org.kde.plasma.panelspacer");
panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.clock");
"""

# ==============================================================================
# ⚙️ BACKEND
# ==============================================================================

class ApplyWorker(threading.Thread):
    def __init__(self, password, preset, on_progress, on_finish):
        super().__init__()
        self.password = password
        self.preset = preset
        self.on_progress = on_progress
        self.on_finish = on_finish
        self.daemon = True

    def run_sudo(self, cmd):
        subprocess.run(f"echo '{self.password}' | sudo -S {cmd}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def run_yay(self, pkg):
        self.run_sudo("ls")
        subprocess.run(f"yay -S {pkg} --noconfirm --answerdiff None --answerclean None", shell=True)

    def apply_js_layout(self, script_content):
        os.makedirs(os.path.expanduser("~/.config/autostart"), exist_ok=True)
        spath = "/tmp/layout.js"
        with open(spath, "w") as f: f.write(script_content)

        desktop = f"""[Desktop Entry]
Type=Application
Name=ThemeApply
Exec=sh -c 'sleep 5; qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat {spath})"; lookandfeeltool -a com.github.vinceliuice.Layan; kwriteconfig6 --file kwinrc --group Plugins --key betterblurEnabled true; kwriteconfig6 --file kwinrc --group Plugins --key roundedcornersEnabled true; rm ~/.config/autostart/theme_apply.desktop'
X-KDE-autostart-after=panel
"""
        with open(os.path.expanduser("~/.config/autostart/theme_apply.desktop"), "w") as f:
            f.write(desktop)

    def run(self):
        pkgs = self.preset["pkgs"]
        total = len(pkgs) + 2

        for i, pkg in enumerate(pkgs):
            self.on_progress(int((i/total)*100), f"Instalowanie: {pkg}...")
            self.run_yay(pkg)

        self.on_progress(90, "Konfiguracja KDE Plasma...")
        if self.preset["script"] == "dock":
            self.apply_js_layout(JS_DOCK)
        elif self.preset["script"] == "standard":
            self.apply_js_layout(JS_STD)

        self.on_progress(100, "Gotowe!")
        GLib.idle_add(self.on_finish)

# ==============================================================================
# 🎨 GUI
# ==============================================================================

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Presets")
        self.set_default_size(800, 600)

        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        page = Adw.PreferencesPage()
        page.set_title("Wybierz Styl")
        page.set_icon_name("preferences-desktop-theme")

        group = Adw.PreferencesGroup()
        group.set_title("Dostępne Presety")
        group.set_description("Kliknij 'Zastosuj', aby pobrać i ustawić wygląd.")

        for preset in PRESETS:
            row = Adw.ActionRow()
            row.set_title(preset["name"])
            row.set_subtitle(preset["desc"])

            icon = Gtk.Image.new_from_icon_name(preset["icon"])
            row.add_prefix(icon)

            btn = Gtk.Button(label="Zastosuj")
            btn.add_css_class("pill")
            btn.add_css_class("suggested-action")
            btn.set_valign(Gtk.Align.CENTER)
            btn.connect("clicked", self.on_apply_clicked, preset)

            row.add_suffix(btn)
            group.add(row)

        page.add(group)
        self.set_content(page)

    def on_apply_clicked(self, btn, preset):
        self.ask_password(preset)

    def ask_password(self, preset):
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        entry = Gtk.PasswordEntry()
        # --- NAPRAWA BŁĘDU ---
        # Zamiast entry.set_placeholder_text używamy set_property
        entry.set_property("placeholder-text", "Hasło sudo")

        body.append(Gtk.Label(label="Wymagane uprawnienia administratora."))
        body.append(entry)

        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=f"Instalacja: {preset['name']}",
        )
        dialog.set_extra_child(body)
        dialog.add_response("cancel", "Anuluj")
        dialog.add_response("apply", "Zatwierdź")
        dialog.set_response_appearance("apply", Adw.ResponseAppearance.SUGGESTED)

        def response_cb(d, response):
            if response == "apply":
                pwd = entry.get_text()
                self.show_progress(pwd, preset)
            d.close()

        dialog.connect("response", response_cb)
        dialog.present()

    def show_progress(self, password, preset):
        self.prog_win = Adw.Window(transient_for=self)
        self.prog_win.set_default_size(400, 300)
        self.prog_win.set_modal(True)
        self.prog_win.set_title("Przetwarzanie...")

        content = Adw.StatusPage()
        content.set_title("Proszę czekać")
        content.set_description("Trwa pobieranie i konfiguracja...")
        content.set_icon_name("system-software-install-symbolic")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_halign(Gtk.Align.CENTER)

        self.pbar = Gtk.ProgressBar()
        self.pbar.set_size_request(300, -1)
        self.lbl_status = Gtk.Label(label="Inicjalizacja...")

        box.append(self.pbar)
        box.append(self.lbl_status)

        content.set_child(box)
        self.prog_win.set_content(content)
        self.prog_win.present()

        ApplyWorker(password, preset, self.update_progress, self.finish_progress).start()

    def update_progress(self, pct, text):
        GLib.idle_add(lambda: (self.pbar.set_fraction(pct/100), self.lbl_status.set_text(text)))

    def finish_progress(self):
        self.prog_win.close()
        toast = Adw.Toast.new("Gotowe! Wyloguj się, aby zobaczyć zmiany.")
        self.add_toast(toast)

class PresetsApp(Adw.Application):
    def __init__(self):
        super().__init__(application=app, title="Presets") # ZMIENIONO NAZWĘ APLIKACJI

    def do_activate(self):
        win = self.props.active_window
        if not win: win = MainWindow(self)
        win.present()

if __name__ == "__main__":
    app = PresetsApp()
    app.run(sys.argv)
