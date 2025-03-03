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

class PinState(Enum):
    """States for the PIN entry process"""
    IDLE = "idle"
    LOADING = "loading"
    ERROR = "error"
    SUCCESS = "success"

class Config:
    """Configuration settings"""
    API_BASE_URL = "https://127.0.0.1:8000/api"
    LOGIN_ENDPOINT = "/login/"
    VERIFY_SSL = False  # For development only
    REQUEST_TIMEOUT = 10  # seconds

class PinEntryWindow(BaseWindow):
    """PIN entry window for login authentication"""

    def __init__(self, parent_window: Gtk.Window) -> None:
        super().__init__(parent_window, title="PIN-Eingabe")
        self._state = PinState.IDLE
        self.pin_value = ""  # Store the PIN
        self.username_display = None
        self._init_ui()
        self._apply_styles()

    def _init_ui(self) -> None:
        """Initialize the UI components"""
        # Back button
        back_button = self._create_back_button(self._go_back)
        self.header_box.pack_start(back_button, False, False, 0)

        # MOTO logo but with a smaller size
        logo_image = Gtk.Image.new_from_file("img/moto_transparent_200.png")
        logo_image.set_pixel_size(80)  # Make the logo smaller than original
        logo_image.set_margin_bottom(2)  # Minimal margin
        self.content_container.pack_start(logo_image, False, False, 0)

        # Title
        #title_label = Gtk.Label(label="PIN-Eingabe")
        #title_label.set_name("heading_type1")
        #title_label.set_margin_bottom(2)
        #self.content_container.pack_start(title_label, False, False, 0)

        # User info
        self.username_display = Gtk.Label()
        self.username_display.set_name("username_display")
        self.username_display.set_margin_bottom(3)
        self.content_container.pack_start(self.username_display, False, False, 0)

        # Update with selected username when the widget is mapped
        self.connect("map", lambda w: self._update_username_display())

        # PIN form with balanced margins
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        form_box.set_margin_start(160)
        form_box.set_margin_end(160)
        form_box.set_margin_top(2)

        # PIN entry field - horizontal layout
        pin_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pin_box.set_halign(Gtk.Align.CENTER)
        pin_box.set_margin_start(35)
        pin_box.set_margin_end(35)

        # pin_label = Gtk.Label(label="PIN:")
        # pin_label.set_name("label_text")
        # pin_label.set_halign(Gtk.Align.START)
        # pin_label.set_margin_end(10)
        # pin_box.pack_start(pin_label, False, False, 0)

        self.pin_entry = Gtk.Entry()
        self.pin_entry.set_name("pin_entry")
        self.pin_entry.set_visibility(False)  # Hide PIN (show dots)
        self.pin_entry.set_editable(False)  # Not directly editable
        self.pin_entry.set_can_focus(False)  # Cannot be focused
        self.pin_entry.set_alignment(0.5)  # Center align text
        self.pin_entry.set_hexpand(True)  # Allow entry to expand horizontally
        # Make the width match the keypad width (3 buttons at 75px each + 2 spacings at 12px each)
        self.pin_entry.set_size_request(249, -1)  # 3*75 + 2*12 = 249px
        pin_box.pack_start(self.pin_entry, True, True, 0)

        form_box.pack_start(pin_box, False, False, 0)

        # Numeric keypad
        keypad_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        keypad_container.set_margin_top(5)
        keypad_container.set_halign(Gtk.Align.CENTER)
        keypad_container.set_hexpand(True)

        # Create the keypad grid (3x4)
        keypad = Gtk.Grid()
        keypad.set_row_spacing(10)
        keypad.set_column_spacing(12)
        keypad.set_halign(Gtk.Align.CENTER)
        keypad.set_margin_start(35)
        keypad.set_margin_end(35)

        # Add number buttons (1-9)
        for i in range(3):
            for j in range(3):
                num = i * 3 + j + 1
                button = Gtk.Button(label=str(num))
                button.set_name("keypad_button")
                button.connect("clicked", self._on_keypad_button_clicked, str(num))
                keypad.attach(button, j, i, 1, 1)

        # Add 0 button at the bottom center
        button_0 = Gtk.Button(label="0")
        button_0.set_name("keypad_button")
        button_0.connect("clicked", self._on_keypad_button_clicked, "0")
        keypad.attach(button_0, 1, 3, 1, 1)

        # Add clear button at bottom left
        clear_button = Gtk.Button(label="C")
        clear_button.set_name("clear_button")
        clear_button.connect("clicked", self._on_clear_clicked)
        keypad.attach(clear_button, 0, 3, 1, 1)

        # Add backspace button at bottom right
        backspace_button = Gtk.Button(label="←")
        backspace_button.set_name("backspace_button")
        backspace_button.connect("clicked", self._on_backspace_clicked)
        keypad.attach(backspace_button, 2, 3, 1, 1)

        keypad_container.pack_start(keypad, False, False, 0)
        form_box.pack_start(keypad_container, False, False, 0)

        self.content_container.pack_start(form_box, False, False, 0)

        # Error message is already in BaseWindow
        self.content_container.pack_start(self.error_label, False, False, 0)

        # Connect PIN entry to auto-login when 4 digits are entered
        self.connect("draw", self._check_pin_length)

    def _update_username_display(self) -> None:
        """Update the username display with the selected username"""
        if hasattr(self.parent_window, 'selected_username'):
            self.username_display.set_text(f"{self.parent_window.selected_username}")
        else:
            self.username_display.set_text("")

    def _check_pin_length(self, widget, ctx):
        """Check if PIN has reached desired length and trigger login"""
        if len(self.pin_value) == 4 and self._state != PinState.LOADING:
            GLib.idle_add(self._handle_login)
        return False

    def _on_keypad_button_clicked(self, button: Gtk.Button, value: str) -> None:
        """Handle keypad button click and update PIN"""
        # Limit PIN to 4 digits
        if len(self.pin_value) < 4:
            self.pin_value += value
            self.pin_entry.set_text("*" * len(self.pin_value))

            # Auto-login when PIN reaches 4 digits
            if len(self.pin_value) == 4:
                GLib.timeout_add(300, self._handle_login)  # Small delay for better UX

    def _on_clear_clicked(self, button: Gtk.Button) -> None:
        """Clear the PIN value"""
        self.pin_value = ""
        self.pin_entry.set_text("")

    def _on_backspace_clicked(self, button: Gtk.Button) -> None:
        """Remove the last digit from PIN"""
        if self.pin_value:
            self.pin_value = self.pin_value[:-1]
            self.pin_entry.set_text("*" * len(self.pin_value))

    def _go_back(self, button: Gtk.Button) -> None:
        """Go back to the login screen"""
        self.parent_window.switch_page("login")

    def _apply_styles(self) -> None:
        """Apply CSS styles to match web version"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #heading_type1 {{
                font-family: "Inter", sans-serif;
                font-size: 32px;
                font-weight: bold;
                color: {Colors.FONT};
                margin: 0;
                padding: 0;
            }}
            
            #username_display {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                font-weight: bold;
                color: {Colors.FONT};
                margin: 0;
                padding: 0;
            }}
            
            #label_text {{
                font-family: "Inter", sans-serif;
                font-size: 18px;
                color: {Colors.FONT};
                margin: 0;
                padding: 0;
            }}
            
            #pin_entry {{
                font-family: "Inter", sans-serif;
                font-size: 22px;
                padding: 4px;
                border-radius: 8px;
                background: {Colors.INPUT_BG};
                color: {Colors.FONT};
                margin: 2px 0;
                letter-spacing: 6px;
            }}
            
            #keypad_button {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                font-weight: bold;
                background: {Colors.KEYPAD_BUTTON};
                color: {Colors.FONT};
                border-radius: 7px;
                padding: 4px 16px;
                min-width: 75px;
                min-height: 45px;
            }}
            
            #clear_button {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                font-weight: bold;
                background: {Colors.ERROR};
                color: white;
                border-radius: 7px;
                padding: 4px 16px;
                min-width: 75px;
                min-height: 45px;
            }}
            
            #backspace_button {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                font-weight: bold;
                background: {Colors.KEYPAD_BUTTON};
                color: {Colors.FONT};
                border-radius: 7px;
                padding: 4px 16px;
                min-width: 75px;
                min-height: 45px;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _handle_login(self) -> None:
        """Handle login with username and PIN"""
        if self._state == PinState.LOADING:
            return False

        if not hasattr(self.parent_window, 'selected_username'):
            self.show_error("Kein Benutzer ausgewählt")
            return False

        if len(self.pin_value) < 4:
            self.show_error("Bitte geben Sie eine 4-stellige PIN ein")
            return False

        username = self.parent_window.selected_username
        pin = self.pin_value

        self._set_loading_state(True)

        try:
            # For the prototype, hardcode root/root
            response = requests.post(
                f"{Config.API_BASE_URL}{Config.LOGIN_ENDPOINT}",
                json={
                    "username": "root",  # Hardcoded for prototype
                    "password": "root",  # Hardcoded for prototype
                    "device_id": self.parent_window.get_device_id()
                },
                verify=Config.VERIFY_SSL,
                timeout=Config.REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                self.parent_window.set_auth_tokens(
                    access_token=data["access"],
                    refresh_token=data["refresh"]
                )
                self._handle_successful_login()
            else:
                self.show_error("PIN ist nicht korrekt")
                self.pin_value = ""
                self.pin_entry.set_text("")
        except requests.RequestException as e:
            self.logger.error(f"Login failed: {str(e)}")
            self.show_error("Verbindungsfehler")
        finally:
            self._set_loading_state(False)

        return False  # For GLib.timeout_add

    def _handle_successful_login(self) -> None:
        """Handle successful login and navigate to next screen"""
        self.error_label.set_text("")
        self._state = PinState.SUCCESS

        # Navigate to room selection after successful login
        GLib.timeout_add(500, self.parent_window.switch_page, "set_merged_room")

    def _set_loading_state(self, is_loading: bool) -> None:
        """Update UI for loading state"""
        self._state = PinState.LOADING if is_loading else PinState.IDLE

    def get_help_text(self) -> str:
        """Provide help text for PIN entry screen"""
        return ("Geben Sie Ihre vierstellige PIN ein, um sich anzumelden. "
                "Die Anmeldung erfolgt automatisch, sobald alle vier Ziffern eingegeben wurden.")