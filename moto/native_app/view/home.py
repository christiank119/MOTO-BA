import gi
from typing import Optional
import logging

from view.base import BaseWindow, Colors

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

class HomeWindow(BaseWindow):
    """Home screen for NFC tag scanning to check in/out"""
    
    def __init__(self, parent_window: Gtk.Window, room_id: str) -> None:
        super().__init__(parent_window, title="Home")
        self.room_id = room_id
        self._init_ui()
        self._apply_styles()

    def _init_ui(self) -> None:
        """Initialize the UI components"""
        # Settings button in header
        settings_button = Gtk.Button(label="Einstellungen")
        settings_button.set_name("help_button")
        settings_button.connect("clicked", self._on_login_clicked)
        self.header_box.pack_end(settings_button, False, False, 0)

        # Middle container for main content
        mid_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        mid_container.set_name("mid_container")
        mid_container.set_valign(Gtk.Align.CENTER)
        mid_container.set_halign(Gtk.Align.CENTER)
        mid_container.set_vexpand(True)

        # Room number
        room_label = Gtk.Label()
        room_label.set_markup(f"Raum {self.room_id}")
        room_label.set_name("heading_type1")
        mid_container.pack_start(room_label, False, False, 10)

        # NFC Image
        logo_image = Gtk.Image.new_from_file("img/nfc_pfeil.png")
        logo_image.set_margin_top(20)
        logo_image.set_margin_bottom(10)
        mid_container.pack_start(logo_image, False, False, 0)

        # Explanation text
        explanation = Gtk.Label(
            label="Halte dein Armband an das Logo um dich an- oder abzumelden!"
        )
        explanation.set_name("explanation")
        mid_container.pack_start(explanation, False, False, 10)
        
        # Add the middle container to the main content container
        self.content_container.pack_start(mid_container, True, True, 0)

        # Hidden form for NFC tag ID
        self.tag_id_entry = Gtk.Entry()
        self.tag_id_entry.set_visible(False)
        self.tag_id_entry.set_no_show_all(True)
        self.content_container.pack_end(self.tag_id_entry, False, False, 0)

    def _apply_styles(self) -> None:
        """Apply custom CSS styles"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #mid_container {{
                margin: 0px;
            }}
            
            #explanation {{
                font-family: "Inter", sans-serif;
                font-size: 25px;
                color: {Colors.FONT};
                margin: 0px 0;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _on_login_clicked(self, button: Gtk.Button) -> None:
        """Handle settings button click"""
        self.parent_window.switch_page("login")

    def _on_nfc_tag_detected(self, tag_id: str) -> None:
        """Handle NFC tag detection"""
        self.tag_id_entry.set_text(tag_id)
        # TODO: Add API call to handle check-in/check-out
        
    def get_help_text(self) -> str:
        """Provide help text for home screen"""
        return ("Auf diesem Bildschirm können Schüler ihr NFC-Armband an den Leser halten, "
                "um sich im Raum an- oder abzumelden. Die Statusänderung wird automatisch "
                "erfasst und im System gespeichert.")