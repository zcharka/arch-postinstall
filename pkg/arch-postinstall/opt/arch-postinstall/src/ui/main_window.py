import sys
import os
import subprocess
import threading
import urllib.request
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

# --- 1. CONFIG: LOGIKA INSTALACJI (BACKEND) ---

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
        # 1. Automatyka dla YAY
        if "yay" in command and "--answer" not in command:
            command = command.replace("yay", "yay --answerdiff All --answerclean All --noconfirm")

        # 2. Automatyka dla PACMAN (pomijanie zainstalowanych)
        if "pacman -S" in command and "--needed" not in command:
             if "-S" in command: command = command.replace("-S", "-S --needed")
             elif "-Sy" in command: command = command.replace("-Sy", "-Sy --needed")
             elif "-Syu" in command: command = command.replace("-Syu", "-Syu --needed")

        # 3. Obsługa SUDO
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
            if process.returncode != 0:
                self.log(f"[!] BŁĄD: Kod wyjścia {process.returncode}")
        except Exception as e:
            self.log(f"[!!!] Błąd krytyczny: {str(e)}")

    def run(self):
        self.log("--- ROZPOCZYNAM INSTALACJĘ ARCH POST-INSTALL ---")

        # --- TU WPISZ KOMENDY DO WYKONANIA ---
        self.log(">> Aktualizacja repozytoriów...")
        self.run_cmd("sudo pacman -Sy")

        self.log(">> Instalacja Gita i podstaw...")
        self.run_cmd("sudo pacman -S git base-devel")

        self.log(">> Instalacja zakończona!")
        GLib.idle_add(self.on_finish)


# --- 2. UI: WYGLĄD LINEXIN (LIBADWAITA) ---

class InstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Arch Setup")
        self.set_default_size(800, 600)

        self.stack = Adw.ViewStack()
        self.header = Adw.HeaderBar()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.header)
        main_box.append(self.stack)
        self.set_content(main_box)

        # --- EKRAN 1: POWITANIE ---
        self.page_welcome = Adw.StatusPage()

        # PRÓBA ZAŁADOWANIA LOGO ARCH LINUX
        self.load_arch_logo()

        self.page_welcome.set_title("Instalator Systemu")
        self.page_welcome.set_description("Skonfiguruj swój system Arch Linux jednym kliknięciem.\nZainstalowane zostaną motywy, ikony i poprawki.")

        self.btn_start = Gtk.Button(label="Rozpocznij instalację")
        self.btn_start.add_css_class("pill")
        self.btn_start.add_css_class("suggested-action")
        self.btn_start.set_size_request(200, 50)
        self.btn_start.set_halign(Gtk.Align.CENTER)
        self.btn_start.connect("clicked", self.on_start_clicked)

        self.page_welcome.set_child(self.btn_start)

        # --- EKRAN 2: KONSOLA ---
        self.page_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.page_progress.set_margin_top(20)
        self.page_progress.set_margin_bottom(20)
        self.page_progress.set_margin_start(20)
        self.page_progress.set_margin_end(20)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.console_view = Gtk.TextView()
        self.console_view.set_editable(False)
        self.console_view.set_monospace(True)
        self.console_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.console_view.add_css_class("card")

        self.text_buffer = self.console_view.get_buffer()
        scrolled.set_child(self.console_view)

        self.lbl_status = Gtk.Label(label="Przygotowywanie...")
        self.lbl_status.add_css_class("title-4")

        self.page_progress.append(self.lbl_status)
        self.page_progress.append(scrolled)

        self.stack.add_named(self.page_welcome, "welcome")
        self.stack.add_named(self.page_progress, "progress")
        self.stack.set_visible_child_name("welcome")

    def load_arch_logo(self):
        """Pobiera logo Arch Linux i ustawia jako ikonę"""
        logo_path = "/tmp/arch_logo_installer.svg"
        logo_url = "https://archlinux.org/static/logos/archlinux-logo-dark-scalable.518881f04ca9.svg"

        try:
            # Pobierz jeśli nie ma
            if not os.path.exists(logo_path):
                urllib.request.urlretrieve(logo_url, logo_path)

            # Wczytaj do tekstury
            texture = Gdk.Texture.new_from_file(Gio.File.new_for_path(logo_path))
            self.page_welcome.set_paintable(texture)
        except Exception as e:
            print(f"Nie udało się pobrać logo: {e}")
            # Fallback do domyślnej ikony
            self.page_welcome.set_icon_name("system-software-install-symbolic")

    def on_start_clicked(self, button):
        self.ask_password()

    def ask_password(self):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Wymagane uprawnienia",
            body="Podaj hasło administratora (sudo), aby rozpocząć instalację."
        )
        dialog.add_response("cancel", "Anuluj")
        dialog.add_response("ok", "Zatwierdź")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pwd_entry = Gtk.PasswordEntry()

        # --- NAPRAWA BŁĘDU ---
        # Zamiast set_placeholder_text używamy set_property, bo pythonowe bindingi czasem gubią metodę
        self.pwd_entry.set_property("placeholder-text", "Hasło")

        self.pwd_entry.connect("activate", lambda w: dialog.response("ok"))
        box.append(self.pwd_entry)

        dialog.set_extra_child(box)
        dialog.connect("response", self.on_password_response)
        dialog.present()

    def on_password_response(self, dialog, response):
        if response == "ok":
            pwd = self.pwd_entry.get_text()
            dialog.close()
            self.stack.set_visible_child_name("progress")
            self.lbl_status.set_text("Instalacja w toku...")

            worker = InstallWorker(pwd, self.append_log, self.on_install_finished)
            worker.start()
        else:
            dialog.close()

    def append_log(self, text):
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end_iter, text + "\n")
        adj = self.console_view.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper())

    def on_install_finished(self):
        self.lbl_status.set_text("Zakończono pomyślnie!")

class InstallerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.arch.postinstall", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = InstallerWindow(self)
        win.present()

if __name__ == "__main__":
    app = InstallerApp()
    app.run(sys.argv)
