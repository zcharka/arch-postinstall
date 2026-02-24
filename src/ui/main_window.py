import sys
import os
import subprocess
import threading
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

# --- 1. CONFIG: LOGIKA INSTALACJI (BACKEND) ---
# Tutaj trzymamy logikę, którą ustaliliśmy wcześniej (pomijanie pakietów, yay auto-answer)

class InstallWorker(threading.Thread):
    def __init__(self, password, on_log, on_finish):
        super().__init__()
        self.password = password
        self.on_log = on_log       # Funkcja do aktualizacji tekstu w UI
        self.on_finish = on_finish # Funkcja wywoływana po zakończeniu
        self.daemon = True

    def log(self, text):
        # GTK nie jest "thread-safe", aktualizacje UI muszą iść przez GLib.idle_add
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
            full_cmd = command.split() # subprocess woli listę, chyba że shell=True

        self.log(f"\n➜ {command}")

        try:
            # Uruchamiamy proces
            process = subprocess.Popen(
                full_cmd,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Czytanie wyjścia linia po linii
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
        # Przykładowa sekwencja (możesz tu zaimportować swoje moduły src.postinstall)

        self.log(">> Aktualizacja repozytoriów...")
        self.run_cmd("sudo pacman -Sy")

        self.log(">> Instalacja Gita i podstaw...")
        self.run_cmd("sudo pacman -S git base-devel")

        # Tutaj wstaw wywołanie swoich skryptów Plasmy, jeśli chcesz
        # self.run_cmd("yay -S kwin-effects-better-blur-dx-git")

        self.log(">> Instalacja zakończona!")
        GLib.idle_add(self.on_finish)


# --- 2. UI: WYGLĄD LINEXIN (LIBADWAITA) ---

class InstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Arch Setup")
        self.set_default_size(800, 600)

        # Główny kontener widoków (ViewStack pozwala przełączać ekrany)
        self.stack = Adw.ViewStack()

        # Pasek tytułowy (zintegrowany z oknem)
        self.header = Adw.HeaderBar()

        # Główny layout: Pasek na górze, reszta pod spodem
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.header)
        main_box.append(self.stack)
        self.set_content(main_box)

        # --- EKRAN 1: POWITANIE (StatusPage) ---
        self.page_welcome = Adw.StatusPage()
        self.page_welcome.set_icon_name("system-software-install-symbolic") # Ikona systemowa
        self.page_welcome.set_title("Instalator Systemu")
        self.page_welcome.set_description("Skonfiguruj swój system Arch Linux jednym kliknięciem.\nZainstalowane zostaną motywy, ikony i poprawki.")

        # Przycisk "Rozpocznij" (Pill button)
        self.btn_start = Gtk.Button(label="Rozpocznij instalację")
        self.btn_start.add_css_class("pill")     # Zaokrąglony kształt
        self.btn_start.add_css_class("suggested-action") # Niebieski/Akcentowy kolor
        self.btn_start.set_size_request(200, 50) # Duży przycisk
        self.btn_start.set_halign(Gtk.Align.CENTER)
        self.btn_start.connect("clicked", self.on_start_clicked)

        # Dodajemy przycisk do strony powitalnej
        self.page_welcome.set_child(self.btn_start)

        # --- EKRAN 2: KONSOLA (Postęp) ---
        self.page_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.page_progress.set_margin_top(20)
        self.page_progress.set_margin_bottom(20)
        self.page_progress.set_margin_start(20)
        self.page_progress.set_margin_end(20)

        # Pole tekstowe (logi)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True) # Rozciągnij na całe okno
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.console_view = Gtk.TextView()
        self.console_view.set_editable(False)
        self.console_view.set_monospace(True)
        self.console_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.console_view.add_css_class("card") # Wygląd karty

        # Buffer przechowuje tekst
        self.text_buffer = self.console_view.get_buffer()

        scrolled.set_child(self.console_view)

        # Etykieta statusu
        self.lbl_status = Gtk.Label(label="Przygotowywanie...")
        self.lbl_status.add_css_class("title-4")

        self.page_progress.append(self.lbl_status)
        self.page_progress.append(scrolled)

        # Dodanie ekranów do stosu
        self.stack.add_named(self.page_welcome, "welcome")
        self.stack.add_named(self.page_progress, "progress")

        self.stack.set_visible_child_name("welcome")

    def on_start_clicked(self, button):
        # Zapytaj o hasło w ładnym oknie
        self.ask_password()

    def ask_password(self):
        # Tworzymy dialog (okienko)
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Wymagane uprawnienia",
            body="Podaj hasło administratora (sudo), aby rozpocząć instalację."
        )
        dialog.add_response("cancel", "Anuluj")
        dialog.add_response("ok", "Zatwierdź")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)

        # Pole hasła w środku dialogu
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.pwd_entry = Gtk.PasswordEntry()
        self.pwd_entry.set_placeholder_text("Hasło")
        self.pwd_entry.connect("activate", lambda w: dialog.response("ok")) # Enter zatwierdza
        box.append(self.pwd_entry)

        dialog.set_extra_child(box)
        dialog.connect("response", self.on_password_response)
        dialog.present()

    def on_password_response(self, dialog, response):
        if response == "ok":
            pwd = self.pwd_entry.get_text()
            dialog.close()
            # Przełącz na ekran konsoli i uruchom worker
            self.stack.set_visible_child_name("progress")
            self.lbl_status.set_text("Instalacja w toku...")

            worker = InstallWorker(pwd, self.append_log, self.on_install_finished)
            worker.start()
        else:
            dialog.close()

    def append_log(self, text):
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end_iter, text + "\n")
        # Auto-scroll na dół
        adj = self.console_view.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper())

    def on_install_finished(self):
        self.lbl_status.set_text("Zakończono pomyślnie!")
        # Można tu dodać przycisk "Zamknij" lub "Restart"

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
