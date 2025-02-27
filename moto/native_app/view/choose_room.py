import gi
from typing import List, Optional, Dict
from enum import Enum
import requests
import logging
from datetime import datetime

from view.base import BaseWindow, Colors

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

class Choose_RoomWindow(BaseWindow):
    """Room selection window for choosing which room to assign to the device"""
    
    def __init__(self, parent_window: Gtk.Window) -> None:
        super().__init__(parent_window, title="Raumauswahl")
        self._state = RoomState.IDLE
        self._rooms = []
        self._init_ui()
        self._apply_styles()

        # Set up room refresh
        GLib.timeout_add_seconds(30, self._refresh_rooms)
        GLib.idle_add(self._load_rooms)
        
        self.logger.info("Choose_RoomWindow initialization complete")

    def _init_ui(self) -> None:
        """Initialize the UI components"""
        self.logger.info("Starting UI initialization")

        # Logout button - Now with logout handler
        logout_button = Gtk.Button(label="Abmelden")
        logout_button.set_name("help_button")
        logout_button.connect("clicked", self._on_logout_clicked)
        self.header_box.pack_start(logout_button, False, False, 0)

        # Add refresh button to header
        refresh_button = Gtk.Button(label="Aktualisieren")
        refresh_button.set_name("help_button")
        refresh_button.connect("clicked", lambda _: self._load_rooms())
        self.header_box.pack_end(refresh_button, False, False, 10)

        # Header title
        title = Gtk.Label(label="Hallo VORNAME")
        title.set_name("heading_type1")
        title.set_halign(Gtk.Align.START)
        self.content_container.pack_start(title, False, True, 0)

        # Subtitle
        subtitle = Gtk.Label(label="Bitte ordne dem Gerät einen Raum zu:")
        subtitle.set_name("big_subheading")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_bottom(20)
        self.content_container.pack_start(subtitle, False, True, 0)

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
        self.status_bar = Gtk.Label(label="Zuletzt aktualisiert: 28.12.2024 12:00")
        self.status_bar.set_name("status_bar")
        self.status_bar.set_margin_top(10)
        self.content_container.pack_end(self.status_bar, False, False, 0)

    # New method to handle logout button click
    def _on_logout_clicked(self, button: Gtk.Button) -> None:
        """Handle logout button click by redirecting to login screen"""
        self.logger.info("Logout button clicked, redirecting to login screen")

        # Clear authentication tokens
        if hasattr(self.parent_window, "access_token"):
            self.parent_window.access_token = None
        if hasattr(self.parent_window, "refresh_token"):
            self.parent_window.refresh_token = None

        # Redirect to login screen
        self.parent_window.switch_page("login")

    def _load_rooms(self) -> None:
        self._state = RoomState.LOADING
        try:
            headers = {
                "Authorization": f"Bearer {self.parent_window.access_token}",
                "Content-Type": "application/json"
            }

            # For testing purposes, let's simulate some activity data
            # In a real implementation, this would come from the API
            sample_activities = {
                1: "Fußball",
                2: "Lesen",
                3: "Kunst",
                4: "Musik",
                5: "Pausenbetreuung",
                6: "Hausaufgaben",
                7: "Basketball",
                8: "keine"
            }

            response = requests.get(
                f"{Config.API_BASE_URL}{Config.ROOMS_ENDPOINT}",
                headers=headers,
                timeout=Config.REQUEST_TIMEOUT,
                verify=Config.VERIFY_SSL
            )

            if response.status_code == 200:
                data = response.json()

                # Add simulated activities to the data
                # In a real implementation, activities would come directly from the API
                for category_data in data:
                    for room in category_data['raeume']:
                        room_id = room['id']
                        # Assign a sample activity based on room ID
                        activity_index = room_id % len(sample_activities)
                        room['activity'] = sample_activities.get(activity_index, "keine")

                self._rooms_by_category = []

                for category_data in data:
                    category = category_data['kategorie']
                    rooms = [
                        RoomData(
                            id=room['id'],
                            raum_nr=room['raum_nr'],
                            is_occupied=room.get('belegt', False),
                            color=room['color'],
                            # Activity would normally come from API, get a default or extract from room data
                            activity=room.get('activity', "keine")
                        )
                        for room in category_data['raeume']
                    ]
                    self._rooms_by_category.append({"kategorie": category, "raeume": rooms})

                self._update_room_list()
                self._state = RoomState.IDLE
            else:
                self.logger.error(f"API error: {response.status_code}")
                self._state = RoomState.ERROR

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
                room_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                room_box.set_name("room_container")
                room_box.set_margin_top(5)
                room_box.set_margin_bottom(5)

                # Single-line room info with room number and activity
                room_info_label = Gtk.Label(label=f"Raum {room.raum_nr} - Aktivität: {room.activity}")
                room_info_label.set_name("room_info_label")
                room_info_label.set_halign(Gtk.Align.START)
                room_box.pack_start(room_info_label, True, True, 10)

                button = Gtk.Button(label="Belegt" if room.is_occupied else "Auswählen")
                button.set_name("occupied_button" if room.is_occupied else "select_button")
                if not room.is_occupied:
                    button.connect("clicked", self._on_room_selected, room.id)
                button.set_sensitive(not room.is_occupied)
                room_box.pack_end(button, False, False, 10)

                self.room_list.pack_start(room_box, False, True, 0)

        self.room_list.show_all()


    def _refresh_rooms(self) -> bool:
        self._load_rooms()
        return True

    def _on_room_selected(self, button: Gtk.Button, room_id: int) -> None:
        self.logger.info(f"Room {room_id} selected")
        if hasattr(self.parent_window, "switch_to_create_activity"):
            self.parent_window.switch_to_create_activity(room_id)
        else:
            self.logger.error("Parent window does not support switching views")

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
                background: {Colors.LIST_BACKGROUND};
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
        """Provide help text for room selection screen"""
        return ("In dieser Ansicht können Sie dem Gerät einen verfügbaren Raum zuweisen, "
                "um eine Aktivität zu erstellen. Verfügbare Räume erkennen Sie an der "
                "grünen Schaltfläche \"Auswählen\".") 