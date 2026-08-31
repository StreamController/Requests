from .base import ContentConverterBase, RequestDecodeError, KeyProvider
from .json_converter import JsonConverter
from .xml_converter import XmlConverter
from .plain_text_converter import PlainTextConverter
from .ignore_converter import IgnoreConverter

CONVERTERS: dict[str, ContentConverterBase] = {
    "json": JsonConverter(),
    "xml": XmlConverter(),
    "plain_text": PlainTextConverter(),
    "ignore": IgnoreConverter(),
}

__all__ = [
    "CONVERTERS",
    "ContentConverterBase",
    "RequestDecodeError",
    "KeyProvider",
]