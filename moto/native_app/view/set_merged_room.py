import gi
from typing import List, Optional, Dict
from enum import Enum
import requests
import logging
from datetime import datetime

from view.base import BaseWindow, Colors
from view.base.overlay import BaseOverlay

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib


class RoomState(Enum):
    IDLE = "idle"
    LOADING = "loading"
    ERROR = "error"


class Config:
    API_BASE_URL = "https://127.0.0.1:8000/api"  # Note the https
    ROOMS_ENDPOINT = "/get_room_list/"
    VERIFY_SSL = False
    REQUEST_TIMEOUT = 10


class RoomData:
    def __init__(self, id: int, raum_nr: str, is_occupied: bool, color: str, activity: str = "keine"):
        self.id = id
        self.raum_nr = raum_nr
        self.is_occupied = is_occupied
        self.color = color
        self.activity = activity  # Activity information with default value "keine"


class MergeRoomOverlay(BaseOverlay):
    """Overlay for room merging confirmation"""

    def __init__(self, parent_window: Gtk.Window, current_room: str, target_room: str):
        super().__init__(parent_window, title="Raumzusammenführung", auto_dismiss=False)
        self.current_room = current_room
        self.target_room = target_room
        self._create_content()
        self._apply_custom_styles()

    def _create_content(self):
        """Create the overlay content"""
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_name("overlay_content")
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)

        # Title
        title = Gtk.Label(label="Raumzusammenführung")
        title.set_name("overlay_title")
        content_box.pack_start(title, False, False, 10)

        # Message
        message = Gtk.Label()
        message.set_name("overlay_message")
        message.set_markup(
            f"Der aktuelle Raum <b>{self.current_room}</b> wird mit Raum <b>{self.target_room}</b> zusammengeführt.\n\nDieses Gerät wird anschließend abgemeldet.")
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

        self.pack_start(content_box, True, True, 0)

    def _apply_custom_styles(self):
        """Apply custom overlay styles"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #overlay_cancel_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.ERROR};
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
        """Handle cancel button click"""
        self.dismiss()

    def _on_confirm(self, button):
        """Handle confirm button click"""
        # This would perform the merge in a real implementation
        # For now, just go back to login screen after unregistering
        self.parent_window.access_token = None
        self.parent_window.refresh_token = None
        self.parent_window.switch_page("login")


class Set_MergedRoom(BaseWindow):
    """Room merging window for combining two rooms"""

    def __init__(self, parent_window: Gtk.Window) -> None:
        super().__init__(parent_window, title="Räume zusammenführen")
        self._state = RoomState.IDLE
        self._rooms = []
        self.current_room = "Raum 101"  # Current room the device is registered to

        # Create the overlay before initializing UI
        self.overlay = Gtk.Overlay()

        self._init_ui()
        self._apply_styles()

        # Set up room refresh
        GLib.timeout_add_seconds(30, self._refresh_rooms)
        GLib.idle_add(self._load_rooms)

        self.logger.info("Set_MergedRoom initialization complete")



    def _init_ui(self) -> None:
        """Initialize the UI components"""
        self.logger.info("Starting UI initialization")

        # Back button in header
        back_button = Gtk.Button(label="← Zurück")
        back_button.set_name("help_button")
        back_button.connect("clicked", self._on_back_clicked)
        self.header_box.pack_start(back_button, False, False, 0)

        # Add refresh button to header
        refresh_button = Gtk.Button(label="Aktualisieren")
        refresh_button.set_name("help_button")
        refresh_button.connect("clicked", lambda _: self._load_rooms())
        self.header_box.pack_end(refresh_button, False, False, 10)

        if self.content_container.get_parent():
            self.content_container.get_parent().remove(self.content_container)

        # Main container for overlay
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_hexpand(True)
        main_box.set_vexpand(True)

        # Header title - Show current room information
        title = Gtk.Label(label=f"Aktueller Raum: {self.current_room}")
        title.set_name("heading_type1")
        title.set_halign(Gtk.Align.START)
        self.content_container.pack_start(title, False, False, 0)

        # Subtitle
        subtitle = Gtk.Label(label="Bitte wählen Sie einen Raum für die Zusammenführung:")
        subtitle.set_name("big_subheading")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(20)
        self.content_container.pack_start(subtitle, False, False, 0)

        # Room list container
        self.room_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.room_list.set_name("room_list")

        # Scrollable container for room list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_name("room_scrolled_window")
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.add(self.room_list)
        self.content_container.pack_start(scrolled, True, True, 0)

        # Status bar
        self.status_bar = Gtk.Label(label="Zuletzt aktualisiert: " + datetime.now().strftime("%d.%m.%Y %H:%M"))
        self.status_bar.set_name("status_bar")
        self.status_bar.set_margin_top(10)
        self.content_container.pack_end(self.status_bar, False, False, 0)

        # Set up overlay container for confirmation dialogs
        self.overlay = Gtk.Overlay()
        self.overlay.add(self.content_container)

        # Add the overlay to the main content container
        main_box.pack_start(self.overlay, True, True, 0)

        # Create a new overlay
        self.overlay = Gtk.Overlay()
        self.overlay.set_size_request(1217, 660)

        # Get the fixed container (parent of content_container)
        fixed_container = self.get_children()[0]  # The BaseWindow adds a fixed container as its only child

        # Remove the content_container from the fixed_container
        if self.content_container.get_parent():
            self.content_container.get_parent().remove(self.content_container)

        # Add content_container to the overlay
        self.overlay.add(self.content_container)

        # Add the overlay to the fixed container
        fixed_container.put(self.overlay, 0, 0)

    def _on_back_clicked(self, button: Gtk.Button) -> None:
        """Handle back button click"""
        self.parent_window.switch_page("home")

    def _load_rooms(self) -> None:
        self._state = RoomState.LOADING
        # For demo purposes, let's use hardcoded data instead of API calls
        try:
            # Define some sample activities
            # In a real implementation, these would come from the API
            sample_activities = {
                102: "Fußball",
                103: "Lesen",
                104: "keine",
                201: "Kunst",
                202: "Musik",
                301: "Sport"
            }

            # Simulated data - normally from API
            self._rooms_by_category = [
                {
                    "kategorie": "Klassenräume",
                    "raeume": [
                        RoomData(id=102, raum_nr="102", is_occupied=False, color="#FFFFFF",
                                 activity=sample_activities[102]),
                        RoomData(id=103, raum_nr="103", is_occupied=True, color="#FFFFFF",
                                 activity=sample_activities[103]),
                        RoomData(id=104, raum_nr="104", is_occupied=False, color="#FFFFFF",
                                 activity=sample_activities[104]),
                    ]
                },
                {
                    "kategorie": "Fachräume",
                    "raeume": [
                        RoomData(id=201, raum_nr="201", is_occupied=False, color="#FFFFFF",
                                 activity=sample_activities[201]),
                        RoomData(id=202, raum_nr="202", is_occupied=True, color="#FFFFFF",
                                 activity=sample_activities[202]),
                    ]
                },
                {
                    "kategorie": "Sporthallen",
                    "raeume": [
                        RoomData(id=301, raum_nr="Sporthalle 1", is_occupied=False, color="#FFFFFF",
                                 activity=sample_activities[301]),
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
                room_box.set_margin_top(5)
                room_box.set_margin_bottom(5)

                # Single-line room info with room number and activity
                room_info_label = Gtk.Label(label=f"Raum {room.raum_nr} - Aktivität: {room.activity}")
                room_info_label.set_name("room_info_label")
                room_info_label.set_halign(Gtk.Align.START)
                room_box.pack_start(room_info_label, True, True, 10)

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
        """Apply custom CSS styles"""
        css_provider = Gtk.CssProvider()
        css = f"""
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
                background: {Colors.KEYPAD_BUTTON};
                padding: 18px;
                margin: 5px 0;
                border-radius: 18px;
                box-shadow: rgba(0, 0, 0, 0.18) 0px 2px 4px;
            }}
            
            #room_info_label {{
                font-family: "Inter", sans-serif;
                font-size: 24px;
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
                background: {Colors.ERROR};
                color: {Colors.FONT};
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
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

    def get_help_text(self) -> str:
        """Provide help text for room merging screen"""
        return ("In dieser Ansicht können Sie den aktuellen Raum mit einem anderen Raum zusammenführen. "
                "Wählen Sie einen freien Raum aus der Liste aus. "
                "Belegte Räume stehen für eine Zusammenführung nicht zur Verfügung.")
