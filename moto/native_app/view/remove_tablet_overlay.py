import gi
from typing import Optional, Callable

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from view.base import BaseWindow, Colors


class RemoveTabletOverlay(BaseWindow):
    def __init__(self, parent_window: Gtk.Window, callback: Optional[Callable] = None) -> None:
        super().__init__(parent_window, title="Gerät abmelden")  # Set title

        self._init_ui()
        self._apply_styles()
        self.show_all()

    def _init_ui(self) -> None:
        """Initialize the UI components"""
        # Title
        title = Gtk.Label()
        title.set_markup("<span size='36000'>Wollen Sie das Gerät wirklich abmelden?</span>")
        title.set_name("overlay_heading")
        title.set_halign(Gtk.Align.CENTER)
        title.set_margin_top(50)
        title.set_margin_bottom(60)
        self.content_container.pack_start(title, False, False, 0)

        # Buttons container
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        button_box.set_halign(Gtk.Align.CENTER)

        # "Nein" Button
        no_button = self._create_action_button("Nein", Colors.ERROR, self._on_no_clicked)
        no_button.set_name("abort_button")
        button_box.pack_start(no_button, False, False, 0)

        # "Ja" Button
        yes_button = self._create_action_button("Ja", Colors.GREEN, self._on_yes_clicked)
        yes_button.set_name("yes_button")
        button_box.pack_start(yes_button, False, False, 0)

        self.content_container.pack_start(button_box, False, False, 0)

        # Second row: "Raum zusammenlegen" centered below
        change_button = self._create_action_button("Raum zusammenlegen", Colors.ORANGE, self._on_change_clicked)
        change_button.set_halign(Gtk.Align.CENTER)  # Center the button
        change_button.set_name("change_button")
        self.content_container.pack_start(change_button, False, False, 10)




    def _create_action_button(self, label: str, color: str, callback: Callable) -> Gtk.Button:
        """Create a uniform action button"""
        button = Gtk.Button(label=label)
        button.set_name("overlay_button")
        button.set_size_request(260, 100)  # Fixed button size
        button.connect("clicked", lambda w: callback())
        button.get_style_context().add_class(f"button_{label.lower().replace(' ', '_')}")
        return button

    def _apply_styles(self) -> None:
        """Apply CSS styles"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #overlay_heading {{
                font-family: "Inter", sans-serif;
                font-size: 36px;
                font-weight: bold;
                color: {Colors.FONT};
            }}
            
            #yes_button, #abort_button {{
                font-family: "Inter", sans-serif;
                font-size: 28px;
                font-weight: bold;
                border: none;
                border-radius: 18px;
                padding: 10px 40px;
                min-width: 260px;
                min-height: 100px;
                box-shadow: rgba(0, 0, 0, 0.36) 0px 6px 20px 2px;
            }}
            
            
            #change_button {{
                font-family: "Inter", sans-serif;
                font-size: 22px;
                font-weight: bold;
                border: none;
                border-radius: 18px;
                margin-top: 20px;
                padding: 10px 40px;
                min-width: 200px;
                min-height: 80px;
                box-shadow: rgba(0, 0, 0, 0.36) 0px 6px 20px 2px;
                background: {Colors.ORANGE};
                color: white;
            }}
            
            #abort_button {{
                background: {Colors.ERROR};
                color: white;
            }}
            
            #yes_button {{
                background: {Colors.GREEN};
                color: {Colors.FONT};
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _on_yes_clicked(self) -> None:
        """Handle 'Ja' button click"""
        self.parent_window.access_token = None
        self.parent_window.refresh_token = None
        self.parent_window.switch_page("choose_room")
        self.destroy()

    def _on_change_clicked(self) -> None:
        """Handle 'Raum zusammenlegen' button click"""
        self.parent_window.switch_page("merge_rooms")
        self.destroy()

    def _on_no_clicked(self) -> None:
        """Handle 'Nein' button click"""
        self.parent_window.switch_page("master_tablet")
        self.destroy()

    def get_help_text(self) -> str:
        """Provide help text for this screen"""
        return ("Hier können Sie das Gerät von diesem Raum abmelden. "
                "Wenn Sie 'Ja' wählen, wird das Gerät zurückgesetzt. "
                "Mit 'Raum zusammenlegen' können Sie diesen Raum mit einem anderen kombinieren.")
