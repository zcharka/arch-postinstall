import sys
import os
import subprocess
import threading
import gi
import time

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

# ==============================================================================
# 🔮 PRESETY (KOPIA 1:1 Z LINEXIN)
# ==============================================================================

PRESETS = [
    {
        "id": "layan",
        "name": "Layan Theme",
        "desc": "Nowoczesny, fioletowy motyw z zaokrąglonymi rogami i efektem blur.",
        "icon": "preferences-desktop-theme",
        "pkgs": [
            "layan-kde-git",
            "bibata-cursor-theme-bin",
            "papirus-icon-theme",
            "kwin-effects-better-blur-dx-git",
            "kwin-effect-rounded-corners-git"
        ],
        "script": "layan"
    },
    {
        "id": "whitesur",
        "name": "WhiteSur (MacOS)",
        "desc": "Wygląd inspirowany systemem macOS Big Sur.",
        "icon": "user-desktop-symbolic",
        "pkgs": [
            "whitesur-kde-git",
            "whitesur-icon-theme-git",
            "bibata-cursor-theme-bin"
        ],
        "script": "whitesur"
    },
    {
        "id": "clean",
        "name": "Czysta Plasma (Reset)",
        "desc": "Przywraca domyślny wygląd Breeze.",
        "icon": "edit-delete-symbolic",
        "pkgs": [],
        "script": "clean"
    }
]

# SKRYPT JS: DOCK (Dla Layan/WhiteSur)
JS_LAYOUT = """
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) { allPanels[i].remove(); }

// --- GÓRNY PASEK ---
var topPanel = new Panel();
topPanel.location = "top";
topPanel.height = 30;
topPanel.addWidget("org.kde.plasma.kickoff");
topPanel.addWidget("org.kde.plasma.appmenu");
topPanel.addWidget("org.kde.plasma.panelspacer");
topPanel.addWidget("org.kde.plasma.clock");
topPanel.addWidget("org.kde.plasma.panelspacer");
topPanel.addWidget("org.kde.plasma.systemtray");

// --- DOLNY DOCK ---
var bottomPanel = new Panel();
bottomPanel.location = "bottom";
bottomPanel.height = 52;
bottomPanel.lengthMode = "fit";
bottomPanel.hiding = "dodgewindows";
bottomPanel.floating = true;
bottomPanel.addWidget("org.kde.plasma.icontasks");
"""

# SKRYPT JS: CLEAN (Standard)
JS_CLEAN = """
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) { allPanels[i].remove(); }
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
        # Odświeżamy uprawnienia sudo
        subprocess.run(f"echo '{self.password}' | sudo -S {cmd}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def run_yay(self, pkg):
        self.run_sudo("ls")
        # Ważne: --answerdiff=None --answerclean=All (bez spacji przy =)
        subprocess.run(f"yay -S {pkg} --noconfirm --answerdiff=None --answerclean=All", shell=True)

    def apply_config(self, script_js, theme_cmd, kwin_cmds):
        os.makedirs(os.path.expanduser("~/.config/autostart"), exist_ok=True)
        spath = "/tmp/layout.js"
        with open(spath, "w") as f: f.write(script_js)

        # Budujemy komendę do pliku .desktop
        cmds = ["sleep 3"] # Czekamy chwilę po starcie

        # Aplikowanie motywu
        if theme_cmd:
            cmds.append(theme_cmd)

        # Aplikowanie JS (Paneli)
        cmds.append(f'qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat {spath})"')

        # Aplikowanie KWin (Efekty)
        for cmd in kwin_cmds:
            cmds.append(cmd)

        # Sprzątanie
        cmds.append("rm ~/.config/autostart/theme_apply.desktop")

        full_cmd = "; ".join(cmds)

        desktop_entry = f"""[Desktop Entry]
Type=Application
Name=ThemeApply
Exec=sh -c '{full_cmd}'
X-KDE-autostart-after=panel
"""
        with open(os.path.expanduser("~/.config/autostart/theme_apply.desktop"), "w") as f:
            f.write(desktop_entry)

    def run(self):
        pkgs = self.preset["pkgs"]
        total = len(pkgs) + 2

        # 1. Instalacja
        for i, pkg in enumerate(pkgs):
            self.on_progress(int((i/total)*100), f"Instalowanie: {pkg}...")
            self.run_yay(pkg)

        self.on_progress(90, "Konfiguracja KDE Plasma...")

        # 2. Wybór Konfiguracji
        p_id = self.preset["script"]

        if p_id == "layan":
            self.apply_config(
                JS_LAYOUT,
                "lookandfeeltool -a com.github.vinceliuice.Layan",
                [
                    "kwriteconfig6 --file kwinrc --group Plugins --key betterblurEnabled true",
                    "kwriteconfig6 --file kwinrc --group Plugins --key roundedcornersEnabled true"
                ]
            )
        elif p_id == "whitesur":
            self.apply_config(
                JS_LAYOUT,
                "lookandfeeltool -a com.github.vinceliuice.WhiteSur",
                ["kwriteconfig6 --file kwinrc --group Plugins --key betterblurEnabled true"]
            )
        elif p_id == "clean":
            self.apply_config(
                JS_CLEAN,
                "lookandfeeltool -a org.kde.breeze.desktop",
                [
                    "kwriteconfig6 --file kwinrc --group Plugins --key betterblurEnabled false",
                    "kwriteconfig6 --file kwinrc --group Plugins --key roundedcornersEnabled false"
                ]
            )

        self.on_progress(100, "Gotowe!")
        GLib.idle_add(self.on_finish)

# ==============================================================================
# 🎨 GUI (POPRAWIONE TOASTY I HASŁO)
# ==============================================================================

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="RatPresets")
        self.set_default_size(850, 650)

        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        # 1. Overlay (dla Toastów)
        self.overlay = Adw.ToastOverlay()
        self.set_content(self.overlay)

        # 2. Główna strona
        page = Adw.PreferencesPage()
        page.set_title("Wybierz Styl")
        page.set_icon_name("preferences-desktop-theme")
        self.overlay.set_child(page)

        group = Adw.PreferencesGroup()
        group.set_title("Dostępne Presety")
        group.set_description("Zastosowanie presetu wymaga wylogowania.")

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

    def on_apply_clicked(self, btn, preset):
        self.ask_password(preset)

    def ask_password(self, preset):
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        entry = Gtk.PasswordEntry()
        # Poprawka: używamy set_placeholder_text tylko jeśli zadziała, fallback do property
        try:
            entry.set_placeholder_text("Hasło sudo")
        except AttributeError:
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
                d.close() # Najpierw zamykamy dialog hasła
                self.show_progress(pwd, preset)
            else:
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
        # Używamy overlay do wyświetlenia toasta
        toast = Adw.Toast.new("Gotowe! Wyloguj się, aby zobaczyć zmiany.")
        self.overlay.add_toast(toast)

class RatPresetsApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.rat.presets", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win: win = MainWindow(self)
        win.present()

if __name__ == "__main__":
    app = RatPresetsApp()
    app.run(sys.argv)
