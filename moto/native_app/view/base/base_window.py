import gi
from typing import Optional, Callable
import logging

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class Colors:
    """Centralized color constants"""
    BACKGROUND = "#f6f4f3"
    FONT = "#1b2021"
    ERROR = "#ff3130"
    HELP_BUTTON = "#ffffff"
    INPUT_BG = "rgba(217, 217, 217, 0.5)"
    GREEN = "#83cd2d"
    KEYPAD_BUTTON = "rgba(217, 217, 217, 0.75)"
    LIST_BACKGROUND = "#D9D9D9"

class BaseWindow(Gtk.Box):
    """Base window with common UI components and styling"""
    
    def __init__(self, parent_window: Gtk.Window, title: str = "") -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.parent_window = parent_window
        self.title = title
        self.logger = self._setup_logging()
        
        # Common UI components
        self.content_container = None
        self.header_box = None
        self.error_label = None
        
        # Initialize base UI structure
        self._init_base_ui()
        self._apply_base_styles()
    
    def _setup_logging(self) -> logging.Logger:
        """Initialize logging configuration"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _init_base_ui(self) -> None:
        """Initialize the base UI structure"""
        # Create a Fixed container for absolute positioning
        fixed_container = Gtk.Fixed()
        fixed_container.set_size_request(1280, 720)
        
        # Background image (common across views)
        background_image = Gtk.Image.new_from_file("img/colors.png")
        fixed_container.put(background_image, 0, 0)
        
        # Main content container
        self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.content_container.set_size_request(1217, 660)
        self.content_container.set_margin_top(30)
        self.content_container.set_margin_bottom(30)
        self.content_container.set_margin_start(30)
        self.content_container.set_margin_end(30)
        self.content_container.set_name("content_container")
        
        # Header with standard layout
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_box.set_margin_bottom(10)
        
        # Help button (common to most screens)
        help_button = self._create_help_button()
        self.header_box.pack_end(help_button, False, False, 0)
        
        self.content_container.pack_start(self.header_box, False, False, 0)
        
        # Error message container
        self.error_label = Gtk.Label()
        self.error_label.set_name("error_label")
        self.error_label.set_margin_top(10)
        
        # Position content on top of background
        fixed_container.put(self.content_container, 0, 0)
        self.add(fixed_container)
    
    def _create_help_button(self) -> Gtk.Button:
        """Create standard help button"""
        button = Gtk.Button(label="HILFE")
        button.set_name("help_button")
        button.connect("clicked", self._show_help_dialog)
        return button
    
    def _create_back_button(self, callback: Optional[Callable] = None) -> Gtk.Button:
        """Create standard back button"""
        button = Gtk.Button(label="← Zurück")
        button.set_name("help_button")
        if callback:
            button.connect("clicked", callback)
        return button
    
    def _apply_base_styles(self) -> None:
        """Apply common CSS styles"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #content_container {{
                background-color: white;
                border-radius: 25px;
                box-shadow: rgba(0, 0, 0, 0.2) 0px 10px 15px;
                padding: 20px;
            }}
            
            #heading_type1 {{
                font-family: "Inter", sans-serif;
                font-size: 40px;
                font-weight: bold;
                color: {Colors.FONT};
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
    
    def show_error(self, message: str) -> None:
        """Display error message in the standard error label"""
        self.error_label.set_text(message)
        self.content_container.pack_end(self.error_label, False, False, 0)
        self.error_label.show()
    
    def _show_help_dialog(self, button: Gtk.Button) -> None:
        """Show help dialog with content specific to the child class"""
        help_text = self.get_help_text()
        
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Was muss ich in diesem Anzeigefenster beachten?"
        )
        dialog.format_secondary_text(help_text)
        dialog.run()
        dialog.destroy()
    
    def get_help_text(self) -> str:
        """Override in child classes to provide screen-specific help text"""
        return "Hilfetext wird in der abgeleiteten Klasse definiert."