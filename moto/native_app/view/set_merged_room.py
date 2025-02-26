import gi
from typing import List, Optional, Dict
from enum import Enum
import requests
import logging
from datetime import datetime

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class RoomState(Enum):
    IDLE = "idle"
    LOADING = "loading"
    ERROR = "error"

class Colors:
    BACKGROUND = "#f6f4f3"
    FONT = "#1b2021"
    HELP_BUTTON = "#ffffff"
    LIST_BACKGROUND = "#D9D9D9"
    GREEN = "#83cd2d"
    RED = "#ff3130"
    OVERLAY_BG = "rgba(255, 255, 255, 0.95)"

class Config:
    API_BASE_URL = "https://127.0.0.1:8000/api"  # Note the https
    ROOMS_ENDPOINT = "/get_room_list/"
    VERIFY_SSL = False
    REQUEST_TIMEOUT = 10

class RoomData:
    def __init__(self, id: int, raum_nr: str, is_occupied: bool, color: str):
        self.id = id
        self.raum_nr = raum_nr
        self.is_occupied = is_occupied
        self.color = color

class MergeRoomOverlay(Gtk.Overlay):
    """Overlay for room merging confirmation"""

    def __init__(self, parent_window: Gtk.Window, current_room: str, target_room: str):
        super().__init__()

        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_name("overlay_content")
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)

        # Title
        title = Gtk.Label(label="Raumzusammenführung")
        title.set_name("overlay_title")
        content_box.pack_start(title, False, False, 10)

        # Message
        message = Gtk.Label()
        message.set_name("overlay_message")
        message.set_markup(f"Der aktuelle Raum <b>{current_room}</b> wird mit Raum <b>{target_room}</b> zusammengeführt.\n\nDieses Gerät wird anschließend abgemeldet.")
        message.set_line_wrap(True)
        message.set_max_width_chars(40)
        content_box.pack_start(message, False, False, 10)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        button_box.set_halign(Gtk.Align.CENTER)

        cancel_button = Gtk.Button(label="Abbrechen")
        cancel_button.set_name("overlay_cancel_button")
        cancel_button.connect("clicked", self._on_cancel)
        button_box.pack_start(cancel_button, False, False, 10)

        confirm_button = Gtk.Button(label="Bestätigen")
        confirm_button.set_name("overlay_confirm_button")
        confirm_button.connect("clicked", self._on_confirm)
        button_box.pack_start(confirm_button, False, False, 10)

        content_box.pack_start(button_box, False, False, 10)

        self.add(content_box)
        self.parent_window = parent_window
        self._apply_styles()

    def _apply_styles(self):
        css_provider = Gtk.CssProvider()
        css = f"""
            #overlay_content {{
                background-color: white;
                border-radius: 25px;
                box-shadow: rgba(0, 0, 0, 0.2) 0px 10px 15px;
                padding: 25px;
            }}
            
            #overlay_title {{
                font-family: "Inter", sans-serif;
                font-size: 32px;
                font-weight: bold;
                color: {Colors.FONT};
            }}
            
            #overlay_message {{
                font-family: "Inter", sans-serif;
                font-size: 18px;
                color: {Colors.FONT};
                margin: 15px 0;
            }}
            
            #overlay_cancel_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.RED};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }}
            
            #overlay_confirm_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.GREEN};
                color: {Colors.FONT};
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _on_cancel(self, button):
        # Just remove the overlay
        self.destroy()

    def _on_confirm(self, button):
        # This would perform the merge in a real implementation
        # For now, just go back to login screen after unregistering
        self.parent_window.access_token = None
        self.parent_window.refresh_token = None
        self.parent_window.switch_page("login")

class Set_MergedRoom(Gtk.Box):
    def __init__(self, parent_window: Gtk.Window) -> None:
        super().__init__(homogeneous=False, spacing=20)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.parent_window = parent_window
        self._state = RoomState.IDLE
        self._rooms = []
        self.current_room = "Raum 101"  # Current room the device is registered to

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self._init_ui()
        self._apply_styles()

        # Set up room refresh
        GLib.timeout_add_seconds(30, self._refresh_rooms)
        GLib.idle_add(self._load_rooms)

        self.show_all()
        self.logger.info("Choose_RoomWindow initialization complete")

    def _init_ui(self) -> None:
        self.logger.info("Starting UI initialization")

        # Create the overlay container
        self.overlay = Gtk.Overlay()

        # Main content container
        main_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_content.set_margin_top(30)
        main_content.set_margin_bottom(0)
        main_content.set_margin_start(20)
        main_content.set_margin_end(20)

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_bottom(20)

        # Back button
        back_button = Gtk.Button(label="← Zurück")
        back_button.set_name("help_button")
        back_button.set_halign(Gtk.Align.START)
        back_button.connect("clicked", self._on_back_clicked)
        header_box.pack_start(back_button, False, False, 0)

        help_button = Gtk.Button(label="HILFE")
        help_button.set_name("help_button")
        help_button.connect("clicked", self._show_help_dialog)
        header_box.pack_end(help_button, False, False, 0)

        refresh_button = Gtk.Button(label="Aktualisieren")
        refresh_button.set_name("help_button")
        refresh_button.connect("clicked", lambda _: self._load_rooms())
        header_box.pack_end(refresh_button, False, False, 0)

        main_content.pack_start(header_box, False, True, 0)

        # Header title - Show current room information
        title = Gtk.Label(label=f"Aktueller Raum: {self.current_room}")
        title.set_name("big_heading")
        title.set_halign(Gtk.Align.START)
        main_content.pack_start(title, False, True, 0)

        # Subtitle
        subtitle = Gtk.Label(label="Bitte wählen Sie einen Raum für die Zusammenführung:")
        subtitle.set_name("big_subheading")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(20)
        main_content.pack_start(subtitle, False, True, 0)

        # Room list
        self.room_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.room_list.set_margin_start(10)
        self.room_list.set_margin_end(0)
        self.room_list.set_name("room_list")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_name("room_scrolled_window")
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.add(self.room_list)
        main_content.pack_start(scrolled, True, True, 0)

        # Status bar
        self.status_bar = Gtk.Label(label="Zuletzt aktualisiert: " + datetime.now().strftime("%d.%m.%Y %H:%M"))
        self.status_bar.set_name("status_bar")
        self.status_bar.set_margin_bottom(10)
        main_content.pack_end(self.status_bar, False, True, 0)

        # Add main content to overlay
        self.overlay.add(main_content)

        # Add the overlay to this container
        self.add(self.overlay)

    def _on_back_clicked(self, button: Gtk.Button) -> None:
        """Handle back button click"""
        self.parent_window.switch_page("home")

    def _load_rooms(self) -> None:
        self._state = RoomState.LOADING
        # For demo purposes, let's use hardcoded data instead of API calls
        try:
            # Simulated data - normally from API
            self._rooms_by_category = [
                {
                    "kategorie": "Klassenräume",
                    "raeume": [
                        RoomData(id=102, raum_nr="102", is_occupied=False, color="#FFFFFF"),
                        RoomData(id=103, raum_nr="103", is_occupied=True, color="#FFFFFF"),
                        RoomData(id=104, raum_nr="104", is_occupied=False, color="#FFFFFF"),
                    ]
                },
                {
                    "kategorie": "Fachräume",
                    "raeume": [
                        RoomData(id=201, raum_nr="201", is_occupied=False, color="#FFFFFF"),
                        RoomData(id=202, raum_nr="202", is_occupied=True, color="#FFFFFF"),
                    ]
                },
                {
                    "kategorie": "Sporthallen",
                    "raeume": [
                        RoomData(id=301, raum_nr="Sporthalle 1", is_occupied=False, color="#FFFFFF"),
                    ]
                }
            ]

            self._update_room_list()
            self._state = RoomState.IDLE

            # Update status bar with current time
            self.status_bar.set_text("Zuletzt aktualisiert: " + datetime.now().strftime("%d.%m.%Y %H:%M"))

        except Exception as e:
            self.logger.error(f"Failed to load rooms: {e}")
            self._state = RoomState.ERROR


    def _update_room_list(self) -> None:
        for child in self.room_list.get_children():
            self.room_list.remove(child)

        for category_data in self._rooms_by_category:
            category = category_data['kategorie']
            rooms = category_data['raeume']

            category_label = Gtk.Label(label=f"Kategorie: {category}")
            category_label.set_name("category_label")
            category_label.set_halign(Gtk.Align.START)
            self.room_list.pack_start(category_label, False, True, 10)

            for room in sorted(rooms, key=lambda x: x.raum_nr):
                # Skip the current room - can't merge with itself
                if room.raum_nr == self.current_room[5:]:  # Remove "Raum " prefix
                    continue

                room_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                room_box.set_name("room_container")

                label = Gtk.Label(label=f"Raum {room.raum_nr}")
                label.set_name("room_label")
                label.set_halign(Gtk.Align.START)
                room_box.pack_start(label, True, True, 10)

                button = Gtk.Button(label="Belegt" if room.is_occupied else "Zusammenführen")
                button.set_name("occupied_button" if room.is_occupied else "select_button")
                if not room.is_occupied:
                    button.connect("clicked", self._on_room_selected, room.id, f"Raum {room.raum_nr}")
                button.set_sensitive(not room.is_occupied)
                room_box.pack_end(button, False, False, 10)

                self.room_list.pack_start(room_box, False, True, 0)

        self.room_list.show_all()


    def _refresh_rooms(self) -> bool:
        self._load_rooms()
        return True

    def _on_room_selected(self, button: Gtk.Button, room_id: int, room_name: str) -> None:
        """Handle room selection for merging"""
        self.logger.info(f"Room {room_id} selected for merging with current room")

        # Show the merge confirmation overlay
        merge_overlay = MergeRoomOverlay(self.parent_window, self.current_room, room_name)
        self.overlay.add_overlay(merge_overlay)
        merge_overlay.show_all()

    def _apply_styles(self) -> None:
        css_provider = Gtk.CssProvider()
        css = f"""
            box {{
                background: {Colors.BACKGROUND};
            }}
            
            #big_heading {{
                font-family: "Inter", sans-serif;
                font-size: 48px;
                font-weight: bold;
                color: {Colors.FONT};
            }}
            
            #big_subheading {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
                color: {Colors.FONT};
            }}
            
            #category_label {{
                font-family: "Inter", sans-serif;
                font-size: 20px;
                color: {Colors.FONT};
                border-bottom: 2px solid {Colors.FONT};
            }}
            
            #room_container {{
                font-family: "Inter", sans-serif;
                background: {Colors.LIST_BACKGROUND};
                padding: 18px;
                margin: 5px 0;
                border-radius: 18px;
                box-shadow: rgba(0, 0, 0, 0.18) 0px 2px 4px;
            }}
            
            #room_label {{
                font-family: "Inter", sans-serif;
                font-size: 26px;
                color: {Colors.FONT};
            }}
                
            #room_list {{
                background: inherit;
                border-radius: 40px;
            }}
            
            #select_button {{
                font-family: "Inter", sans-serif;
                font-size: 20px;
                background: {Colors.GREEN};
                color: {Colors.FONT};
                border: none;
                border-radius: 10px;
                padding: 15px 25px;
                box-shadow: rgba(0, 0, 0, 0.18) 0px 2px 4px;
            }}
            
            #occupied_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.RED};
                color: {Colors.FONT};
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                box-shadow: rgba(0, 0, 0, 0.18) 0px 2px 4px;
            }}
            
            #help_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.HELP_BUTTON};
                color: {Colors.FONT};
                border: 2px solid {Colors.FONT};
                border-radius: 45px;
                padding: 5px 15px;
                font-size: 20px;
                box-shadow: rgba(0, 0, 0, 0.18) 0px 2px 4px;
            }}
            
            #status_bar {{
                font-family: "Inter", sans-serif;
                font-size: 12px;
                color: #666666;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _show_help_dialog(self, button: Gtk.Button) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Was muss ich in diesem Anzeigefenster beachten?"
        )
        dialog.format_secondary_text(
            "In dieser Ansicht können Sie den aktuellen Raum mit einem anderen Raum zusammenführen. "
            "Wählen Sie einen freien Raum aus der Liste aus. "
            "Belegte Räume stehen für eine Zusammenführung nicht zur Verfügung."
        )
        dialog.run()
        dialog.destroy()