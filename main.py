import json
import threading
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.n_ticks = 0
        
    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "http.png"), size=0.8)

    def get_config_rows(self) -> list:
        self.url_entry = Adw.EntryRow(title="URL")
        self.headers_entry = Adw.EntryRow(title="Header (json)")
        self.keys_entry = Adw.EntryRow(title="Json Keys")
        self.auto_fetch_spinner = Adw.SpinRow.new_with_range(step=1, min=0, max=3600)
        self.auto_fetch_spinner.set_title("Auto Fetch (s)")
        self.auto_fetch_spinner.set_subtitle("0 to disable")

        self.load_config_defaults()

        # Connect signals
        self.url_entry.connect("notify::text", self.on_url_changed)
        self.headers_entry.connect("notify::text", self.on_headers_changed)
        self.keys_entry.connect("notify::text", self.on_keys_changed)
        self.auto_fetch_spinner.connect("notify::value", self.on_auto_fetch_changed)

        return [self.url_entry, self.headers_entry, self.keys_entry, self.auto_fetch_spinner]
    
    def on_url_changed(self, entry, *args):
        settings = self.get_settings()
        settings["url"] = entry.get_text()
        self.set_settings(settings)

    def on_headers_changed(self, entry, *args):
        settings = self.get_settings()
        settings["headers"] = entry.get_text()
        self.set_settings(settings)

    def on_keys_changed(self, entry, *args):
        settings = self.get_settings()
        settings["keys"] = entry.get_text()
        self.set_settings(settings)

    def on_auto_fetch_changed(self, spinner, *args):
        settings = self.get_settings()
        settings["auto_fetch"] = spinner.get_value()
        self.set_settings(settings)

    def load_config_defaults(self):
        settings = self.get_settings()
        self.url_entry.set_text(settings.get("url", "")) # Does not accept None
        self.headers_entry.set_text(settings.get("headers", "{}"))
        self.keys_entry.set_text(settings.get("keys", "")) # Does not accept None
        self.auto_fetch_spinner.set_value(settings.get("auto_fetch", 0))

    def on_key_down(self):
        threading.Thread(target=self._on_key_down, daemon=True, name="get_request").start()

    def _on_key_down(self):
        settings = self.get_settings()
        url = settings.get("url")
        headers = settings.get("headers", {})

        if url in ["", None]:
            self.show_error(duration=1)

        try:
            response = requests.get(url=url, headers=json.loads(headers), timeout=2)
            j = None
            try:
                j = json.loads(response.text)
            except json.decoder.JSONDecodeError as e:
                log.error(e)
                self.show_error(duration=1)
            if j is not None:
                value = self.get_value(j, self.get_settings().get("keys", ""))
                self.set_center_label(text=str(value))
        except Exception as e:
            log.error(e)
            self.show_error(duration=1)

    def get_value(self, j, keys):
        for key in keys.split('.'):
            if key not in j:
                return None
            j = j.get(key)

        return j
    
    def get_custom_config_area(self):
        return Gtk.Label(label="Separate keys with a period (example: key1.key2.key3)")
    
    def on_tick(self):
        auto_fetch = self.get_settings().get("auto_fetch", 0)
        if auto_fetch <= 0:
            self.n_ticks = 0
            return
        
        if self.n_ticks % auto_fetch == 0:
            self.on_key_down()
            self.n_ticks = 0
        self.n_ticks += 1
        



class RequestsPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        self.init_locale_manager()

        self.lm = self.locale_manager

        ## Register actions
        self.post_request_holder = ActionHolder(
            plugin_base=self,
            action_base=PostRequest,
            action_id_suffix="PostRequest",
            action_name="Post Request",
            icon=Gtk.Picture.new_for_filename(os.path.join(self.PATH, "assets", "POST.png")),
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.UNTESTED
            }
        )
        self.add_action_holder(self.post_request_holder)

        self.get_request_holder = ActionHolder(
            plugin_base=self,
            action_base=GetRequest,
            action_id_suffix="GetRequest",
            action_name="Get Request",
            icon=Gtk.Picture.new_for_filename(os.path.join(self.PATH, "assets", "GET.png")),
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.UNTESTED
            }
        )
        self.add_action_holder(self.get_request_holder)

        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/StreamController/Requests",
            plugin_version="1.0.0",
            app_version="1.0.0-alpha"
        )

    def init_locale_manager(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()

    def get_selector_icon(self) -> Gtk.Widget:
        return Gtk.Image(icon_name="network-transmit-receive")