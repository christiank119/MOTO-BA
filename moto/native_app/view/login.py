import gi
from typing import Optional
from enum import Enum
import requests
import logging
from urllib3.exceptions import InsecureRequestWarning
import urllib3
# Suppress only the single warning from urllib3 needed.
urllib3.disable_warnings(InsecureRequestWarning)

from view.base import BaseWindow, Colors

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class LoginState(Enum):
    """States for the login process"""
    IDLE = "idle"
    LOADING = "loading"
    ERROR = "error"
    SUCCESS = "success"

class Config:
    """Configuration settings"""
    API_BASE_URL = "https://127.0.0.1:8000/api"
    LOGIN_ENDPOINT = "/login/"
    GET_USER_ENDPOINT = "/get_user_by_id/"
    VERIFY_SSL = False  # For development only
    REQUEST_TIMEOUT = 10  # seconds

class LoginWindow(BaseWindow):
    """Login window component matching web styling and functionality"""

    def __init__(self, parent_window: Gtk.Window) -> None:
        super().__init__(parent_window, title="Login")
        self._state = LoginState.IDLE
        self._init_ui()
        self._apply_styles()

    def _init_ui(self) -> None:
        """Initialize the UI components with webapp styling"""
        # MOTO Logo
        logo_image = Gtk.Image.new_from_file("img/moto_transparent_200.png")
        logo_image.set_margin_bottom(5)
        self.content_container.pack_start(logo_image, False, False, 0)

        # Title
        title = Gtk.Label(label="Login")
        title.set_name("heading_type1")
        title.set_margin_bottom(20)
        self.content_container.pack_start(title, False, False, 0)

        # Login form
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        form_box.set_margin_start(200)
        form_box.set_margin_end(200)

        # User selection row
        user_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # User selection label
        user_label = Gtk.Label(label="Benutzername:")
        user_label.set_name("label_text")
        user_label.set_halign(Gtk.Align.START)
        user_label.set_margin_end(10)  # Add some spacing between label and dropdown
        user_row.pack_start(user_label, False, False, 0)  # False means don't expand

        # User selection dropdown
        self.user_combo = Gtk.ComboBoxText()
        self.user_combo.set_name("user_dropdown")
        # Add placeholder
        self.user_combo.append_text("Bitte auswählen...")
        self.user_combo.append_text("root") # TODO: Populate from API
        self.user_combo.append_text("Max Mustermann")
        self.user_combo.append_text("Erika Musterfrau")
        self.user_combo.set_active(0)
        user_row.pack_start(self.user_combo, True, True, 0)  # True means expand to fill space

        # Add the row to the form box
        form_box.pack_start(user_row, False, False, 0)

        self.content_container.pack_start(form_box, False, False, 0)

        # Continue button
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        button_box.set_margin_start(450)
        button_box.set_margin_end(450)
        button_box.set_margin_top(20)
        self.continue_button = Gtk.Button(label="Weiter")
        self.continue_button.set_name("login_button")
        self.continue_button.set_size_request(100, 50)
        self.continue_button.connect("clicked", self._handle_continue)
        button_box.pack_start(self.continue_button, False, False, 0)

        self.content_container.pack_start(button_box, False, False, 0)

        # Add error label to content (already created in BaseWindow)
        self.content_container.pack_start(self.error_label, False, False, 0)

    def _apply_styles(self) -> None:
        """Apply CSS styles to match web version"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #heading_type1 {{
                font-family: "Inter", sans-serif;
                font-size: 50px;
                font-weight: bold;
                color: {Colors.FONT};
            }}
            
            #label_text {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                color: {Colors.FONT};
            }}
            
            #user_dropdown {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                padding: 8px;
                border-radius: 10px;
                color: {Colors.FONT};
                margin: 5px 0;
            }}
            
            #login_button {{
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

    def _handle_continue(self, button: Gtk.Button) -> None:
        """Handle continue button click to proceed to PIN entry"""
        if self._state == LoginState.LOADING:
            return

        # Get selected user
        active_index = self.user_combo.get_active()
        if active_index <= 0:  # First item is "Please select..."
            self.show_error("Bitte wählen Sie einen Benutzer aus")
            return

        # Store the selected username in the parent window for the PIN entry view
        selected_user = self.user_combo.get_active_text()
        self.parent_window.selected_username = selected_user

        # Switch to PIN entry view
        self.parent_window.switch_page("pin_entry")
    def get_help_text(self) -> str:
        """Provide help text for login screen"""
        return ("Hier können Sie sich mit Ihrem Nutzerkonto anmelden. "
                "Wählen Sie zuerst Ihren Benutzernamen aus der Liste aus und klicken Sie dann auf \"Weiter\".")