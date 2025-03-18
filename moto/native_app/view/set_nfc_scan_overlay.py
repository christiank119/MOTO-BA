import gi
import logging

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from view.base import BaseWindow, Colors


class SetNFCScanOverlay(BaseWindow):
    def __init__(self, parent_window: Gtk.Window) -> None:
        super().__init__(parent_window, title="NFC-Scan")
        self._init_ui()
        self._apply_styles()
        self.show_all()

    def _init_ui(self) -> None:
        """Initialize UI components"""
        # Add back button
        back_button = self._create_back_button(self._on_back_clicked)
        self.header_box.pack_start(back_button, False, False, 0)

        # Title
        self.title_label = Gtk.Label(
            label="Scannen Sie den NFC-Chip, den Sie neu setzen möchten."
        )
        self.title_label.set_name("heading_type1")
        self.title_label.set_halign(Gtk.Align.CENTER)
        self.content_container.pack_start(self.title_label, False, False, 30)

        # NFC Image
        self._add_nfc_image()

    def _add_nfc_image(self) -> None:
        """Load and display NFC scan image"""
        try:
            logo_image = Gtk.Image.new_from_file("img/nfc_pfeil.png")
            logo_image.set_margin_bottom(5)
            self.content_container.pack_start(logo_image, False, False, 10)
        except Exception as e:
            logging.error(f"Failed to load NFC scan image: {e}")
            error_label = Gtk.Label(label="⚠ Bild konnte nicht geladen werden.")
            error_label.set_name("error_label")
            self.content_container.pack_start(error_label, False, False, 10)

    def _on_back_clicked(self, button: Gtk.Button) -> None:
        """Handle back button click"""
        self.parent_window.switch_page("master_tablet")

    def get_help_text(self) -> str:
        """Provide help text for this screen"""
        return ("Hier können Sie den NFC-Chip eines Kinds neu zuweisen. "
                "Halten Sie das Armband dafür an den Scanner. "
                "Nach erfolgreicher Identifizierung des NFC-Chips öffnet "
                "sich ein Fenster, in dem Sie den Chip neu zuweisen können.")

    def _apply_styles(self) -> None:
        """Apply consistent UI styles"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #heading_type1 {{
                font-family: "Inter", sans-serif;
                font-size: 38px;
                font-weight: 600;
                color: {Colors.FONT};
            }}
            
            #error_label {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                font-weight: bold;
                color: red;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
