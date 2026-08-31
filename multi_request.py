import json
import threading
from src.backend.PluginManager.ActionBase import ActionBase
from GtkHelper.StaticItemListComboRow import StaticItemListComboRow, ListItem
from .converters import CONVERTERS, KeyProvider, RequestDecodeError

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import os
from loguru import logger as log
import requests


class Abort(Exception):
    pass


class VisibleError(Exception):
    pass


_SUPPORTS_BODY = ["POST", "PUT"]

class RequestWrapper:
    def __init__(self, action: "MultiRequest"):
        self._action = action

    def send(self):
        try:
            self._send()
        except Abort:
            return
        except VisibleError:
            self._action.show_error(duration=1)
        except Exception as e:
            log.exception(e)
            self._action.show_error(duration=1)

    def _send(self):
        settings = self._action.get_settings()
        url = settings["url"]
        headers = settings["headers"]
        http_method = settings["http_method"]

        if not url:
            log.error("url is empty!")
            raise VisibleError

        headers = self._parse_headers(headers)
        data = self._get_body_data(headers)
        conv = CONVERTERS[settings["reply_type"]]
        response = requests.request(http_method, url=url, data=data, headers=headers, timeout=2)
        text = None
        try:
            text = conv.get_button_text(self._action, response)
        except RequestDecodeError as e:
            log.error("could not convert response with {0}! {1}", conv.__class__.__name__, e.inner)
            raise VisibleError

        if text is not None:
            self._action.set_center_label(text=str(text))

    def _parse_headers(self, headers: str | None) -> dict:
        try:
            if headers:
                headers = headers.strip()
                if headers:
                    mapping = json.loads(headers)
                    return { str(k).lower(): v for k, v in mapping }
            return {}
        except json.decoder.JSONDecodeError as e:
            log.error("could not parse headers: {0}", e)
            raise VisibleError

    def _get_body_data(self, headers: dict) -> str | None:
        settings = self._action.get_settings()
        http_method = settings["http_method"]
        if http_method in _SUPPORTS_BODY:
            body: str = (settings.get("body") or "").strip()
            if body:
                if "content-type" not in headers:
                    body_conv = CONVERTERS[settings["body_type"]]
                    if body_conv.mime_type:
                        headers["content-type"] = body_conv.mime_type
                return body


class MultiRequest(ActionBase, KeyProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.n_ticks = 0
        self._wrapper = RequestWrapper(self)

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "http.png"), size=0.8)
        self._custom_config_area = Gtk.Label(wrap=True)
        self._update_custom_config_area()

    def get_config_rows(self) -> list:
        lm = self.plugin_base.locale_manager

        self.http_method_combo = StaticItemListComboRow(
            [ListItem(m, m) for m in ["GET", "HEAD", "POST", "PUT", "DELETE"]],
            title=lm.get("actions.request.http_method.title"))
        self.url_entry = Adw.EntryRow(title="URL")
        self.headers_entry = Adw.EntryRow(title="Header (json)")

        self.body_entry = Adw.EntryRow(title="Body")
        _body_types = [
            ListItem(k, lm.get(f"convert.list_item.{k}"))
            for k in ["json", "xml", "plain_text"]
        ]
        self.body_type_combo = StaticItemListComboRow(
            _body_types,
            title=lm.get("actions.request.body_type.title"))

        self.keys_entry = Adw.EntryRow(title=lm.get("actions.get.keys_entry.title"))
        self.auto_fetch_spinner = Adw.SpinRow.new_with_range(step=1, min=0, max=3600)
        self.auto_fetch_spinner.set_title("Auto Fetch (s)")
        self.auto_fetch_spinner.set_subtitle("0 to disable")
        _reply_types = [
            ListItem(k, lm.get(f"convert.list_item.{k}"))
            for k in ["json", "xml", "plain_text", "ignore"]
        ]
        self.reply_type_combo = StaticItemListComboRow(
            _reply_types,
            title=lm.get("actions.request.reply_type.title"))

        self.body_group = [self.body_type_combo, self.body_entry]

        self.load_config_defaults()
        self._update_reply_type_dependant_widgets()
        self._update_http_method_dependant_widgets()

        # Connect signals
        self.http_method_combo.connect("notify::selected", self.on_http_method_changed)
        self.url_entry.connect("notify::text", self.on_url_changed)
        self.headers_entry.connect("notify::text", self.on_headers_changed)
        self.reply_type_combo.connect("notify::selected", self.on_reply_type_changed)
        self.keys_entry.connect("notify::text", self.on_keys_changed)
        self.auto_fetch_spinner.connect("notify::value", self.on_auto_fetch_changed)

        return [
            self.http_method_combo,
            self.url_entry,
            self.headers_entry,
        ] + self.body_group + [

            self.reply_type_combo,
            self.keys_entry,

            self.auto_fetch_spinner,
        ]

    def on_http_method_changed(self, entry, *args):
        settings = self.get_settings()
        settings["http_method"] = entry.get_selected_item().key
        self.set_settings(settings)
        self._update_http_method_dependant_widgets()

    def _update_http_method_dependant_widgets(self):
        settings = self.get_settings()
        key = settings.get("http_method", "GET")
        enable_body = key in _SUPPORTS_BODY
        for widget in self.body_group:
            widget.set_visible(enable_body)

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

    def on_reply_type_changed(self, entry, *args):
        settings = self.get_settings()
        settings["reply_type"] = entry.get_selected_item().key
        self.set_settings(settings)
        self._update_reply_type_dependant_widgets()

    def _update_reply_type_dependant_widgets(self):
        settings = self.get_settings()
        key = settings.get("reply_type", "json")
        conv = CONVERTERS[key]
        self.keys_entry.set_visible(conv.supports_keys)
        self._update_custom_config_area()

    def load_config_defaults(self):
        settings = self.get_settings()
        self.url_entry.set_text(settings.get("url", "")) # Does not accept None
        self.headers_entry.set_text(settings.get("headers", "{}"))
        self.keys_entry.set_text(settings.get("keys", "")) # Does not accept None
        self.auto_fetch_spinner.set_value(settings.get("auto_fetch", 0))
        self.reply_type_combo.set_selected_item_by_key(settings.get("reply_type", "json"))

    def on_key_down(self):
        threading.Thread(target=self._wrapper.send, daemon=True, name="get_request").start()

    @property
    def keys(self):
        return self.get_settings().get("keys", "")

    def get_custom_config_area(self):
        return self._custom_config_area

    def _update_custom_config_area(self):
        lm = self.plugin_base.locale_manager
        settings = self.get_settings()
        rt = settings.get("reply_type", "json")
        label = lm.get(f"custom_config.keys_hint.label.{rt}")
        self._custom_config_area.set_visible(bool(label))
        self._custom_config_area.set_label(label)

    def on_tick(self):
        auto_fetch = self.get_settings().get("auto_fetch", 0)
        if auto_fetch <= 0:
            self.n_ticks = 0
            return

        if self.n_ticks % auto_fetch == 0:
            self.on_key_down()
            self.n_ticks = 0
        self.n_ticks += 1

