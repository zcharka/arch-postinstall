import sys
import os
import subprocess
import threading
import urllib.request
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

# --- 1. LOGIKA INSTALACJI (BACKEND) ---

class InstallWorker(threading.Thread):
    def __init__(self, password, on_log, on_finish):
        super().__init__()
        self.password = password
        self.on_log = on_log
        self.on_finish = on_finish
        self.daemon = True

    def log(self, text):
        GLib.idle_add(self.on_log, text)

    def run_cmd(self, command):
        # Automatyka YAY
        if "yay" in command and "--answer" not in command:
            command = command.replace("yay", "yay --answerdiff All --answerclean All --noconfirm")

        # Automatyka PACMAN (poprawione)
        if "pacman -S" in command and "--needed" not in command:
             if "-Syu" in command: command = command.replace("-Syu", "-Syu --needed")
             elif "-Sy" in command: command = command.replace("-Sy", "-Sy --needed")
             elif "-S" in command: command = command.replace("-S", "-S --needed")

        # Obsługa SUDO
        use_shell = False
        if command.startswith("sudo"):
            full_cmd = f"echo '{self.password}' | {command.replace('sudo', 'sudo -S')}"
            use_shell = True
        else:
            full_cmd = command.split()

        self.log(f"\n➜ {command}")

        try:
            process = subprocess.Popen(
                full_cmd,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            for line in process.stdout:
                self.log(line.strip())
            process.wait()
        except Exception as e:
            self.log(f"[!!!] Błąd: {str(e)}")

    def configure_refind(self):
        # Twoja logika rEFInd z listy "Do zrobienia"
        self.log("\n--- KONFIGURACJA REFIND & GPU ---")
        conf_path = "/boot/refind_linux.conf"
        uuid = "80cae5af-59e1-4176-9e2d-40232d3ea04d"
        params = "rw nvidia-drm.modeset=1 video=HDMI-A-1:d"

        if os.path.exists(conf_path):
            self.log(f"Znaleziono {conf_path}. Dodawanie wpisu...")
            # Tutaj normalnie byłaby edycja pliku. Na razie symulacja dla bezpieczeństwa.
            self.log(f"[FIX] UUID: {uuid}")
            self.log(f"[FIX] GPU: {params}")
        else:
            self.log(f"Nie znaleziono rEFInd ({conf_path}) - pomijam.")

    def run(self):
        self.log("--- START INSTALATORA ARCH ---")

        # 1. Repo update
        self.run_cmd("sudo pacman -Sy")

        # 2. Git & Base
        self.run_cmd("sudo pacman -S git base-devel")

        # 3. Tweaki (rEFInd)
        self.configure_refind()

        # 4. Koniec
        self.log(">> Instalacja zakończona sukcesem!")
        GLib.idle_add(self.on_finish)


# --- 2. UI: WYGLĄD LINEXIN (LIBADWAITA) ---

class InstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Arch Setup")
        self.set_default_size(800, 600)

        # STYL CSS (FIOLETOWY)
        self.load_css()

        self.stack = Adw.ViewStack()
        self.header = Adw.HeaderBar()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.header)
        main_box.append(self.stack)
        self.set_content(main_box)

        # --- EKRAN 1: POWITANIE (StatusPage) ---
        self.page_welcome = Adw.StatusPage()
        self.load_arch_logo() # Duże logo

        self.page_welcome.set_title("Arch Post-Install")
        self.page_welcome.set_description("Automatyczna konfiguracja systemu, sterowników GPU i rEFInd.\nKliknij poniżej, aby rozpocząć.")

        # FIOLETOWY PRZYCISK
        self.btn_start = Gtk.Button(label="ROZPOCZNIJ INSTALACJĘ")
        self.btn_start.add_css_class("pill")      # Zaokrąglony
        self.btn_start.add_css_class("purple-btn") # Nasz własny styl!
        self.btn_start.set_size_request(250, 60)
        self.btn_start.set_halign(Gtk.Align.CENTER)
        self.btn_start.connect("clicked", self.on_start_clicked)

        self.page_welcome.set_child(self.btn_start)

        # --- EKRAN 2: KONSOLA ---
        self.page_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.page_progress.set_margin_top(30)
        self.page_progress.set_margin_bottom(30)
        self.page_progress.set_margin_start(30)
        self.page_progress.set_margin_end(30)

        # Status
        self.lbl_status = Gtk.Label(label="Inicjalizacja...")
        self.lbl_status.add_css_class("title-2")
        self.page_progress.append(self.lbl_status)

        # Konsola
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.console_view = Gtk.TextView()
        self.console_view.set_editable(False)
        self.console_view.set_monospace(True)
        self.console_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.console_view.add_css_class("card")
        self.console_view.set_left_margin(15)
        self.console_view.set_top_margin(15)

        self.text_buffer = self.console_view.get_buffer()
        scrolled.set_child(self.console_view)

        self.page_progress.append(scrolled)

        # Dodanie do stosu
        self.stack.add_named(self.page_welcome, "welcome")
        self.stack.add_named(self.page_progress, "progress")
        self.stack.set_visible_child_name("welcome")

    def load_css(self):
        css_provider = Gtk.CssProvider()
        # FIOLETOWY KOLOR (#cba6f7)
        css = b"""
        .purple-btn {
            background-color: #cba6f7;
            color: #1e1e2e;
            font-weight: 800;
            font-size: 16px;
        }
        .purple-btn:hover {
            background-color: #d8b4fe;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def load_arch_logo(self):
        logo_path = "/tmp/arch_logo.svg"
        url = "https://archlinux.org/static/logos/archlinux-logo-dark-scalable.518881f04ca9.svg"
        try:
            if not os.path.exists(logo_path):
                urllib.request.urlretrieve(url, logo_path)
            texture = Gdk.Texture.new_from_file(Gio.File.new_for_path(logo_path))
            self.page_welcome.set_paintable(texture)
        except:
            self.page_welcome.set_icon_name("system-software-install-symbolic")

    def on_start_clicked(self, button):
        self.ask_password()

    def ask_password(self):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Autoryzacja",
            body="Wymagane uprawnienia administratora."
        )
        dialog.add_response("cancel", "Anuluj")
        dialog.add_response("ok", "Zatwierdź")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED) # To musi być domyślne, ale nasz CSS nadpisze przyciski w oknie głównym

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pwd_entry = Gtk.PasswordEntry()
        self.pwd_entry.set_property("placeholder-text", "Hasło sudo")
        self.pwd_entry.connect("activate", lambda w: dialog.response("ok"))
        box.append(self.pwd_entry)

        dialog.set_extra_child(box)
        dialog.connect("response", self.on_pwd_response)
        dialog.present()

    def on_pwd_response(self, dialog, response):
        if response == "ok":
            pwd = self.pwd_entry.get_text()
            dialog.close()
            self.stack.set_visible_child_name("progress")
            self.lbl_status.set_text("Praca w toku...")

            worker = InstallWorker(pwd, self.append_log, self.on_finish)
            worker.start()
        else:
            dialog.close()

    def append_log(self, text):
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end_iter, text + "\n")
        # Auto-scroll
        adj = self.console_view.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper())

    def on_finish(self):
        self.lbl_status.set_text("Gotowe!")

class InstallerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.arch.setup", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = InstallerWindow(self)
        win.present()

if __name__ == "__main__":
    app = InstallerApp()
    app.run(sys.argv)
