import requests
from .base import ContentConverterBase, KeyProvider


class IgnoreConverter(ContentConverterBase):
    supports_keys = False
    mime_type = None

    def get_button_text(self, provider: KeyProvider, response: requests.Response):
        _ = provider
        _ = response
        return None
