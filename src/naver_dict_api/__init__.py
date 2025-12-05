"""Naver Dictionary API Client Library"""

from .client import (
    DictEntry,
    DictType,
    InvalidResponseError,
    NaverDictClient,
    NaverDictError,
    NetworkError,
    ParseError,
    SearchMode,
    search_dict,
)

__version__ = "0.1.0"
__all__ = [
    "NaverDictClient",
    "DictEntry",
    "DictType",
    "SearchMode",
    "search_dict",
    "NaverDictError",
    "NetworkError",
    "ParseError",
    "InvalidResponseError",
]
