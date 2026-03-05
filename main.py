import gi
import os
import subprocess
import threading
import urllib.request

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib, Gdk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GNOME_SCRIPT = os.path.join(BASE_DIR, "gnome.sh")
KDE_SCRIPT = os.path.join(BASE_DIR, "kde.sh")
POSTER_IMAGE_PATH = os.path.join(BASE_DIR, "poster.jpg")
POSTER_URL = "https://i.imgur.com/Y9X3VQz.jpeg"

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("ArchRat")
        self.set_default_size(1000, 700)
        
        # Main layout: Box with Sidebar and Content
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_content(main_box)
        
        # --- Sidebar ---
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(250, -1)
        sidebar_box.add_css_class("background")
        main_box.append(sidebar_box)
        
        # Sidebar Header
        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_show_title(False)
        sidebar_header.set_show_start_title_buttons(False)
        sidebar_header.set_show_end_title_buttons(False)
        sidebar_box.append(sidebar_header)
        
        # Title in Sidebar Header
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        logo = Gtk.Image.new_from_icon_name("computer-symbolic")
        title_label = Gtk.Label(label="<b>ArchRat</b>", use_markup=True)
        title_box.append(logo)
        title_box.append(title_label)
        sidebar_header.set_title_widget(title_box)
        
        # Sidebar List
        self.list_box = Gtk.ListBox()
        self.list_box.add_css_class("navigation-sidebar")
        self.list_box.connect("row-activated", self.on_sidebar_row_activated)
        
        scrolled_sidebar = Gtk.ScrolledWindow()
        scrolled_sidebar.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_sidebar.set_child(self.list_box)
        scrolled_sidebar.set_hexpand(True)
        scrolled_sidebar.set_vexpand(True)
        sidebar_box.append(scrolled_sidebar)
        
        # Adding items to sidebar
        self.add_sidebar_row("GNOME", "preferences-desktop-display-symbolic", "gnome")
        self.add_sidebar_row("KDE Plasma", "preferences-desktop-theme-symbolic", "kde")
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(separator)
        
        # --- Main Content Stack ---
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_hexpand(True)
        content_box.set_vexpand(True)
        main_box.append(content_box)
        
        content_header = Adw.HeaderBar()
        content_header.set_show_end_title_buttons(True)
        content_header.set_show_start_title_buttons(False)
        content_box.append(content_header)
        
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        content_box.append(self.content_stack)
        
        # Ensure image is downloaded
        self.ensure_image_downloaded()
        
        # Add pages
        self.content_stack.add_named(self.create_page("GNOME"), "gnome")
        self.content_stack.add_named(self.create_page("KDE Plasma"), "kde")
        
        # Select first row
        row = self.list_box.get_row_at_index(0)
        if row:
            self.list_box.select_row(row)
            self.content_stack.set_visible_child_name("gnome")

    def ensure_image_downloaded(self):
        if not os.path.exists(POSTER_IMAGE_PATH):
            def download_thread():
                try:
                    urllib.request.urlretrieve(POSTER_URL, POSTER_IMAGE_PATH)
                    GLib.idle_add(self.refresh_images)
                except Exception as e:
                    print("Could not download image:", e)
            threading.Thread(target=download_thread, daemon=True).start()

    def refresh_images(self):
        # Trigger redraw by setting visible child again or recreating paths
        # This is a bit hacky, but fine for simple load.
        pass

    def add_sidebar_row(self, label_text, icon_name, obj_name):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_icon_size(Gtk.IconSize.LARGE)
        
        label = Gtk.Label(label=label_text)
        
        box.append(icon)
        box.append(label)
        row.set_child(box)
        row.obj_name = obj_name
        self.list_box.append(row)

    def on_sidebar_row_activated(self, listbox, row):
        if hasattr(row, 'obj_name'):
            self.content_stack.set_visible_child_name(row.obj_name)

    def create_page(self, desktop_name):
        # Create similar page as requested
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        
        title_label = Gtk.Label(label="<b>Wybierz Skrypt</b>", use_markup=True)
        title_label.add_css_class("title-1")
        title_label.set_margin_bottom(20)
        box.append(title_label)
        
        # Mock Carousel View
        carousel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        carousel_box.set_halign(Gtk.Align.CENTER)
        box.append(carousel_box)
        
        # Picture
        picture = Gtk.Picture()
        if os.path.exists(POSTER_IMAGE_PATH):
            picture.set_filename(POSTER_IMAGE_PATH)
        else:
            # Placeholder until downloaded
            picture.set_file(Gio.File.new_for_uri(POSTER_URL))
            
        picture.set_size_request(600, 337)
        picture.set_can_shrink(True)
        picture.set_content_fit(Gtk.ContentFit.COVER)
        
        # Wrapper to add border-radius to picture (GTK4 doesn't style GtkPicture directly well)
        frame = Gtk.Frame()
        frame.set_child(picture)
        frame.add_css_class("card")
        
        carousel_box.append(frame)
        
        # Subtitle
        subtitle = Gtk.Label(label=f"<b>Skrypt Poinstalacyjny {desktop_name}</b>", use_markup=True)
        subtitle.add_css_class("title-2")
        subtitle.set_margin_top(10)
        box.append(subtitle)
        
        # Button
        btn = Gtk.Button(label="Uruchom Skrypt")
        btn.add_css_class("suggested-action")
        btn.add_css_class("pill")
        btn.set_size_request(200, 45)
        btn.set_margin_top(10)
        btn.connect("clicked", self.on_apply_clicked, desktop_name)
        box.append(btn)
        
        return box

    def on_apply_clicked(self, button, desktop_name):
        script_to_run = GNOME_SCRIPT if desktop_name == "GNOME" else KDE_SCRIPT
        
        # Ask for password
        dialog = Adw.MessageDialog.new(self, "Wymagane uprawnienia", f"Wprowadź hasło administratora (sudo), aby zainstalować {desktop_name}.")
        
        entry = Gtk.PasswordEntry()
        entry.set_show_peek_icon(True)
        dialog.set_extra_child(entry)
        
        dialog.add_response("cancel", "Anuluj")
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "ok":
                password = entry.get_text()
                self.execute_script_with_sudo(script_to_run, password)
                
        dialog.connect("response", on_response)
        dialog.present()

    def execute_script_with_sudo(self, script_path, password):
        def run_thread():
            try:
                # Clear sudo cache
                subprocess.run(['sudo', '-k'], check=False)
                # Authenticate sudo
                p = subprocess.Popen(['sudo', '-S', '-v'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate(input=password.encode() + b'\n')
                
                if p.returncode == 0:
                    GLib.idle_add(self.show_message, "Autoryzacja udana", "Rozpoczynam instalację w nowym oknie terminala.")
                    
                    # Try different terminals
                    terminals = [
                        ['gnome-terminal', '--', 'bash', '-c'],
                        ['konsole', '-e', 'bash', '-c'],
                        ['alacritty', '-e', 'bash', '-c'],
                        ['kitty', 'bash', '-c'],
                        ['xterm', '-e', 'bash', '-c']
                    ]
                    
                    cmd = f'sudo -S bash "{script_path}"; echo "Gotowe. Naciśnij Enter aby zamknąć."; read'
                    success = False
                    
                    for term in terminals:
                        try:
                            # Test if terminal exists
                            if subprocess.run(['which', term[0]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                                spawn_cmd = term + [cmd]
                                sp = subprocess.Popen(spawn_cmd, stdin=subprocess.PIPE)
                                sp.communicate(input=password.encode() + b'\n')
                                success = True
                                break
                        except Exception:
                            pass
                            
                    if not success:
                        GLib.idle_add(self.show_message, "Błąd integracji", "Nie znaleziono obsługiwanego terminala (gnome-terminal, konsole, xterm).")
                else:
                    GLib.idle_add(self.show_message, "Błąd autoryzacji", "Nieprawidłowe hasło administratora.")
            except Exception as e:
                GLib.idle_add(self.show_message, "Błąd krytyczny", str(e))
                
        threading.Thread(target=run_thread, daemon=True).start()

    def show_message(self, title, msg):
        dialog = Adw.MessageDialog.new(self, title, msg)
        dialog.add_response("ok", "OK")
        dialog.present()


class RatApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.archrat.installer", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_startup(self):
        Adw.Application.do_startup(self)
        
        # Load CSS
        css_provider = Gtk.CssProvider()
        css = b"""
        window {
            font-family: 'Poppins', 'Inter', sans-serif;
        }
        .card {
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }
        button.pill {
            border-radius: 20px;
            padding: 8px 32px;
            font-weight: bold;
        }
        label.title-1 {
            font-size: 24pt;
        }
        label.title-2 {
            font-size: 16pt;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), 
            css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Force Dark Theme
        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = RatApp()
    app.run(None)
