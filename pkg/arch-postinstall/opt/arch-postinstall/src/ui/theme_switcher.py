import sys
import os
import subprocess
import threading
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

# ==============================================================================
# 🔮 DANE PRESETÓW
# ==============================================================================

PRESETS = {
    "kde": [
        {
            "id": "kde_dock",
            "title": "✨ Layan Dock",
            "desc": "Pasek na górze, pływający dock na dole.\nMotyw Layan + Efekty.",
            "pkgs": ["layan-kde-git", "bibata-cursor-theme-bin", "kwin-effects-better-blur-dx-git", "kwin-effect-rounded-corners-git"],
            "script_type": "js_dock"
        },
        {
            "id": "kde_standard",
            "title": "🎨 Layan Standard",
            "desc": "Klasyczny układ z nowoczesnym motywem.\nLayan Theme.",
            "pkgs": ["layan-kde-git", "bibata-cursor-theme-bin"],
            "script_type": "js_standard"
        },
        {
            "id": "clean",
            "title": "🧹 Czysta Plasma",
            "desc": "Przywraca domyślny wygląd Arch Linux.",
            "pkgs": [],
            "script_type": "none"
        }
    ],
    "gnome": [
        {
            "id": "gnome_macos",
            "title": "🍎 WhiteSur (MacOS Style)",
            "desc": "Motyw WhiteSur, ikony MacOS, Dock na dole.",
            "pkgs": ["whitesur-gtk-theme-git", "whitesur-icon-theme-git", "bibata-cursor-theme-bin"],
            "script_type": "gnome_macos"
        },
        {
            "id": "gnome_dark",
            "title": "🌑 Adwaita Pro",
            "desc": "Ciemny motyw systemowy, kursor Bibata.",
            "pkgs": ["bibata-cursor-theme-bin", "adw-gtk3-git"],
            "script_type": "gnome_dark"
        }
    ]
}

# Skrypty JS dla KDE
JS_KDE_DOCK = """
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) { allPanels[i].remove(); }
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

JS_KDE_STANDARD = """
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
# 🧠 BACKEND
# ==============================================================================

class ThemeWorker(threading.Thread):
    def __init__(self, password, env, preset_data, on_progress, on_finish):
        super().__init__()
        self.password = password
        self.env = env
        self.data = preset_data
        self.on_progress = on_progress
        self.on_finish = on_finish
        self.daemon = True

    def run_sudo(self, cmd):
        full = f"echo '{self.password}' | sudo -S {cmd}"
        subprocess.run(full, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def run_yay(self, pkg):
        self.run_sudo("ls") # Refresh token
        cmd = f"yay -S {pkg} --noconfirm --answerdiff None --answerclean None"
        subprocess.run(cmd, shell=True)

    def apply_kde(self):
        pkgs = self.data.get("pkgs", [])
        total = len(pkgs) + 2
        for i, pkg in enumerate(pkgs):
            self.on_progress(int((i/total)*100), f"Instalacja: {pkg}")
            self.run_yay(pkg)

        stype = self.data.get("script_type")
        if stype != "none":
            self.on_progress(80, "Konfiguracja układu Plasma...")
            js = JS_KDE_DOCK if stype == "js_dock" else JS_KDE_STANDARD

            os.makedirs(os.path.expanduser("~/.config/autostart"), exist_ok=True)
            spath = "/tmp/layout.js"
            with open(spath, "w") as f: f.write(js)

            desktop_file = f"""[Desktop Entry]
Type=Application
Name=ThemeApply
Exec=sh -c 'qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat {spath})"; lookandfeeltool -a com.github.vinceliuice.Layan; rm ~/.config/autostart/theme_apply.desktop'
X-KDE-autostart-after=panel
"""
            with open(os.path.expanduser("~/.config/autostart/theme_apply.desktop"), "w") as f:
                f.write(desktop_file)

    def run(self):
        self.on_progress(5, "Przygotowanie...")
        if self.env == "kde": self.apply_kde()
        # Tu można dodać logikę GNOME
        self.on_progress(100, "Gotowe! Zrestartuj sesję.")
        GLib.idle_add(self.on_finish)

# ==============================================================================
# 🎨 GUI
# ==============================================================================

class ThemeAppWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Presets")
        self.set_default_size(900, 650)

        self.current_de = self.detect_de()
        print(f"DEBUG: Wykryto środowisko: {self.current_de}")

        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self.load_css()

        self.stack = Adw.ViewStack()
        self.header = Adw.HeaderBar()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.header)
        main_box.append(self.stack)
        self.set_content(main_box)

        self.init_pages()

    def detect_de(self):
        xdg = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "kde" in xdg or "plasma" in xdg: return "kde"
        if "gnome" in xdg: return "gnome"
        return "kde"

    def load_css(self):
        provider = Gtk.CssProvider()
        css = b"""
        .purple-btn { background-color: #cba6f7; color: #1e1e2e; font-weight: bold; border-radius: 9999px; padding: 10px 40px; }
        .purple-card { background-color: #313244; border-radius: 12px; padding: 20px; margin: 10px; }
        .title-accent { color: #cba6f7; font-weight: 800; font-size: 20px; }
        .violet-progress progress { background-color: #cba6f7; }
        """
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def init_pages(self):
        self.main_scroll = Gtk.ScrolledWindow()
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_container.set_margin_top(30)
        self.main_container.set_margin_bottom(30)
        self.main_container.set_margin_start(30)
        self.main_container.set_margin_end(30)

        title_label = Gtk.Label(label=f"Presety dla {self.current_de.upper()}")
        title_label.add_css_class("title-1")
        self.main_container.append(title_label)

        self.build_preset_list()

        self.main_scroll.set_child(self.main_container)
        self.stack.add_named(self.main_scroll, "presets")

        self.page_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.page_progress.set_valign(Gtk.Align.CENTER)
        self.page_progress.set_halign(Gtk.Align.CENTER)

        self.pbar = Gtk.ProgressBar()
        self.pbar.add_css_class("violet-progress")
        self.pbar.set_size_request(400, 20)
        self.lbl_stat = Gtk.Label(label="Inicjalizacja...")

        self.page_progress.append(self.pbar)
        self.page_progress.append(self.lbl_stat)
        self.stack.add_named(self.page_progress, "progress")

        self.page_finish = Adw.StatusPage()
        self.page_finish.set_title("Zastosowano!")
        self.page_finish.set_icon_name("emblem-ok-symbolic")
        self.page_finish.set_description("Wyloguj się i zaloguj ponownie, aby zobaczyć pełne efekty.")

        btn = Gtk.Button(label="Wyloguj teraz")
        btn.add_css_class("purple-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self.logout)
        self.page_finish.set_child(btn)
        self.stack.add_named(self.page_finish, "finish")

    def build_preset_list(self):
        items = PRESETS.get(self.current_de, [])
        self.radios = {}
        first_radio = None

        for item in items:
            card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
            card.add_css_class("purple-card")

            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            t = Gtk.Label(label=item["title"], xalign=0); t.add_css_class("title-accent")
            d = Gtk.Label(label=item["desc"], xalign=0); d.add_css_class("body")
            v.append(t); v.append(d)

            radio = Gtk.CheckButton(group=first_radio)
            if not first_radio: first_radio = radio
            radio.set_valign(Gtk.Align.CENTER)

            card.append(v)
            img = Gtk.Image(); card.append(img); img.set_hexpand(True)
            card.append(radio)

            self.main_container.append(card)
            self.radios[item["id"]] = (radio, item)

        btn = Gtk.Button(label="Zastosuj Wybrany Styl")
        btn.add_css_class("purple-btn")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_margin_top(20)
        btn.connect("clicked", self.on_apply)

        self.main_container.append(btn)

    def on_apply(self, btn):
        selected_data = None
        for pid, (rad, data) in self.radios.items():
            if rad.get_active():
                selected_data = data
                break
        if selected_data: self.ask_password(selected_data)

    def ask_password(self, data):
        dialog = Adw.MessageDialog(transient_for=self, heading="Autoryzacja", body="Wymagane hasło sudo.")
        dialog.add_response("ok", "Zatwierdź")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        entry = Gtk.PasswordEntry()
        entry.connect("activate", lambda w: dialog.response("ok"))
        box.append(entry)
        dialog.set_extra_child(box)

        def on_res(d, r):
            pwd = entry.get_text()
            d.close()
            self.stack.set_visible_child_name("progress")
            ThemeWorker(pwd, self.current_de, data, self.update_p, self.finish).start()

        dialog.connect("response", on_res)
        dialog.present()

    def update_p(self, pct, txt):
        GLib.idle_add(lambda: (self.pbar.set_fraction(pct/100), self.lbl_stat.set_text(txt)))

    def finish(self):
        self.stack.set_visible_child_name("finish")

    def logout(self, btn):
        subprocess.run(["qdbus", "org.kde.ksmserver", "/KSMServer", "logout", "0", "0", "0"])

class ThemeApp(Adw.Application):
    def __init__(self): super().__init__(application_id="com.arch.presets", flags=Gio.ApplicationFlags.FLAGS_NONE)
    def do_activate(self):
        win = self.props.active_window
        if not win: win = ThemeAppWindow(self)
        win.present()

if __name__ == "__main__":
    app = ThemeApp()
    app.run(sys.argv)
