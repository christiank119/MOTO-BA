import gi
from typing import Optional
import logging

from view.base import BaseWindow, Colors

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class CreateActivityWindow(BaseWindow):
    """Activity creation window with specific form fields for room activities"""

    def __init__(self, parent_window: Gtk.Window, room_id: str) -> None:
        super().__init__(parent_window, title=f"Raum {room_id}")
        self.room_id = room_id

        # Form elements
        self.supervisor_dropdown = None
        self.activity_entry = None
        self.category_dropdown = None
        self.capacity_entry = None

        self._init_ui()
        self._apply_styles()

    def _init_ui(self) -> None:
        """Initialize the UI components"""
        # Back button
        back_button = self._create_back_button(self._on_back_clicked)
        self.header_box.pack_start(back_button, False, False, 0)

        # Title
        title = Gtk.Label()
        title.set_markup(f"<span size='36000'>Raum {self.room_id}</span>")
        title.set_name("big_heading")
        title.set_halign(Gtk.Align.START)
        self.content_container.pack_start(title, False, False, 0)

        # Subtitle
        subtitle = Gtk.Label(label="Geben Sie folgende Informationen an:")
        subtitle.set_name("big_subheading")
        subtitle.set_halign(Gtk.Align.START)
        self.content_container.pack_start(subtitle, False, False, 0)

        # Form container
        form_grid = Gtk.Grid()
        form_grid.set_name("form_grid")
        form_grid.set_row_spacing(30)
        form_grid.set_column_spacing(10)
        form_grid.set_margin_top(10)
        form_grid.set_margin_start(30)
        form_grid.set_margin_end(30)

        # Supervisor (Aufsichtsperson)
        supervisor_label = Gtk.Label(label="Aufsichtsperson:")
        supervisor_label.set_xalign(0)  # Align text to the left
        self.supervisor_dropdown = Gtk.ComboBoxText()
        self.supervisor_dropdown.set_hexpand(True)  # Allow it to expand in the grid
        self.supervisor_dropdown.append_text("Bitte auswählen...")
        self.supervisor_dropdown.append_text("Person 1") # TODO: Populate from API
        self.supervisor_dropdown.append_text("Person 2")
        self.supervisor_dropdown.set_active(0)  # Select the first option by default

        form_grid.attach(supervisor_label, 0, 0, 1, 1)  # Column 0, Row 0
        form_grid.attach(self.supervisor_dropdown, 1, 0, 1, 1)  # Column 1, Row 0

        # Activity name
        activity_label = Gtk.Label(label="Aktivitätsname:")
        activity_label.set_xalign(0)
        self.activity_entry = Gtk.Entry()
        self.activity_entry.set_placeholder_text("Aktivitätsname")

        form_grid.attach(activity_label, 0, 1, 1, 1)  # Column 0, Row 1
        form_grid.attach(self.activity_entry, 1, 1, 1, 1)  # Column 1, Row 1

        # Activity category
        category_label = Gtk.Label(label="AG-Kategorie:")
        category_label.set_xalign(0)
        self.category_dropdown = Gtk.ComboBoxText()
        self.category_dropdown.set_hexpand(True)
        self.category_dropdown.append_text("Bitte auswählen...")
        self.category_dropdown.append_text("Sport") # TODO: Populate from API
        self.category_dropdown.append_text("Kunst")
        self.category_dropdown.append_text("Musik")
        self.category_dropdown.set_active(0)

        form_grid.attach(category_label, 0, 2, 1, 1)  # Column 0, Row 2
        form_grid.attach(self.category_dropdown, 1, 2, 1, 1)  # Column 1, Row 2

        # Maximum participants
        capacity_label = Gtk.Label(label="Maximale Kinderanzahl:")
        capacity_label.set_xalign(0)
        self.capacity_entry = Gtk.Entry()
        self.capacity_entry.set_placeholder_text("Maximale Anzahl")

        form_grid.attach(capacity_label, 0, 3, 1, 1)  # Column 0, Row 3
        form_grid.attach(self.capacity_entry, 1, 3, 1, 1)  # Column 1, Row 3

        # Add grid to the container
        self.content_container.pack_start(form_grid, True, True, 0)

        # Submit button container
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        button_box.set_margin_start(500)
        button_box.set_margin_end(500)
        button_box.set_margin_top(0)
        self.submit_button = Gtk.Button(label="Los geht's!")
        self.submit_button.set_name("submit_button")
        self.submit_button.connect("clicked", self._on_submit)
        button_box.pack_start(self.submit_button, False, False, 0)
        self.content_container.pack_start(button_box, False, False, 0)

        # Error message area (already in BaseWindow)
        self.content_container.pack_start(self.error_label, False, False, 0)

    def _apply_styles(self) -> None:
        """Apply CSS styles for activity creation window"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #big_heading {{
                font-family: "Inter", sans-serif;
                font-size: 48px;
                font-weight: 600;
                color: {Colors.FONT};
            }}
            
            #big_subheading {{
                font-family: "Inter", sans-serif;
                font-size: 32px;
                color: {Colors.FONT};
            }}
            
            #form_grid * {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
            }}
            
            #submit_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.GREEN};
                color: {Colors.FONT};
                font-size: 26px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 10px;
                box-shadow: rgba(0, 0, 0, 0.18) 0px 2px 4px;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _on_back_clicked(self, button: Gtk.Button) -> None:
        """Handle back button click"""
        self.parent_window.switch_page("choose_room")

    def _on_submit(self, button: Gtk.Button) -> None:
        """Handle activity creation and redirect to home"""
        # Get form values
        supervisor_index = self.supervisor_dropdown.get_active()
        activity_name = self.activity_entry.get_text()
        category_index = self.category_dropdown.get_active()
        capacity = self.capacity_entry.get_text()

        # Validate form
        if supervisor_index <= 0:
            self.show_error("Bitte wählen Sie eine Aufsichtsperson aus")
            return

        if not activity_name.strip():
            self.show_error("Bitte geben Sie einen Namen für die Aktivität an")
            return

        if category_index <= 0:
            self.show_error("Bitte wählen Sie eine AG-Kategorie aus")
            return

        try:
            capacity_int = int(capacity)
            if capacity_int <= 0:
                self.show_error("Die maximale Kapazität muss größer als Null sein")
                return
        except ValueError:
            self.show_error("Bitte geben Sie die maximale Anzahl an Teilnehmern an")
            return

        # TODO: Add API call to create activity

        # After successful creation:
        self.parent_window.switch_to_home(self.room_id)

    def get_help_text(self) -> str:
        """Provide help text for activity creation screen"""
        return ("In dieser Ansicht müssen sie die unten stehenden Eingabefelder ausfüllen, "
                "um eine Aktivität im Raum zu registrieren. Für Eingaben müssen Sie auf die "
                "grauen Schaltflächen klicken. Klicken Sie auf \"Los geht's!\", um den "
                "Raum zu buchen.")