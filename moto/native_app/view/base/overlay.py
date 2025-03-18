import gi
import logging
from typing import Optional, Callable
import time

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class BaseOverlay(Gtk.Box):
    """Base class for overlay notifications with auto-dismiss functionality"""
    
    def __init__(self, parent_window: Gtk.Window, title: str = "", auto_dismiss: bool = True, duration: int = 3) -> None:
        """Initialize the base overlay"""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.parent_window = parent_window
        self.title = title
        self.auto_dismiss = auto_dismiss
        self.duration = duration  # in seconds
        self.dismiss_timeout_id = None
        
        # Set up logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Track when the overlay was shown
        self.show_time = None
        
        # Set up transparent background
        self.set_name("overlay_background")
        
        # Apply base styles
        self._apply_base_styles()
        
        # Connect to map signal to start auto-dismiss timer
        self.connect("map", self._on_map)
    
    def _on_map(self, widget) -> None:
        """Handle when the overlay is mapped to the screen"""
        self.show_time = time.time()
        
        if self.auto_dismiss:
            # Set up auto-dismiss timer
            self.dismiss_timeout_id = GLib.timeout_add_seconds(
                self.duration, 
                self._auto_dismiss
            )
    
    def _auto_dismiss(self) -> bool:
        """Auto-dismiss the overlay after the specified duration"""
        self.logger.info(f"Auto-dismissing overlay after {self.duration} seconds")
        self.dismiss()
        return False  # Don't repeat the timeout
    
    def dismiss(self) -> None:
        """Dismiss the overlay"""
        # Remove from parent
        parent = self.get_parent()
        if parent:
            parent.remove(self)
    
    def cancel_auto_dismiss(self) -> None:
        """Cancel the auto-dismiss timer"""
        if self.dismiss_timeout_id:
            GLib.source_remove(self.dismiss_timeout_id)
            self.dismiss_timeout_id = None
    
    def _apply_base_styles(self) -> None:
        """Apply base overlay styles"""
        css_provider = Gtk.CssProvider()
        css = """
            #overlay_background {
                background-color: rgba(0, 0, 0, 0.7);
            }
            
            #overlay_content {
                background-color: white;
                border-radius: 15px;
                padding: 20px;
            }
            
            #overlay_title {
                font-family: "Inter", sans-serif;
                font-size: 24px;
                font-weight: bold;
            }
            
            #overlay_message {
                font-family: "Inter", sans-serif;
                font-size: 18px;
            }
            
            #overlay_button {
                font-family: "Inter", sans-serif;
                font-size: 16px;
                padding: 8px 16px;
                border-radius: 5px;
            }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

class NotificationOverlay(BaseOverlay):
    """General notification overlay with customizable content"""
    
    def __init__(self, parent_window: Gtk.Window, title: str, message: str, 
                 icon_path: Optional[str] = None, button_text: str = "OK",
                 callback: Optional[Callable] = None, auto_dismiss: bool = True, 
                 duration: int = 3) -> None:
        """Initialize notification overlay"""
        super().__init__(parent_window, title, auto_dismiss, duration)
        self.message = message
        self.icon_path = icon_path
        self.button_text = button_text
        self.callback = callback
        
        # Center the overlay content
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        
        # Create the overlay content
        self._create_content()
    
    def _create_content(self) -> None:
        """Create the overlay content"""
        # Create content container
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content.set_name("overlay_content")
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        
        # Title
        title_label = Gtk.Label(label=self.title)
        title_label.set_name("overlay_title")
        content.pack_start(title_label, False, False, 0)
        
        # Icon if provided
        if self.icon_path:
            try:
                icon = Gtk.Image.new_from_file(self.icon_path)
                icon.set_pixel_size(64)  # Set icon size
                content.pack_start(icon, False, False, 10)
            except Exception as e:
                self.logger.error(f"Error loading icon: {e}")
        
        # Message
        message_label = Gtk.Label(label=self.message)
        message_label.set_name("overlay_message")
        message_label.set_line_wrap(True)
        message_label.set_max_width_chars(40)
        content.pack_start(message_label, False, False, 0)
        
        # Button
        button = Gtk.Button(label=self.button_text)
        button.set_name("overlay_button")
        button.connect("clicked", self._on_button_clicked)
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.pack_start(button, False, False, 0)
        content.pack_start(button_box, False, False, 10)
        
        self.pack_start(content, True, True, 0)
    
    def _on_button_clicked(self, button: Gtk.Button) -> None:
        """Handle button click"""
        # Cancel auto-dismiss since user interacted
        self.cancel_auto_dismiss()
        
        # Dismiss the overlay
        self.dismiss()
        
        # Call callback if provided
        if self.callback:
            self.callback()