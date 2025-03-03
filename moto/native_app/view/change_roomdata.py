import gi
from typing import Optional, List
import requests

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from view.base import BaseWindow, Colors


class ChangeRoomDataWindow(BaseWindow):
    def __init__(self, parent_window: Gtk.Window, room_id: str) -> None:
        super().__init__(parent_window, title=f"Raumangaben für Raum {room_id}")
        self.room_id = room_id
        self._init_ui()
        self._apply_styles()
        self._load_data()
        self.show_all()

    def _init_ui(self) -> None:
        """Initialize the UI components"""
        # Add back button to the header (provided by BaseWindow)
        back_button = self._create_back_button(lambda x: self.parent_window.switch_page("master_tablet"))
        self.header_box.pack_start(back_button, False, False, 0)

        # Title and subtitle
        subtitle = Gtk.Label(label="Ändern Sie bei Bedarf folgende Informationen:")
        subtitle.set_name("subheading")
        subtitle.set_halign(Gtk.Align.START)
        self.content_container.pack_start(subtitle, False, False, 10)

        # Table header
        header_grid = Gtk.Grid()
        header_grid.set_column_spacing(10)
        header_grid.set_name("header_line")

        headers = ["Kategorie", "Aktueller Wert", "Neuer Wert", ""]
        for i, header_text in enumerate(headers):
            label = Gtk.Label(label=header_text)
            label.set_name(f"header_label{i+1}")
            label.set_xalign(0)
            header_grid.attach(label, i, 0, 1, 1)

        self.content_container.pack_start(header_grid, False, False, 20)

        # Form container
        self.form_grid = Gtk.Grid()
        self.form_grid.set_name("form_grid")
        self.form_grid.set_row_spacing(30)
        self.form_grid.set_column_spacing(10)
        self.form_grid.set_margin_start(10)
        self.form_grid.set_margin_end(10)

        self.content_container.pack_start(self.form_grid, True, True, 0)

    def _create_form_row(self, row: int, label: str, current_value: str, is_dropdown: bool = False,
                         options: List[str] = None) -> None:
        """Create a form row with label, current value, input field, and a change button"""
        category_label = Gtk.Label(label=label)
        category_label.set_name("category")
        category_label.set_xalign(0)

        current_value_label = Gtk.Label(label=current_value)
        current_value_label.set_name("current")

        if is_dropdown:
            input_widget = Gtk.ComboBoxText()
            input_widget.set_name("dropdown")
            input_widget.set_hexpand(True)
            input_widget.append_text("Bitte auswählen...")
            for option in (options or []):
                input_widget.append_text(option)
            input_widget.set_active(0)
        else:
            input_widget = Gtk.Entry()
            input_widget.set_placeholder_text("Neuer Wert eingeben...")
            input_widget.set_name("inputfield")

        change_button = Gtk.Button(label="Ändern")
        change_button.set_name("change_button")

        self.form_grid.attach(category_label, 0, row, 1, 1)
        self.form_grid.attach(current_value_label, 1, row, 1, 1)
        self.form_grid.attach(input_widget, 2, row, 1, 1)
        self.form_grid.attach(change_button, 3, row, 1, 1)

    def _load_data(self) -> None:
        """Mock function to simulate data retrieval from an API"""
        # TODO: Replace with actual API calls
        supervisors = ["Max Mustermann", "Erika Musterfrau"]
        categories = ["Sport", "Kunst", "Musik"]
        current_data = {
            "supervisor": "Max Mustermann",
            "activity": "Fußball",
            "category": "Sport",
            "capacity": "20"
        }

        # Populate form with rows
        self._create_form_row(0, "Aufsichtsperson:", current_data["supervisor"], True, supervisors)
        self._create_form_row(1, "Aktivitätsname:", current_data["activity"])
        self._create_form_row(2, "AG-Kategorie:", current_data["category"], True, categories)
        self._create_form_row(3, "Maximale Kinderanzahl:", current_data["capacity"])

    def _show_help_dialog(self, button: Gtk.Button) -> None:
        """Show a help dialog explaining this screen"""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Was muss ich in diesem Anzeigefenster beachten?"
        )
        dialog.format_secondary_text(
            "In dieser Ansicht können Sie bei Bedarf die Rauminformationen ändern. "
            "Geben Sie hierzu Ihre neuen Daten in das entsprechende Eingabefeld ein. "
            "Tippen Sie auf \"Ändern\", um die neuen Daten zu speichern."
        )
        dialog.run()
        dialog.destroy()

    def _apply_styles(self) -> None:
        """Apply consistent UI styles"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #subheading {{
                font-family: "Inter", sans-serif;
                font-size: 32px;
                color: {Colors.FONT};
            }}
            
            #header_line {{
                border-bottom: 1px solid {Colors.FONT};
            }}
            
            #header_label1, #header_label2, #header_label3, #header_label4 {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                font-weight: 600;
                min-width: 250px;
                color: {Colors.FONT};
                padding: 10px;
            }}
            
            #category {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                color: {Colors.FONT};
                min-width: 200px;
            }}
            
            #dropdown {{
                font-family: "Inter", sans-serif;
                background-color: {Colors.KEYPAD_BUTTON};
                border-radius: 10px;
                font-size: 24px;
                color: {Colors.FONT};
                min-width: 180px;
            }}
            
            #current {{
                font-family: "Inter", sans-serif;
                background-color: {Colors.KEYPAD_BUTTON};
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                color: {Colors.FONT};
                min-width: 180px;
            }}
            
            #inputfield {{
                background-color: {Colors.INPUT_BG};
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                min-width: 200px;
            }}
            
            #change_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.GREEN};
                color: {Colors.FONT};
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                font-weight: 600;
                min-width: 120px;
                box-shadow: rgba(0, 0, 0, 0.2) 15px 28px 25px -18px;
            }}
            #change_button:hover {{
                box-shadow: rgba(0, 0, 0, 0.3) 2px 8px 8px -5px;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

