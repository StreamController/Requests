from abc import ABCMeta, abstractmethod
from typing import Protocol
import requests


class KeyProvider(Protocol):
    @property
    @abstractmethod
    def keys(self) -> str:
        pass


class RequestDecodeError(ValueError):
    def __init__(self, inner: Exception, *args: object) -> None:
        super().__init__(*args)
        self.inner = inner


class ContentConverterBase(metaclass=ABCMeta):
    @property
    @abstractmethod
    def supports_keys(self) -> bool:
        pass

    @property
    @abstractmethod
    def mime_type(self) -> str | None:
        pass

    @abstractmethod
    def get_button_text(self, provider: KeyProvider, response: requests.Response) -> str | None:
        pass
