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

class LoginState(Enum):
    """States for the login process"""
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

class Config:
    """Configuration settings"""
    API_BASE_URL = "https://127.0.0.1:8000/api"
    LOGIN_ENDPOINT = "/login/"
    GET_USER_ENDPOINT = "/get_user_by_id/"
    VERIFY_SSL = False  # For development only
    REQUEST_TIMEOUT = 10  # seconds

class LoginWindow(Gtk.Box):
    """Login window component matching web styling and functionality"""

    def __init__(self, parent_window: Gtk.Window) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.parent_window = parent_window
        self._state = LoginState.IDLE
        self._setup_logging()
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
        background_image = Gtk.Image.new_from_file("img/colors.png")  # Update path to your background image
        background_image.set_halign(Gtk.Align.CENTER)
        background_image.set_valign(Gtk.Align.CENTER)

        # Position the background image in the fixed container (0,0 is top-left corner)
        fixed_container.put(background_image, 0, 0)

        # Create the content container for the login form
        content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_container.set_size_request(1217, 660)
        content_container.set_hexpand(True)
        content_container.set_vexpand(True)
        content_container.set_margin_top(30)
        content_container.set_margin_bottom(30)
        content_container.set_margin_start(30)
        content_container.set_margin_end(30)
        content_container.set_name("content_container")

        # Add the form components into the content container
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_bottom(20)
        help_button = self._create_help_button()
        header.pack_end(help_button, False, False, 0)
        content_container.pack_start(header, False, False, 0)

        # MOTO Logo
        logo_image = Gtk.Image.new_from_file("img/moto_transparent_200.png")
        logo_image.set_margin_bottom(5)
        content_container.pack_start(logo_image, False, False, 0)

        # Title
        title = Gtk.Label(label="Login")
        title.set_name("heading_type1")
        title.set_margin_bottom(20)
        content_container.pack_start(title, False, False, 0)

        # Login form
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        form_box.set_margin_start(200)
        form_box.set_margin_end(200)

        # User selection label
        user_label = Gtk.Label(label="Benutzername")
        user_label.set_name("label_text")
        user_label.set_halign(Gtk.Align.START)
        form_box.pack_start(user_label, False, False, 0)

        # Create a horizontal box for the dropdown and button
        horizontal_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # User selection dropdown
        self.user_combo = Gtk.ComboBoxText()
        self.user_combo.set_name("user_dropdown")
        # Add placeholder
        self.user_combo.append_text("Bitte auswählen...")
        # Add users - these would come from an API in a real implementation
        self.user_combo.append_text("root")
        self.user_combo.append_text("Max Mustermann")
        self.user_combo.append_text("Erika Musterfrau")
        self.user_combo.set_active(0)
        horizontal_box.pack_start(self.user_combo, True, True, 0)  # Set expand to True to fill available space

        # Continue button - now on the same line as the dropdown
        self.continue_button = Gtk.Button(label="Weiter")
        self.continue_button.set_name("login_button")
        self.continue_button.connect("clicked", self._handle_continue)
        horizontal_box.pack_end(self.continue_button, False, False, 0)  # False for expand to keep natural size

        # Add the horizontal box to the form box
        form_box.pack_start(horizontal_box, False, False, 0)

        content_container.pack_start(form_box, False, False, 0)

        # Error message area
        self.error_label = Gtk.Label()
        self.error_label.set_name("error_label")
        self.error_label.set_margin_top(20)
        content_container.pack_start(self.error_label, False, False, 0)

        # Position the content container on top of the background image
        fixed_container.put(content_container, 0, 0)

        # Add the whole fixed container to the parent window
        self.add(fixed_container)

    def _create_help_button(self) -> Gtk.Button:
        """Create help button matching web styling"""
        button = Gtk.Button(label="HILFE")
        button.set_name("help_button")
        button.connect("clicked", self._show_help_dialog)
        return button

    def _apply_styles(self) -> None:
        """Apply CSS styles to match web version"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #content_container {{
            background-color: white;
            border-radius: 25px;
            box-shadow: rgba(0, 0, 0, 0.2) 0px 10px 15px;
            padding: 20px 20px 20px 20px;
            }}
            
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
                background: {Colors.INPUT_BG};
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
            
            #help_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.HELP_BUTTON};
                color: {Colors.FONT};
                border: 2px solid {Colors.FONT};
                border-radius: 45px;
                padding: 10px 25px;
                font-size: 20px;
                box-shadow: rgba(0, 0, 0, 0.18) 0px 2px 4px;
            }}
            
            #error_label {{
                font-family: "Inter", sans-serif;
                color: {Colors.ERROR};
                font-size: 18px;
                font-weight: 500;
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
            self._show_error("Bitte wählen Sie einen Benutzer aus")
            return

        # Store the selected username in the parent window for the PIN entry view
        selected_user = self.user_combo.get_active_text()
        self.parent_window.selected_username = selected_user

        # Switch to PIN entry view
        self.parent_window.switch_page("pin_entry")

    def _show_error(self, message: str) -> None:
        """Display error message"""
        self.error_label.set_text(message)
        self._state = LoginState.ERROR

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
            "Hier können Sie sich mit Ihrem Nutzerkonto anmelden. "
            "Wählen Sie zuerst Ihren Benutzernamen aus der Liste aus und klicken Sie dann auf \"Weiter\"."
        )
        dialog.run()
        dialog.destroy()