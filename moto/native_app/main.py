import gi
import uuid
import os
from typing import Optional, Dict, Type, Callable

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Import centralized logging utilities
from utils import get_logger, log_operation, logger_factory

# Import all view classes
from view.login import LoginWindow
from view.choose_room import Choose_RoomWindow
from view.create_activity import CreateActivityWindow
from view.home import HomeWindow
from view.checked_in_overlay import CheckedInOverlay
from view.checked_out_overlay import CheckedOutOverlay
from view.go_home import GoHomeWindow
from view.leave_room_overlay import LeaveRoomOverlay
from view.set_nfc_scan_overlay import SetNFCScanOverlay
from view.master_tablet import MasterTabletWindow
from view.set_nfc_set import SetNFCSetWindow
from view.remove_tablet_overlay import RemoveTabletOverlay
from view.change_roomdata import ChangeRoomDataWindow
from view.pin_entry import PinEntryWindow
from view.set_merged_room import Set_MergedRoom

class MainWindow(Gtk.Window):
    """Main application window that manages all views and navigation"""
    
    def __init__(self):
        super().__init__(title="MOTO")
        self.set_default_size(1280, 720)
        self.set_resizable(False)
        self.fullscreen()
        
        # Setup logging
        self.logger = get_logger("MainWindow")
        self.logger.info("Initializing MainWindow")
        
        # State management
        self.tag_id = ""
        self.current_room_id = ""
        self.selected_username = ""  # For passing between login and PIN screens
        
        # Authentication tokens
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
        # Device identification
        self._device_id = self._generate_device_id()
        self.logger.info(f"Device ID: {self._device_id}")

        # Create UI containers
        self._setup_containers()
        
        # Initialize first page based on authentication
        if self.user_is_authenticated():
            self.switch_page("choose_room")
        else:
            self.switch_page("login")
    
        
    def _generate_device_id(self) -> str:
        """Generate a unique device identifier or load existing one"""
        # In a real implementation, this should persist across app restarts
        return str(uuid.uuid4())
        
    def _setup_containers(self) -> None:
        """Initialize UI containers for the application"""
        # Create an overlay container for the main content and overlays
        self.overlay_container = Gtk.Overlay()
        self.add(self.overlay_container)

        # Main container for switching views
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.overlay_container.add(self.main_container)

    @log_operation(log_level="debug")
    def user_is_authenticated(self) -> bool:
        """Check if the user is authenticated based on access token."""
        return self.access_token is not None

    @log_operation
    def set_auth_tokens(self, access_token: str, refresh_token: str) -> None:
        """Set the authentication tokens after successful login."""
        self.logger.info("Setting authentication tokens")
        self.access_token = access_token
        self.refresh_token = refresh_token

    @log_operation(log_level="debug")
    def get_device_id(self) -> str:
        """Return the unique device identifier."""
        return self._device_id

    @log_operation
    def show_overlay(self, overlay_class: Type[Gtk.Widget], **kwargs) -> None:
        """Generic method to show an overlay with the specified parameters"""
        self.logger.info(f"Showing overlay: {overlay_class.__name__}")
        overlay = overlay_class(self, **kwargs)
        self.overlay_container.add_overlay(overlay)
        self.overlay_container.show_all()
        
    def show_checked_in_overlay(self, user_name: str, callback: Optional[Callable] = None) -> None:
        """Show the checked-in overlay with user name"""
        self.show_overlay(CheckedInOverlay, user_name=user_name, callback=callback)

    def show_checked_out_overlay(self, user_name: str, callback: Optional[Callable] = None) -> None:
        """Show the checked-out overlay with user name"""
        self.show_overlay(CheckedOutOverlay, user_name=user_name, callback=callback)

    def show_leave_room_overlay(self, user_name: str) -> None:
        """Show the leave room overlay with user name"""
        self.show_overlay(LeaveRoomOverlay, user_name=user_name)
        
    def show_remove_tablet_overlay(self) -> None:
        """Show the remove tablet overlay"""
        self.show_overlay(RemoveTabletOverlay)
        
    def _clear_main_container(self) -> None:
        """Clear all children from the main container"""
        for child in self.main_container.get_children():
            self.main_container.remove(child)
            
    def _switch_view(self, view_class: Type[Gtk.Widget], **kwargs) -> None:
        """Switch to a specific view with the given parameters"""
        self.logger.info(f"Switching to view: {view_class.__name__}")
        self._clear_main_container()
        view = view_class(parent_window=self, **kwargs)
        self.main_container.add(view)
        self.main_container.show_all()

    def switch_to_choose_room(self) -> None:
        """Switch to room selection view"""
        self._switch_view(Choose_RoomWindow)

    def switch_to_create_activity(self, room_id) -> None:
        """Switch to create activity view"""
        self._switch_view(CreateActivityWindow, room_id=room_id)

    def switch_to_home(self, room_id: str) -> None:
        """Switch to home view"""
        self._switch_view(HomeWindow, room_id=room_id)

    def switch_to_go_home(self) -> None:
        """Switch to go home view"""
        self._switch_view(GoHomeWindow)

    @log_operation(log_args=True)
    def switch_page(self, page_name: str) -> None:
        """Switch the current view to the specified page."""
        self.logger.info(f"Switching to page: {page_name}")
        self._clear_main_container()

        # Dictionary mapping page names to view classes and their arguments
        page_mapping = {
            "login": (LoginWindow, {}),
            "pin_entry": (PinEntryWindow, {}),
            "choose_room": (Choose_RoomWindow, {}),
            "create_activity": (CreateActivityWindow, {"room_id": self.current_room_id}),
            "home": (HomeWindow, {"room_id": self.current_room_id or "2"}),  # Default for development
            "go_home": (GoHomeWindow, {}),
            "set_nfc_scan": (SetNFCScanOverlay, {}),
            "set_nfc_scan_overlay": (SetNFCScanOverlay, {}),
            "master_tablet": (MasterTabletWindow, {}),
            "set_nfc_set": (SetNFCSetWindow, {"tag_id": self.tag_id}),
            "change_roomdata": (ChangeRoomDataWindow, {"room_id": self.current_room_id}),
            "set_merged_room": (Set_MergedRoom, {})
        }
        
        # Handle overlay views differently - they should be shown as overlays
        overlay_mapping = {
            "checked_in": lambda: self.show_checked_in_overlay("Test User"),
            "checked_out": lambda: self.show_checked_out_overlay("Test User"),
            "leave_room_overlay": lambda: self.show_leave_room_overlay("Test User"),
            "remove_tablet": lambda: self.show_remove_tablet_overlay()
        }
        
        # First check if it's an overlay page
        if page_name in overlay_mapping:
            overlay_mapping[page_name]()
            return
            
        # Otherwise, handle regular page switch
        if page_name in page_mapping:
            view_class, kwargs = page_mapping[page_name]
            self._switch_view(view_class, **kwargs)
        else:
            self.logger.error(f"Unknown page name: {page_name}")
            raise ValueError(f"Unknown page name: {page_name}")

        self.main_container.show_all()

def load_env_file():
    """Load environment variables from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def configure_logging():
    """Configure logging based on environment variables"""
    import logging
    
    # Create logs directory if it doesn't exist
    log_dir = os.environ.get('MOTO_LOG_DIR', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Map log level strings to logging module constants
    log_levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    # Get log settings from environment variables
    log_enabled = os.environ.get('MOTO_LOGGING_ENABLED', 'true').lower() == 'true'
    console_enabled = os.environ.get('MOTO_CONSOLE_LOGGING', 'true').lower() == 'true'
    file_enabled = os.environ.get('MOTO_FILE_LOGGING', 'true').lower() == 'true'
    console_level = os.environ.get('MOTO_CONSOLE_LOG_LEVEL', 'info').lower()
    file_level = os.environ.get('MOTO_FILE_LOG_LEVEL', 'debug').lower()
    
    # Configure logging
    logger_factory.update_config({
        'console_log_level': log_levels.get(console_level, logging.INFO),
        'file_log_level': log_levels.get(file_level, logging.DEBUG),
        'log_dir': log_dir,
        'enabled': log_enabled,
        'console_enabled': console_enabled,
        'file_enabled': file_enabled
    })

if __name__ == "__main__":
    # Load environment variables
    load_env_file()
    
    # Configure logging
    import logging
    configure_logging()
    
    # Log application startup
    logger = get_logger("main")
    logger.info("==== MOTO Native App Starting ====")
    
    try:
        win = MainWindow()
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("==== MOTO Native App Exiting ====")