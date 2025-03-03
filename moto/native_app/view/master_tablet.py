import gi
from typing import Optional

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from view.base import BaseWindow, Colors


class MasterTabletWindow(BaseWindow):
    def __init__(self, parent_window: Gtk.Window) -> None:
        super().__init__(parent_window, title="Einstellungen")  # Set title for the window
        self._init_ui()
        self._apply_styles()
        self.show_all()

    def _init_ui(self) -> None:
        """Initialize the UI components"""
        # Add back button to the header (provided by BaseWindow)
        back_button = self._create_back_button(lambda x: self.parent_window.switch_page("home"))
        self.header_box.pack_start(back_button, False, False, 0)

        # Title and subtitle
        title = Gtk.Label(label="Einstellungen")
        title.set_name("heading_2")
        title.set_halign(Gtk.Align.START)
        self.content_container.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="Wählen Sie eine der folgenden Aktionen aus:")
        subtitle.set_name("subheading_2")
        subtitle.set_halign(Gtk.Align.START)
        self.content_container.pack_start(subtitle, False, False, 0)

        # Buttons container
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        button_box.set_halign(Gtk.Align.CENTER)

        # Create buttons
        buttons = [
            ("Gerät abmelden", lambda x: self.parent_window.switch_page("remove_tablet")),
            ("Raumangaben ändern", lambda x: self.parent_window.switch_page("change_roomdata")),
            ("NFC Chip neu zuweisen", lambda x: self.parent_window.switch_page("set_nfc_scan"))
        ]

        for label, callback in buttons:
            button = self._create_action_button(label, callback)
            button_box.pack_start(button, False, True, 0)

        self.content_container.pack_start(button_box, True, True, 0)

    def _create_action_button(self, label: str, callback: callable) -> Gtk.Button:
        """Create styled action buttons"""
        button = Gtk.Button(label=label)
        button.set_name("button_style1")
        button.connect("clicked", callback)
        return button

    def _apply_styles(self) -> None:
        css_provider = Gtk.CssProvider()
        css = f"""
            #heading_2 {{
                font-family: "Inter", sans-serif;
                font-size: 48px;
                font-weight: 600;
                color: {Colors.FONT};
            }}
            
            #subheading_2 {{
                font-family: "Inter", sans-serif;
                font-size: 32px;
                color: {Colors.FONT};
            }}
            
            #help_button {{
                background: {Colors.HELP_BUTTON};
                color: {Colors.FONT};
                border: 2px solid {Colors.FONT};
                border-radius: 45px;
                padding: 10px 25px;
                font-size: 20px;
                box-shadow: rgba(0, 0, 0, 0.2) 15px 28px 25px -18px;
            }}
            
            #button_style1 {{
                font-family: "Inter", sans-serif;
                background: {Colors.KEYPAD_BUTTON};
                border-radius: 24px;
                color: {Colors.FONT};
                font-size: 30px;
                font-weight: bold;
                min-height: 70px;
                min-width: 320px;
                margin: 50px 0px 150px 0px;
                box-shadow: rgba(0, 0, 0, 0.2) 15px 28px 25px -18px;
            }}
            
            #button_style1:hover {{
                box-shadow: rgba(0, 0, 0, 0.3) 2px 8px 8px -5px;
            }}
            #help_button:hover {{
                box-shadow: rgba(0, 0, 0, 0.3) 2px 8px 8px -5px;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def get_help_text(self) -> str:
        """Provide help text specific to this screen"""
        return ("In dieser Masteransicht können Sie zwischen verschiedenen Funktionen "
                "der App navigieren. Sie müssen auf die grauen Schaltflächen klicken, "
                "um in das nächste Fenster zu navigieren.")