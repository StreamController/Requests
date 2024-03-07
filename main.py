import json
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

import sys
import os
from PIL import Image
from loguru import logger as log
import requests

# Add plugin to sys.paths
sys.path.append(os.path.dirname(__file__))

# Import globals
import globals as gl

# Import own modules
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page

class PostRequest(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        
    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "http.png"), size=0.9)

    def get_config_rows(self) -> list:
        self.url_entry = Adw.EntryRow(title=self.plugin_base.lm.get("actions.post.url.title"))
        self.json_entry = Adw.EntryRow(title=self.plugin_base.lm.get("actions.post.json.title"))

        self.load_config_defaults()

        # Connect signals
        self.url_entry.connect("notify::text", self.on_url_changed)
        self.json_entry.connect("notify::text", self.on_json_changed)

        return [self.url_entry, self.json_entry]
    
    def on_url_changed(self, entry, *args):
        settings = self.get_settings()
        settings["url"] = entry.get_text()
        self.set_settings(settings)
    
    def on_json_changed(self, entry, *args):
        settings = self.get_settings()
        settings["json"] = entry.get_text()
        self.set_settings(settings)

    def load_config_defaults(self):
        self.url_entry.set_text(self.get_settings().get("url", "")) # Does not accept None
        self.json_entry.set_text(self.get_settings().get("json", "")) # Does not accept None

    def on_key_down(self):
        url = self.get_settings().get("url")
        json_dict = self.get_settings().get("json")

        if url in ["", None]:
            self.show_error(duration=2)

        try:
            json_dict = json.loads(json_dict)
            answer = requests.post(url=url, json=json_dict)
        except Exception as e:
            log.error(e)
            self.show_error(duration=2)

class GetRequest(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        
    def on_ready(self):
        self.set_media(image=Image.open(os.path.join(self.plugin_base.PATH, "assets", "http.png")), margins=[10, 10, 10, 10])

    def get_config_rows(self) -> list:
        self.url_entry = Adw.EntryRow(title="URL")
        self.load_config_defaults()

        # Connect signals
        self.url_entry.connect("notify::text", self.on_url_changed)

        return [self.url_entry]
    
    def on_url_changed(self, entry, *args):
        settings = self.get_settings()
        settings["url"] = entry.get_text()
        self.set_settings(settings)

    def load_config_defaults(self):
        self.url_entry.set_text(self.get_settings().get("url", "")) # Does not accept None

    def on_key_down(self):
        url = self.get_settings().get("url")

        if url in ["", None]:
            self.show_error(duration=2)

        try:
            response = requests.get(url=url)
            # Here you can handle the response as needed
        except Exception as e:
            log.error(e)
            self.show_error(duration=2)


class RequestsPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self.init_locale_manager()

        self.lm = self.locale_manager

        ## Register actions
        self.post_request_holder = ActionHolder(
            plugin_base=self,
            action_base=PostRequest,
            action_id="com_core447_Requests::PostRequest",
            action_name="Post Request",
            icon=Gtk.Picture.new_for_filename(os.path.join(self.PATH, "assets", "POST.png"))
        )
        self.add_action_holder(self.post_request_holder)

        self.get_request_holder = ActionHolder(
            plugin_base=self,
            action_base=GetRequest,
            action_id="com_core447_Requests::GetRequest",
            action_name="Get Request",
            icon=Gtk.Picture.new_for_filename(os.path.join(self.PATH, "assets", "GET.png"))
        )
        self.add_action_holder(self.get_request_holder)

        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/Core447/Requests",
            plugin_version="1.0.0",
            app_version="1.0.0-alpha"
        )

    def init_locale_manager(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()

    def get_selector_icon(self) -> Gtk.Widget:
        return Gtk.Image(icon_name="network-transmit-receive")