import sys
import os
import subprocess
import threading
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

# ==============================================================================
# 🔮 TWOJE PRESETY (KONFIGURACJA)
# ==============================================================================

PRESETS = [
    {
        "id": "layan_dock",
        "name": "Layan Dock",
        "desc": "Styl MacOS. Pasek na górze, pływający dok na dole. Efekt Blur i zaokrąglone rogi.",
        "icon": "user-desktop-symbolic", # Ikona systemowa
        "pkgs": ["layan-kde-git", "bibata-cursor-theme-bin", "kwin-effects-better-blur-dx-git", "kwin-effect-rounded-corners-git"],
        "script": "dock"
    },
    {
        "id": "layan_std",
        "name": "Layan Standard",
        "desc": "Klasyczny układ (Windows-like) z nowoczesnym motywem Layan.",
        "icon": "view-app-grid-symbolic",
        "pkgs": ["layan-kde-git", "bibata-cursor-theme-bin"],
        "script": "standard"
    },
    {
        "id": "clean",
        "name": "Czysta Plasma",
        "desc": "Przywraca domyślny, czysty wygląd Arch Linux.",
        "icon": "edit-delete-symbolic",
        "pkgs": [],
        "script": "none"
    }
]

# SKRYPTY JS DLA KDE (UKŁAD PANELI)
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
# ⚙️ BACKEND (INSTALATOR)
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
        self.run_sudo("ls") # Odśwież sudo
        subprocess.run(f"yay -S {pkg} --noconfirm --answerdiff None --answerclean None", shell=True)

    def apply_js_layout(self, script_content):
        os.makedirs(os.path.expanduser("~/.config/autostart"), exist_ok=True)
        spath = "/tmp/layout.js"
        with open(spath, "w") as f: f.write(script_content)

        # Tworzymy autostart, który wykona się po restarcie
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

        # 1. Instalacja pakietów
        for i, pkg in enumerate(pkgs):
            self.on_progress(int((i/total)*100), f"Instalowanie: {pkg}...")
            self.run_yay(pkg)

        # 2. Aplikowanie skryptów
        self.on_progress(90, "Konfiguracja KDE Plasma...")
        if self.preset["script"] == "dock":
            self.apply_js_layout(JS_DOCK)
        elif self.preset["script"] == "standard":
            self.apply_js_layout(JS_STD)

        self.on_progress(100, "Gotowe!")
        GLib.idle_add(self.on_finish)

# ==============================================================================
# 🎨 GUI (STYL LINEXIN / LIBADWAITA)
# ==============================================================================

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Presets")
        self.set_default_size(800, 600)

        # WYGLĄD
        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        # GŁÓWNY KONTENER (CLAMP - centruje zawartość jak w Linexin)
        clamp = Adw.Clamp()
        clamp.set_maximum_size(700)

        # BOX NA ZAWARTOŚĆ
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_margin_top(40)
        box.set_margin_bottom(40)
        clamp.set_child(box)

        # 1. NAGŁÓWEK (LOGO I TYTUŁ)
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        icon = Gtk.Image.new_from_icon_name("preferences-desktop-theme")
        icon.set_pixel_size(96)

        title = Gtk.Label(label="Wybierz Styl")
        title.add_css_class("title-1")

        subtitle = Gtk.Label(label="Dostosuj wygląd środowiska KDE Plasma")
        subtitle.add_css_class("body")
        subtitle.get_style_context().add_class("dim-label")

        header_box.append(icon)
        header_box.append(title)
        header_box.append(subtitle)
        box.append(header_box)

        # 2. LISTA PRESETÓW (ADW.PREFERENCESGROUP)
        # To klucz do wyglądu - używamy natywnych grup Adwaita
        self.preset_group = Adw.PreferencesGroup()
        self.preset_group.set_title("Dostępne Presety")

        for preset in PRESETS:
            row = Adw.ActionRow()
            row.set_title(preset["name"])
            row.set_subtitle(preset["desc"])
            row.set_icon_name(preset["icon"])

            # Przycisk "Zastosuj" w wierszu
            btn = Gtk.Button(label="Zastosuj")
            btn.add_css_class("pill") # Zaokrąglony
            btn.add_css_class("suggested-action") # Niebieski akcent
            btn.set_valign(Gtk.Align.CENTER)
            btn.connect("clicked", self.on_apply_clicked, preset)

            row.add_suffix(btn)
            self.preset_group.add(row)

        box.append(self.preset_group)

        # SCROLL WINDOW (Żeby można było przewijać)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(clamp)

        # HEADER BAR (Pasek tytułu)
        hb = Adw.HeaderBar()
        hb.set_show_end_title_buttons(True)

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root_box.append(hb)
        root_box.append(scroll)

        self.set_content(root_box)

    def on_apply_clicked(self, btn, preset):
        self.ask_password(preset)

    def ask_password(self, preset):
        # Dialog hasła w stylu Adwaita
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        entry = Gtk.PasswordEntry()
        entry.set_placeholder_text("Hasło sudo")
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

        # Callback dla odpowiedzi
        def response_cb(d, response):
            if response == "apply":
                pwd = entry.get_text()
                self.show_progress(pwd, preset)
            d.close()

        dialog.connect("response", response_cb)
        dialog.present()

    def show_progress(self, password, preset):
        # Tworzymy okno postępu (Modal)
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

        # Hack żeby dodać box do StatusPage (używając set_child)
        content.set_child(box)
        self.prog_win.set_content(content)
        self.prog_win.present()

        # Start Workera
        ApplyWorker(password, preset, self.update_progress, self.finish_progress).start()

    def update_progress(self, pct, text):
        GLib.idle_add(lambda: (self.pbar.set_fraction(pct/100), self.lbl_status.set_text(text)))

    def finish_progress(self):
        # Zamknij okno postępu i pokaż info o sukcesie
        self.prog_win.close()

        toast = Adw.Toast.new("Gotowe! Wyloguj się, aby zobaczyć zmiany.")
        self.add_toast(toast)

class PresetsApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.arch.presets", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win: win = MainWindow(self)
        win.present()

if __name__ == "__main__":
    app = PresetsApp()
    app.run(sys.argv)
