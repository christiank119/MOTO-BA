import gi
from typing import Optional, List
import logging

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from view.base import BaseWindow, Colors


class SetNFCSetWindow(BaseWindow):
    def __init__(self, parent_window: Gtk.Window, tag_id: str) -> None:
        super().__init__(parent_window, title="NFC-Zuweisung")
        self.tag_id = tag_id
        self._init_ui()
        self._apply_styles()
        self.show_all()

    def _init_ui(self) -> None:
        """Initialize UI components"""
        # Add back button
        back_button = self._create_back_button(lambda x: self.parent_window.switch_page("set_nfc_scan"))
        self.header_box.pack_start(back_button, False, False, 0)

        # Title
        title = Gtk.Label()
        title.set_markup(f"<span size='36000'>Chip erkannt: [{self.tag_id}]</span>")
        title.set_name("heading")
        title.set_halign(Gtk.Align.START)
        self.content_container.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="Weisen Sie das Armband bei Bedarf neu zu.")
        subtitle.set_name("subheading")
        subtitle.set_halign(Gtk.Align.START)
        self.content_container.pack_start(subtitle, False, False, 0)

        # Current assignment
        current_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        current_label = Gtk.Label(label="Aktuell Zugewiesen:")
        current_label.set_name("text_current")
        current_box.pack_start(current_label, False, False, 0)

        self.current_value = Gtk.Label(label="Niemand")
        self.current_value.set_name("current_value")
        current_box.pack_start(self.current_value, False, False, 0)

        self.content_container.pack_start(current_box, False, False, 20)

        # Search section
        search_label = Gtk.Label(label="Neu zuweisen:")
        search_label.set_name("text_new")
        search_label.set_halign(Gtk.Align.START)
        self.content_container.pack_start(search_label, False, False, 0)

        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Namen eingeben..")
        self.search_entry.set_name("searchbar")
        search_box.pack_start(self.search_entry, True, True, 0)

        search_button = Gtk.Button(label="Suchen")
        search_button.set_name("search_button")
        search_button.connect("clicked", self._on_search_clicked)
        search_box.pack_end(search_button, False, False, 0)

        self.content_container.pack_start(search_box, False, False, 0)

        # Results container with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)

        self.results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scrolled.add(self.results_box)
        self.content_container.pack_start(scrolled, True, True, 0)

        # Add some test results
        self._add_result("Max Mustermann", "1", True)
        self._add_result("Erika Musterfrau", "2", False)

    def _on_search_clicked(self, button: Gtk.Button) -> None:
        """Handle search button click - simulate user search"""
        search_term = self.search_entry.get_text().strip()
        self.results_box.foreach(lambda widget: self.results_box.remove(widget))  # Clear results

        if search_term:
            self._add_result(f"Gefundene Person: {search_term}", "3", False)

    def _add_result(self, name: str, user_id: str, is_staff: bool = False):
        """Create a result row"""
        result_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        result_box.set_name("pupil_container")

        name_label = Gtk.Label(label=name)
        name_label.set_name("text_pupil")
        name_label.set_halign(Gtk.Align.START)
        result_box.pack_start(name_label, True, True, 30)

        assign_button = Gtk.Button(label="Zuweisen")
        assign_button.set_name("assign_button_orange" if is_staff else "assign_button")
        assign_button.connect("clicked", self._on_assign, user_id)
        result_box.pack_end(assign_button, False, False, 25)

        self.results_box.pack_start(result_box, False, False, 0)

    def _on_assign(self, button: Gtk.Button, user_id: str):
        """Handle assigning NFC tag to a user"""
        # TODO: Implement API call to assign tag
        self.parent_window.switch_page("set_nfc_scan")

    def get_help_text(self) -> str:
        """Provide help text for this screen"""
        return ("In dieser Ansicht können Sie ein NFC-Armband einem neuen Kind oder "
                "Betreuer zuweisen. Tippen Sie beim gewünschten Kind/Betreuer auf "
                "\"Zuweisen\", um das Armband zuzuordnen.")

    def _apply_styles(self) -> None:
        """Apply consistent UI styles"""
        css_provider = Gtk.CssProvider()
        css = f"""
            #heading {{
                font-family: "Inter", sans-serif;
                font-size: 48px;
                font-weight: bold;
                color: {Colors.FONT};
            }}
            
            #subheading {{
                font-family: "Inter", sans-serif;
                font-size: 32px;
                color: {Colors.FONT};
            }}
            
            #text_current {{
                font-family: "Inter", sans-serif;
                font-size: 26px;
                color: {Colors.FONT};
            }}
            
            #current_value {{
                font-family: "Inter", sans-serif;
                background: {Colors.INPUT_BG};
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 26px;
                color: {Colors.FONT};
                box-shadow: rgba(0, 0, 0, 0.2) 15px 28px 25px -18px;
            }}
            
            #text_new {{
                font-family: "Inter", sans-serif;
                font-size: 30px;
                font-weight: 600;
                text-decoration: underline;
                color: {Colors.FONT};
            }}
            
            #searchbar {{
                font-family: "Inter", sans-serif;
                background-color: {Colors.INPUT_BG};
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                min-height: 40px;
            }}
            
            #search_button {{
                font-family: "Inter", sans-serif;
                background: {Colors.BLUE};
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                min-width: 150px;
                min-height: 40px;
                font-weight: 600;
            }}
            
            #pupil_container {{
                background-color: {Colors.KEYPAD_BUTTON};
                border-radius: 18px;
                min-height: 80px;
            }}
            
            #text_pupil {{
                font-family: "Inter", sans-serif;
                font-size: 27px;
                font-weight: 500;
                color: {Colors.FONT};
            }}
            
            
            #assign_button {{
                background: {Colors.GREEN};
                color: {Colors.FONT};
                font-family: "Inter", sans-serif;
                font-size: 24px;
                font-weight: 600;
                border-radius: 10px;
                padding: 10px 20px;
                margin-top: 10px;
                margin-bottom: 10px;
                min-width: 150px;
                min-height: 40px;
            }}
            
            #assign_button_orange {{
                background: {Colors.ORANGE};
                color: {Colors.FONT};
                font-family: "Inter", sans-serif;
                font-size: 24px;
                font-weight: 600;
                border-radius: 10px;
                padding: 10px 20px;
                margin-top: 10px;
                margin-bottom: 10px;
                min-width: 150px;
                min-height: 40px;
            }}
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
