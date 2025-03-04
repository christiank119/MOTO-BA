import gi
from typing import Optional, Callable

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# Import centralized logging utilities
from utils import get_logger, log_operation

class Colors:
    """Centralized color constants"""
    BACKGROUND = "#f6f4f3"
    FONT = "#1b2021"
    ERROR = "#ff3130"
    HELP_BUTTON = "#ffffff"
    INPUT_BG = "rgba(217, 217, 217, 0.5)"
    GREEN = "#83cd2d"
    BLUE = "#5080D8"
    ORANGE = "#F78C10"
    KEYPAD_BUTTON = "rgba(217, 217, 217, 0.75)"
    LIST_BACKGROUND = "#D9D9D9"

class HelpOverlay(Gtk.EventBox):
    """Custom overlay for displaying help text."""
    def __init__(self, parent_window: Gtk.Window, help_text: str):
        super().__init__()
        self.parent_window = parent_window
        self.set_name("help_overlay")

        overlay_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        overlay_box.set_name("help_overlay_box")
        overlay_box.set_valign(Gtk.Align.CENTER)
        overlay_box.set_halign(Gtk.Align.CENTER)
        overlay_box.set_margin_top(50)
        overlay_box.set_margin_bottom(50)
        overlay_box.set_margin_start(50)
        overlay_box.set_margin_end(50)

        # Title
        title = Gtk.Label(label="Hilfe")
        title.set_name("help_overlay_title")
        overlay_box.pack_start(title, False, False, 10)

        # Help text label
        message = Gtk.Label()
        message.set_name("help_overlay_message")
        message.set_markup(help_text)
        message.set_line_wrap(True)
        message.set_max_width_chars(50)
        overlay_box.pack_start(message, False, False, 10)

        # Close button
        close_button = Gtk.Button(label="Schließen")
        close_button.set_name("help_overlay_close")
        close_button.connect("clicked", self._on_close)
        overlay_box.pack_start(close_button, False, False, 10)

        self.add(overlay_box)
        self.show_all()

    def _on_close(self, button: Gtk.Button):
        """Close the overlay"""
        self.get_parent().remove(self)

class BaseWindow(Gtk.Box):
    """Base window with common UI components and styling"""

    def __init__(self, parent_window: Gtk.Window, title: str = "") -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.parent_window = parent_window
        self.title = title
        self.logger = self._setup_logging()

        self.content_container = None
        self.header_box = None
        self.error_label = None

        # Ensure overlay is always present
        self.overlay = Gtk.Overlay()
        self._init_base_ui()
        self._apply_base_styles()

    def _setup_logging(self) -> None:
        """Initialize logging for this view"""
        return get_logger(self.__class__.__name__)

    def _init_base_ui(self) -> None:
        """Initialize the base UI structure"""
        self.overlay = Gtk.Overlay()
        self.overlay.set_size_request(1280, 720)

        # Background image (correctly positioned in the background)
        self.background_image = Gtk.Image.new_from_file("img/colors.png")
        self.background_box = Gtk.EventBox()
        self.background_box.add(self.background_image)
        self.overlay.add(self.background_box)  # Add background to the bottom layer

        # Main content container
        self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.content_container.set_size_request(1217, 660)
        self.content_container.set_margin_top(30)
        self.content_container.set_margin_bottom(30)
        self.content_container.set_margin_start(30)
        self.content_container.set_margin_end(30)
        self.content_container.set_name("content_container")

        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_box.set_margin_bottom(10)

        help_button = self._create_help_button()
        self.header_box.pack_end(help_button, False, False, 0)

        self.content_container.pack_start(self.header_box, False, False, 0)

        self.error_label = Gtk.Label()
        self.error_label.set_name("error_label")
        self.error_label.set_margin_top(10)

        self.overlay.add_overlay(self.content_container)  # Now on top of the background
        self.add(self.overlay)

    def _create_help_button(self) -> Gtk.Button:
        """Create standard help button"""
        button = Gtk.Button(label="HILFE")
        button.set_name("help_button")
        button.connect("clicked", self._show_help_overlay)
        return button

    @log_operation
    def _show_help_overlay(self, button: Gtk.Button) -> None:
        """Show help overlay with content specific to the child class"""
        help_text = self.get_help_text()
        help_overlay = HelpOverlay(self.parent_window, help_text)
        self.overlay.add_overlay(help_overlay)
        help_overlay.show_all()

    def get_help_text(self) -> str:
        """Override in child classes to provide screen-specific help text"""
        return "Hilfetext wird in der abgeleiteten Klasse definiert."

    def _create_back_button(self, callback: Optional[Callable] = None) -> Gtk.Button:
        """Create standard back button"""
        button = Gtk.Button(label="← Zurück")
        button.set_name("back_button")
        if callback:
            button.connect("clicked", callback)
        return button

    def _apply_base_styles(self) -> None:
        """Apply common CSS styles"""
        css_provider = Gtk.CssProvider()
        css = f"""
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
            #back_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.HELP_BUTTON};
                color: {Colors.FONT};
                border: 2px solid {Colors.FONT};
                border-radius: 45px;
                padding: 10px 25px;
                
                font-size: 20px;
                box-shadow: rgba(0, 0, 0, 0.18) 0px 2px 4px;
            }}
            #heading_type1 {{
                font-family: "Inter", sans-serif;
                font-size: 40px;
                font-weight: bold;
                color: {Colors.FONT};
            }}
            #help_overlay {{
                background-color: rgba(0, 0, 0, 0.6);
            }}
            #help_overlay_box {{
                background-color: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: rgba(0, 0, 0, 0.2) 0px 10px 15px;
            }}
            #help_overlay_title {{
                font-family: "Inter", sans-serif;
                font-size: 30px;
                font-weight: bold;
                color: {Colors.FONT};
            }}
            #help_overlay_message {{
                font-family: "Inter", sans-serif;
                font-size: 18px;
                color: {Colors.FONT};
            }}
            #content_container {{
                background-color: #ffffff; 
                border-radius: 15px;
                padding: 20px;
            }}
            #error_label {{
                font-family: "Inter", sans-serif;
                color: {Colors.ERROR};
                font-size: 18px;
                font-weight: 500;
            }}
            #help_overlay_close {{
                font-family: "Inter", sans-serif;
                font-size: 20px;
                font-weight: bold;
                color: #ffffff;
                background: {Colors.ERROR};
                border: none;
                margin-left: 200px;
                margin-right: 200px;
                border-radius: 10px;
                padding: 10px 20px;
                margin-top: 20px;
            }}
            
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )