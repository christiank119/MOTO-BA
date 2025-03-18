import gi
from typing import Optional, Callable
import logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

class Colors:
    BACKGROUND = "#f6f4f3"
    FONT = "#1b2021"
    GREEN = "#83cd2d"

class CheckedInOverlay(Gtk.Overlay):
    def __init__(self, parent_window: Gtk.Window, user_name: str, callback: Optional[Callable] = None) -> None:
        super().__init__()

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

        # Size and position control
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)


        # Welcome message
        welcome_label = Gtk.Label()
        welcome_label.set_markup(f"<span size='50000'>Hallo {user_name}!</span>")
        welcome_label.set_margin_top(100)
        welcome_label.set_name("overlay_heading")
        center_box.pack_start(welcome_label, False, True, 20)

        # Image
        try:
            image = Gtk.Image.new_from_file("img/checked_in.png")
            image.set_pixel_size(60)
            image.set_margin_start(50)
            center_box.pack_start(image, False, False, 10)
        except Exception as e:
            logging.error(f"Failed to load checked_in image: {e}")

        content_container.add(center_box)
        # Position the content container on top of the background image
        fixed_container.put(content_container, 0, 0)

        # Add the whole fixed container to the parent window
        self.add(fixed_container)

        self._apply_styles()
        self.show_all()

        self.callback = callback
        # Hier Zeit bis es weg geht, kann für Debugging länger gemacht werden. Debuggende LG
        GLib.timeout_add(10000, self._on_timeout)

    def _apply_styles(self) -> None:
        css_provider = Gtk.CssProvider()
        css = f"""
            #content_container {{
            background-color: white;
            border-radius: 25px;
            box-shadow: rgba(0, 0, 0, 0.2) 0px 10px 15px;
            padding: 20px 20px 20px 20px;
            }}
            
            
            #overlay_heading {{
                font-family: "Inter", sans-serif;
                font-weight: bold;
                font-size: 70px;
                color: {Colors.FONT};
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _on_timeout(self) -> bool:
        if self.callback:
            self.callback()
        self.destroy()
        return False