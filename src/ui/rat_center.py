import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

class RatCenterWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Rat Center")
        self.set_default_size(1000, 700)

        # Ustawienie ciemnego schematu kolorów
        manager = Adw.StyleManager.get_default()
        manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        # NavigationSplitView
        split_view = Adw.NavigationSplitView()
        split_view.set_vexpand(True)
        split_view.set_hexpand(True)

        # --- Panel boczny ---
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(250, -1)

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        sidebar_box.append(header)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.add_css_class("navigation-sidebar")

        categories = [
            ("ratinstall", "RatInstall", "system-software-install-symbolic"),
            ("ratpkg", "RatPkg", "package-x-generic-symbolic"),
            ("ratupdater", "Rat Updater", "software-update-available-symbolic"),
            ("sysinfo", "Informacje o systemie", "computer-symbolic"),
        ]

        for cat_id, name, icon_name in categories:
            row = Adw.ActionRow()
            row.set_title(name)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            row.add_prefix(icon)
            row.set_activatable(True)
            row.set_name(cat_id)
            listbox.append(row)

        listbox.connect("row-selected", self.on_category_selected)
        sidebar_box.append(listbox)

        # Opakowanie panelu bocznego w NavigationPage
        sidebar_page = Adw.NavigationPage.new(sidebar_box, "Kategorie")
        split_view.set_sidebar(sidebar_page)

        # --- Widok główny ---
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.content_stack.set_vexpand(True)
        self.content_stack.set_hexpand(True)

        # Tworzymy strony dla każdej kategorii (jako NavigationPage)
        for cat_id, name, icon_name in categories:
            page_content = Adw.StatusPage()
            page_content.set_title(name)
            page_content.set_icon_name(icon_name)
            page_content.set_description(f"To jest strona {name}. Tutaj pojawi się właściwa zawartość.")
            # Dodajemy do stosu
            self.content_stack.add_named(page_content, cat_id)

        # Opakowanie stosu w NavigationPage dla widoku głównego
        content_page = Adw.NavigationPage.new(self.content_stack, "Zawartość")
        split_view.set_content(content_page)

        self.set_content(split_view)

        # Zaznacz pierwszą kategorię
        first_row = listbox.get_row_at_index(0)
        if first_row:
            listbox.select_row(first_row)

    def on_category_selected(self, listbox, row):
        if row is None:
            return
        cat_id = row.get_name()
        self.content_stack.set_visible_child_name(cat_id)

def run():
    app = Adw.Application(application_id="com.rat.center")
    app.connect('activate', lambda a: RatCenterWindow(a).present())
    app.run(sys.argv)

if __name__ == "__main__":
    run()
