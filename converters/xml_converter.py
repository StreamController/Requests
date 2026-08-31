import mimetypes
import requests
from .base import ContentConverterBase, KeyProvider, RequestDecodeError
from defusedxml import ElementTree

class XmlConverter(ContentConverterBase):
    supports_keys = True
    mime_type = mimetypes.types_map[".xml"]
    _ignore_namespaces = {"": "*"}

    def get_button_text(self, provider: KeyProvider, response: requests.Response):
        xml = ElementTree.fromstring(response.text)
        xpath = provider.keys
        element = xml.find(xpath, self._ignore_namespaces)
        # `Element`s are false-ly, when they have no children, thus explicit check agains None
        if element is not None and element.text:
            return element.text
        return None