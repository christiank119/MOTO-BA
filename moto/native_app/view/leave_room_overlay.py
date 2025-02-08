import gi
from typing import Optional, Callable
import logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

class Colors:
    BACKGROUND_OVERLAY = "#f6f4f3"
    FONT = "#1b2021"
    DOOR = "#F78C10"
    TOILET = "#5080d8"
    SCHOOLYARD = "#83cd2d"
    HOME = "#ff3130"

class LeaveRoomOverlay(Gtk.Overlay):
    def __init__(self, parent_window: Gtk.Window, user_name: str, callback: Optional[Callable] = None) -> None:
        super().__init__()

        #self.parent_window = parent_window
        #self.callback = callback
        #self.logger = logging.getLogger(__name__)

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

        # Title
        title = Gtk.Label()
        title.set_markup(f"<span size='50000'>Tschüss {user_name}!</span>")
        title.set_name("overlay_heading")
        content_container.pack_start(title, False, False, 0)

        # Subtitle
        subtitle = Gtk.Label()
        subtitle.set_markup("<span size='25000'>Wohin möchtest du gehen?</span>")
        subtitle.set_name("overlay_subheading")
        content_container.pack_start(subtitle, False, False, 20)

        # Buttons container
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        button_box.set_halign(Gtk.Align.CENTER)

        # Create buttons
        buttons = [
            ("Raum wechseln", "leave_room_icon.png", Colors.DOOR, self._on_change_room),
            ("Toilette", "toilet_icon.png", Colors.TOILET, self._on_toilet),
            ("Schulhof", "school_yard_icon.png", Colors.SCHOOLYARD, self._on_schoolyard),
            ("Nach Hause", "home.png", Colors.HOME, self._on_go_home)
        ]

        for label, icon, color, callback in buttons:
            button_container = self._create_button(label, icon, color, callback)
            button_box.pack_start(button_container, False, True, 10)

        content_container.pack_start(button_box, False, False, 0)

        # Position the content container on top of the background image
        fixed_container.put(content_container, 0, 0)

        self.add(fixed_container)
        self._apply_styles()
        #self.show_all()

        # Auto timeout after 5 seconds
        GLib.timeout_add(500000, lambda: self._on_change_room()) # increased for debugging

    def _create_button(self, label: str, icon_name: str, color: str, callback: Callable) -> Gtk.Box:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        container.set_name("button_container")

        button = Gtk.Button()
        button.set_name(f"custom_button_{color[1:]}")  # Remove # from color

        try:
            image = Gtk.Image.new_from_file(f"img/{icon_name}")
            image.set_pixel_size(80)
            button.set_image(image)
        except Exception as e:
            self.logger.error(f"Failed to load image {icon_name}: {e}")

        button.connect("clicked", lambda w: callback())
        container.pack_start(button, False, False, 0)

        label_widget = Gtk.Label(label=label)
        label_widget.set_name("button_label")
        container.pack_start(label_widget, False, False, 0)

        return container

    def _apply_styles(self) -> None:
        css_provider = Gtk.CssProvider()
        css = f"""
            #content_container {{
            background-color: white;
            border-radius: 25px;
            box-shadow: rgba(0, 0, 0, 0.2) 0px 10px 15px;
            padding: 20px 20px 20px 20px;
            }}
            
            #overlay_heading, #overlay_subheading {{
                font-family: "Inter", sans-serif;
                font-weight: bold;
                color: {Colors.FONT};
            }}

            #button_container {{
                background: none;
                padding: 10px;
            }}

            #button_label {{
                font-family: "Inter", sans-serif;
                font-size: 26px;
                font-weight: 600;
                color: {Colors.FONT};
            }}

            #custom_button_{Colors.DOOR[1:]} {{
                background: {Colors.DOOR};
                border: none;
                border-radius: 18px;
                min-width: 200px;
                min-height: 300px;
                box-shadow: rgba(0, 0, 0, 0.36) 0px 6px 20px 2px;
            }}

            #custom_button_{Colors.TOILET[1:]} {{
                background: {Colors.TOILET};
                border: none;
                border-radius: 18px;
                min-width: 200px;
                min-height: 300px;
                box-shadow: rgba(0, 0, 0, 0.36) 0px 6px 20px 2px;
            }}

            #custom_button_{Colors.SCHOOLYARD[1:]} {{
                background: {Colors.SCHOOLYARD};
                border: none;
                border-radius: 18px;
                min-width: 200px;
                min-height: 300px;
                box-shadow: rgba(0, 0, 0, 0.36) 0px 6px 20px 2px;
            }}

            #custom_button_{Colors.HOME[1:]} {{
                background: {Colors.HOME};
                border: none;
                border-radius: 18px;
                min-width: 200px;
                min-height: 300px;
                box-shadow: rgba(0, 0, 0, 0.36) 0px 6px 20px 2px;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _on_change_room(self) -> None:
        self.parent_window.show_checked_out_overlay("User", lambda: self.parent_window.switch_page("choose_room"))
        self.destroy()
        return False

    def _on_toilet(self) -> None:
        self.parent_window.show_checked_out_overlay("User", lambda: self.parent_window.switch_page("home"))
        self.destroy()

    def _on_schoolyard(self) -> None:
        self.parent_window.show_checked_out_overlay("User", lambda: self.parent_window.switch_page("home"))
        self.destroy()

    def _on_go_home(self) -> None:
        self.parent_window.switch_page("go_home")
        self.destroy()