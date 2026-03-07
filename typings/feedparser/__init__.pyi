"""
Type stubs for feedparser library.

This stub file provides type annotations for the feedparser library
to support static type checking with mypy and pyright.
"""

from collections.abc import Callable
from typing import Any, dict, list, optional, tuple

# Version and configuration constants
__author__: str
__license__: str
__version__: str
USER_AGENT: str
RESOLVE_RELATIVE_URIS: bool
SANITIZE_HTML: bool

# Type definitions
class FeedParserdict(dict):
    """A dictionary subclass for holding parsed feed data."""

    bozo: bool
    entries: list[FeedEntry]
    feed: FeedMetadata
    headers: dict[str, str]
    status: int
    encoding: str
    version: str
    namespacers: dict[str, str]
    def __getattr__(self, name: str) -> Any: ...

class FeedEntry:
    """Represents a single entry/item in a feed."""

    id: str
    title: str
    summary: str
    content: list[Content]
    links: list[Link]
    authors: list[Author]
    published: str
    updated: str
    tags: list[Tag]
    def __getattr__(self, name: str) -> Any: ...

class FeedMetadata:
    """Represents feed-level metadata."""

    title: str
    subtitle: str
    links: list[Link]
    icon: str
    logo: str
    rights: str
    updated: str
    def __getattr__(self, name: str) -> Any: ...

class Content:
    """Represents content within a feed entry."""

    type: str
    value: str
    language: optional[str]
    def __getattr__(self, name: str) -> Any: ...

class Link:
    """Represents a link element in a feed."""

    href: str
    rel: str
    type: optional[str]
    title: optional[str]
    hreflang: optional[str]
    lengths: optional[list[int]]
    def __getattr__(self, name: str) -> Any: ...

class Author:
    """Represents an author of a feed entry."""

    name: str
    email: optional[str]
    href: optional[str]
    def __getattr__(self, name: str) -> Any: ...

class Tag:
    """Represents a category/tag."""

    term: str
    scheme: optional[str]
    label: optional[str]
    def __getattr__(self, name: str) -> Any: ...

# Exception types
class ThingsNotFoundException(Exception):
    """Exception raised when requested feed elements are not found."""

    pass

class UndeclaredNamespace(Exception):
    """Exception raised when an undeclared namespace is encountered."""

    pass

class ContentTooBig(Exception):
    """Exception raised when feed content exceeds size limits."""

    pass

class Bootstrapping(Exception):
    """Exception raised during feedparser bootstrapping."""

    pass

# Parse function - the main entry point
def parse(
    url_file_stream_or_string: Any = ...,
    etag: optional[str] = ...,
    modified: optional[str | tuple[int, ...] | Any] = ...,
    agent: optional[str] = ...,
    referrer: optional[str] = ...,
    handlers: optional[list[Any]] = ...,
    request_headers: optional[dict[str, str]] = ...,
    response_headers: optional[dict[str, str]] = ...,
    resolve_relative_uris: optional[bool] = ...,
    sanitize_html: optional[bool] = ...,
) -> FeedParserdict:
    """Parse a feed from a URL, file, stream, or string.

    Args:
        url_file_stream_or_string: URL, file path, file-like object, or string.
        etag: HTTP ETag header value.
        modified: HTTP Last-Modified header value.
        agent: HTTP User-Agent header value.
        referrer: HTTP Referer header value.
        handlers: list of handlers for custom processing.
        request_headers: Additional HTTP request headers.
        response_headers: Override response headers.
        resolve_relative_uris: Whether to resolve relative URIs.
        sanitize_html: Whether to sanitize HTML content.

    Returns:
        A FeedParserdict containing the parsed feed data.
    """
    ...

# Date handler registration
def registerDateHandler(
    date_handler: Callable[[str], optional[Any]],
) -> None:
    """Register a custom date parsing handler.

    Args:
        date_handler: A callable that parses date strings.
    """
    ...
