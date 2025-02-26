import gi
from typing import Optional
from enum import Enum
import requests
import logging
from urllib3.exceptions import InsecureRequestWarning
import urllib3
# Suppress only the single warning from urllib3 needed.
urllib3.disable_warnings(InsecureRequestWarning)

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class PinState(Enum):
    """States for the PIN entry process"""
    IDLE = "idle"
    LOADING = "loading"
    ERROR = "error"
    SUCCESS = "success"

class Colors:
    """Color constants from CSS"""
    BACKGROUND = "#f6f4f3"
    FONT = "#1b2021"
    ERROR = "#ff3130"
    HELP_BUTTON = "#ffffff"
    INPUT_BG = "rgba(217, 217, 217, 0.5)"
    GREEN = "#83cd2d"
    KEYPAD_BUTTON = "rgba(217, 217, 217, 0.75)"

class Config:
    """Configuration settings"""
    API_BASE_URL = "https://127.0.0.1:8000/api"
    LOGIN_ENDPOINT = "/login/"
    VERIFY_SSL = False  # For development only
    REQUEST_TIMEOUT = 10  # seconds

class PinEntryWindow(Gtk.Box):
    """PIN entry window for login authentication"""

    def __init__(self, parent_window: Gtk.Window) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)  # Reduced spacing further
        self.parent_window = parent_window
        self._state = PinState.IDLE
        self._setup_logging()
        self.pin_value = ""  # Store the PIN
        self._init_ui()
        self._apply_styles()

    def _setup_logging(self) -> None:
        """Initialize logging configuration"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def _init_ui(self) -> None:
        """Initialize the UI components with webapp styling"""

        # Create a Fixed container to position items absolutely
        fixed_container = Gtk.Fixed()
        fixed_container.set_size_request(1280, 720)  # Set the desired size for the login window

        # Create the background image
        background_image = Gtk.Image.new_from_file("img/colors.png")
        background_image.set_halign(Gtk.Align.CENTER)
        background_image.set_valign(Gtk.Align.CENTER)

        # Position the background image in the fixed container (0,0 is top-left corner)
        fixed_container.put(background_image, 0, 0)

        # Create the content container for the PIN form - reduced margins
        content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)  # Reduced spacing further
        content_container.set_size_request(1217, 660)
        content_container.set_hexpand(True)
        content_container.set_vexpand(True)
        content_container.set_margin_top(30)  # Reduced further
        content_container.set_margin_bottom(30)  # Reduced further
        content_container.set_margin_start(30)
        content_container.set_margin_end(30)
        content_container.set_name("content_container")

        # Add the form components into the content container
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_bottom(2)  # Reduced further

        # Back button
        back_button = Gtk.Button(label="← Zurück")
        back_button.set_name("help_button")
        back_button.connect("clicked", self._go_back)
        header.pack_start(back_button, False, False, 0)

        help_button = self._create_help_button()
        header.pack_end(help_button, False, False, 0)
        content_container.pack_start(header, False, False, 0)

        # Re-adding the MOTO logo but with a smaller size
        logo_image = Gtk.Image.new_from_file("img/moto_transparent_200.png")
        logo_image.set_pixel_size(80)  # Make the logo smaller than original
        logo_image.set_margin_bottom(2)  # Minimal margin
        content_container.pack_start(logo_image, False, False, 0)

        # Title with username - made smaller
        self.title_label = Gtk.Label(label="PIN-Eingabe")
        self.title_label.set_name("heading_type1")
        self.title_label.set_margin_bottom(2)  # Reduced further
        content_container.pack_start(self.title_label, False, False, 0)

        # User info
        username_display = Gtk.Label()
        username_display.set_name("username_display")
        username_display.set_margin_bottom(3)  # Reduced margin further
        content_container.pack_start(username_display, False, False, 0)

        # Update with selected username when the widget is mapped
        self.connect("map", lambda w: self._update_username_display(username_display))

        # PIN form - balanced margins
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        form_box.set_margin_start(160)  # Middle ground between 200 and 120
        form_box.set_margin_end(160)    # Middle ground between 200 and 120
        form_box.set_margin_top(2)

        # PIN entry field - horizontal layout
        pin_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)  # Changed to horizontal

        pin_label = Gtk.Label(label="PIN:")
        pin_label.set_name("label_text")
        pin_label.set_halign(Gtk.Align.START)
        pin_label.set_margin_end(10)  # Add some spacing between label and entry
        pin_box.pack_start(pin_label, False, False, 0)

        self.pin_entry = Gtk.Entry()
        self.pin_entry.set_name("pin_entry")
        self.pin_entry.set_visibility(False)  # Hide PIN (show dots)
        self.pin_entry.set_editable(False)  # Not directly editable
        self.pin_entry.set_can_focus(False)  # Cannot be focused
        self.pin_entry.set_alignment(0.5)  # Center align text
        self.pin_entry.set_hexpand(True)  # Allow entry to expand horizontally
        pin_box.pack_start(self.pin_entry, True, True, 0)  # Changed to expand to fill space

        form_box.pack_start(pin_box, False, False, 0)

        # Numeric keypad - balanced size
        keypad_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        keypad_container.set_margin_top(5)
        keypad_container.set_halign(Gtk.Align.CENTER)
        keypad_container.set_hexpand(True)  # Allow container to expand horizontally

        # Create the keypad grid (3x4)
        keypad = Gtk.Grid()
        keypad.set_row_spacing(10)  # Middle ground spacing between rows
        keypad.set_column_spacing(12)  # Middle ground spacing between columns
        keypad.set_halign(Gtk.Align.CENTER)
        keypad.set_margin_start(35)  # Middle ground margins
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

        content_container.pack_start(form_box, False, False, 0)

        # Error message area
        self.error_label = Gtk.Label()
        self.error_label.set_name("error_label")
        self.error_label.set_margin_top(5)  # Reduced further
        content_container.pack_start(self.error_label, False, False, 0)

        # Position the content container on top of the background image
        fixed_container.put(content_container, 0, 0)

        # Add the whole fixed container to the parent window
        self.add(fixed_container)

        # Connect PIN entry to auto-login when 4 digits are entered
        self.connect("draw", self._check_pin_length)

    def _update_username_display(self, label: Gtk.Label) -> None:
        """Update the username display with the selected username"""
        if hasattr(self.parent_window, 'selected_username'):
            label.set_text(f"für Benutzer: {self.parent_window.selected_username}")
        else:
            label.set_text("")

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

    def _create_help_button(self) -> Gtk.Button:
        """Create help button matching web styling"""
        button = Gtk.Button(label="HILFE")
        button.set_name("help_button")
        button.connect("clicked", self._show_help_dialog)
        return button

    def _go_back(self, button: Gtk.Button) -> None:
        """Go back to the login screen"""
        self.parent_window.switch_page("login")

    def _apply_styles(self) -> None:
        """Apply CSS styles to match web version"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #content_container {{
            background-color: white;
            border-radius: 25px;
            box-shadow: rgba(0, 0, 0, 0.2) 0px 10px 15px;
            padding: 10px 10px 10px 10px;
            }}
            
            #heading_type1 {{
                font-family: "Inter", sans-serif;
                font-size: 32px;  /* Reduced further */
                font-weight: bold;
                color: {Colors.FONT};
                margin: 0;
                padding: 0;
            }}
            
            #username_display {{
                font-family: "Inter", sans-serif;
                font-size: 18px;  /* Reduced further */
                color: {Colors.FONT};
                margin: 0;
                padding: 0;
            }}
            
            #label_text {{
                font-family: "Inter", sans-serif;
                font-size: 18px;  /* Reduced further */
                color: {Colors.FONT};
                margin: 0;
                padding: 0;
            }}
            
            #pin_entry {{
                font-family: "Inter", sans-serif;
                font-size: 22px;  /* Reduced further */
                padding: 4px;  /* Reduced further */
                border-radius: 8px;
                background: {Colors.INPUT_BG};
                color: {Colors.FONT};
                margin: 2px 0;  /* Reduced further */
                letter-spacing: 6px;
            }}
            
            /* Middle ground button size between previous versions */
            #keypad_button {{
                font-family: "Inter", sans-serif;
                font-size: 24px;    /* Middle ground between 22px and 26px */
                font-weight: bold;
                background: {Colors.KEYPAD_BUTTON};
                color: {Colors.FONT};
                border-radius: 7px;  /* Middle ground between 6px and 8px */
                padding: 8px 16px;   /* Middle ground between previous padding values */
                min-width: 75px;     /* Middle ground between 60px and 90px */
                min-height: 48px;    /* Middle ground between 50px and 65px */
            }}
            
            #clear_button {{
                font-family: "Inter", sans-serif;
                font-size: 24px;    /* Middle ground between 22px and 26px */
                font-weight: bold;
                background: {Colors.ERROR};
                color: white;
                border-radius: 7px;  /* Middle ground between 6px and 8px */
                padding: 8px 16px;   /* Middle ground between previous padding values */
                min-width: 75px;     /* Middle ground between 60px and 90px */
                min-height: 48px;    /* Middle ground between 50px and 65px */
            }}
            
            #backspace_button {{
                font-family: "Inter", sans-serif;
                font-size: 24px;    /* Middle ground between 22px and 26px */
                font-weight: bold;
                background: {Colors.KEYPAD_BUTTON};
                color: {Colors.FONT};
                border-radius: 7px;  /* Middle ground between 6px and 8px */
                padding: 8px 16px;   /* Middle ground between previous padding values */
                min-width: 75px;     /* Middle ground between 60px and 90px */
                min-height: 48px;    /* Middle ground between 50px and 65px */
            }}
            
            #help_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.HELP_BUTTON};
                color: {Colors.FONT};
                border: 1px solid {Colors.FONT};  /* Reduced from 2px */
                border-radius: 30px;  /* Reduced further */
                padding: 4px 12px;  /* Reduced further */
                font-size: 14px;  /* Reduced further */
                box-shadow: rgba(0, 0, 0, 0.18) 0px 1px 2px;  /* Reduced shadow */
            }}
            
            #error_label {{
                font-family: "Inter", sans-serif;
                color: {Colors.ERROR};
                font-size: 14px;  /* Reduced further */
                font-weight: 500;
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
            self._show_error("Kein Benutzer ausgewählt")
            return False

        if len(self.pin_value) < 4:
            self._show_error("Bitte geben Sie eine 4-stellige PIN ein")
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
                self._show_error("PIN ist nicht korrekt")
                self.pin_value = ""
                self.pin_entry.set_text("")
        except requests.RequestException as e:
            self.logger.error(f"Login failed: {str(e)}")
            self._show_error("Verbindungsfehler")
        finally:
            self._set_loading_state(False)

        return False  # For GLib.timeout_add

    def _handle_successful_login(self) -> None:
        """Handle successful login and navigate to next screen"""
        self.error_label.set_text("")
        self._state = PinState.SUCCESS

        # Navigate to room selection after successful login
        GLib.timeout_add(500, self.parent_window.switch_page, "choose_room")

    def _show_error(self, message: str) -> None:
        """Display error message"""
        self.error_label.set_text(message)
        self._state = PinState.ERROR

    def _set_loading_state(self, is_loading: bool) -> None:
        """Update UI for loading state"""
        self._state = PinState.LOADING if is_loading else PinState.IDLE

    def _show_help_dialog(self, button: Gtk.Button) -> None:
        """Show help dialog matching web version"""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Was muss ich in diesem Anzeigefenster beachten?"
        )
        dialog.format_secondary_text(
            "Geben Sie Ihre vierstellige PIN ein, um sich anzumelden. "
            "Die Anmeldung erfolgt automatisch, sobald alle vier Ziffern eingegeben wurden."
        )
        dialog.run()
        dialog.destroy()