import mimetypes
import requests
from .base import ContentConverterBase, KeyProvider

class PlainTextConverter(ContentConverterBase):
    supports_keys = False
    mime_type = mimetypes.types_map[".txt"]

    def get_button_text(self, provider: KeyProvider, response: requests.Response):
        _ = provider
        text = response.text
        if text:
            text = text.strip()
        return text
