"""Small asynchronous, read-only Paperless client with no Home Assistant dependency."""

from __future__ import annotations

import asyncio
import json
import shlex
from dataclasses import asdict, dataclass
from typing import Any

import aiohttp
from yarl import URL

from .const import MAX_PAGE_SIZE, MAX_SEARCH_LENGTH

MAX_RESPONSE_BYTES = 1024 * 1024
MAX_SEARCH_TERMS = 32
MAX_PREVIEW_BYTES = 20 * 1024 * 1024


class PaperlessError(Exception):
    """Safe, user-facing error: never include response bodies or credentials."""


class InvalidAddress(PaperlessError):
    """Invalid server address."""


class InvalidAuth(PaperlessError):
    """The token was rejected."""


class Forbidden(PaperlessError):
    """The Paperless user lacks document access."""


class CannotConnect(PaperlessError):
    """The server could not be reached."""


class InvalidResponse(PaperlessError):
    """Unexpected API response or redirect."""


class RateLimited(PaperlessError):
    """Paperless asked the client to slow down."""


class PreviewUnavailable(PaperlessError):
    """No supported PDF preview exists."""


class PreviewTooLarge(PaperlessError):
    """Preview exceeds the bounded memory budget."""


def search_parameters(text: str, mode: str) -> dict[str, str]:
    """Keep single-term substrings; safely scope AND queries to title/content.

    Double quotes group a phrase. User input is always quoted as data, never
    passed to the index as user-controlled field names or boolean operators.
    """
    lexer = shlex.shlex(text, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    lexer.quotes = '"'
    lexer.escape = ""
    try:
        terms = list(dict.fromkeys(term for term in lexer if term))
    except ValueError as err:
        raise ValueError("Close the double quotes around the phrase") from err
    if len(terms) > MAX_SEARCH_TERMS:
        raise ValueError("Use at most 32 search terms")
    if len(terms) > 1:
        terms = [term for term in terms if any(char.isalnum() for char in term)]
    if not terms:
        return {}
    if len(terms) == 1:
        return {"title__icontains" if mode == "title" else "title_content": terms[0]}
    clauses = []
    for term in terms:
        quoted = json.dumps(term, ensure_ascii=False)
        clauses.append(
            f"title:{quoted}" if mode == "title" else f"(title:{quoted} OR content:{quoted})"
        )
    return {"query": " AND ".join(clauses)}


def normalize_url(value: str) -> str:
    """Normalize a root URL, preserving a reverse-proxy subpath."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidAddress("Enter a server address")
    value = value.strip()
    if any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        raise InvalidAddress("Invalid server address")
    if "://" not in value:
        value = "http://" + value
    try:
        url = URL(value)
        if (
            url.scheme not in {"http", "https"}
            or not url.host
            or url.user is not None
            or url.password is not None
            or url.query_string
            or url.fragment
            or url.port is None
            or not 1 <= url.port <= 65535
        ):
            raise ValueError
    except (ValueError, TypeError) as err:
        raise InvalidAddress("Use an HTTP(S) address without credentials or query") from err
    return str(url).rstrip("/")


def validate_token(value: str) -> str:
    """Reject empty and malformed header values before making a request."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidAuth("Enter an API token")
    token = value.strip()
    if not token.isascii() or any(c.isspace() or ord(c) < 33 or ord(c) == 127 for c in token):
        raise InvalidAuth("Invalid API token format")
    return token


@dataclass(frozen=True)
class Document:
    """Only metadata needed by the cards; no OCR content or upstream URLs."""

    id: int
    title: str
    created: str | None


@dataclass(frozen=True)
class SearchPage:
    """A single server-side results page."""

    count: int
    page: int
    page_size: int
    documents: tuple[Document, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PaperlessClient:
    """Use an injected session. Its lifecycle belongs to Home Assistant."""

    def __init__(self, session: aiohttp.ClientSession, url: str, token: str) -> None:
        self.base_url = normalize_url(url)
        self._token = validate_token(token)
        self._session = session
        self._semaphore = asyncio.Semaphore(4)
        self._closed = False

    def close(self) -> None:
        """Prevent new requests after the integration has been unloaded."""
        self._closed = True

    async def preview(self, document_id: int) -> bytes:
        """Fetch only a bounded PDF preview from a fixed, authenticated endpoint."""
        if type(document_id) is not int or not 1 <= document_id <= 2147483647:
            raise ValueError("Invalid document ID")
        async with self._semaphore:
            if self._closed:
                raise CannotConnect("Integration is unloaded")
            try:
                async with self._session.get(
                    f"{self.base_url}/api/documents/{document_id}/preview/",
                    headers={"Authorization": f"Token {self._token}", "Accept": "application/pdf"},
                    timeout=aiohttp.ClientTimeout(total=60, connect=5),
                    allow_redirects=False,
                ) as response:
                    if response.status == 401:
                        raise InvalidAuth("API token rejected")
                    if response.status == 403:
                        raise Forbidden("Document access denied")
                    if response.status == 404:
                        raise PreviewUnavailable("Preview not found")
                    if response.status == 429:
                        raise RateLimited("Too many requests")
                    if response.status >= 500:
                        raise CannotConnect("Paperless server error")
                    if response.status != 200 or response.content_type != "application/pdf":
                        raise PreviewUnavailable("No PDF preview available")
                    if response.content_length and response.content_length > MAX_PREVIEW_BYTES:
                        raise PreviewTooLarge("Preview exceeds size limit")
                    data = bytearray()
                    async for chunk in response.content.iter_chunked(65536):
                        data.extend(chunk)
                        if len(data) > MAX_PREVIEW_BYTES:
                            raise PreviewTooLarge("Preview exceeds size limit")
                    if not data.startswith(b"%PDF-"):
                        raise PreviewUnavailable("Invalid PDF preview")
                    return bytes(data)
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                raise CannotConnect("Unable to reach Paperless") from err

    async def validate_connection(self) -> None:
        """Check document access while requesting the smallest useful payload."""
        await self.search("", page_size=1)

    async def search(
        self, text: str, *, mode: str = "title", page: int = 1, page_size: int = 5
    ) -> SearchPage:
        """Search terms with AND; retain literal substrings for one term/phrase."""
        if not isinstance(text, str) or len(text) > MAX_SEARCH_LENGTH:
            raise ValueError("Invalid search text")
        if mode not in {"title", "text"}:
            raise ValueError("Invalid search mode")
        if type(page) is not int or not 1 <= page <= 100000:
            raise ValueError("Invalid page")
        if type(page_size) is not int or not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ValueError("Invalid page size")
        params = {
            "page": str(page),
            "page_size": str(page_size),
            "ordering": "-created,-id",
            "fields": "id,title,created",
        }
        params.update(search_parameters(text, mode))
        payload = await self._get_json("documents/", params)
        count, results = payload.get("count"), payload.get("results")
        if type(count) is not int or count < 0 or not isinstance(results, list):
            raise InvalidResponse("Invalid document list")
        if len(results) > page_size or len(results) > count:
            raise InvalidResponse("Unexpected page size")
        documents = []
        for item in results:
            if (
                not isinstance(item, dict)
                or type(item.get("id")) is not int
                or item["id"] <= 0
                or not isinstance(item.get("title"), str)
                or not isinstance(item.get("created"), (str, type(None)))
            ):
                raise InvalidResponse("Invalid document metadata")
            documents.append(Document(item["id"], item["title"], item.get("created")))
        return SearchPage(count, page, page_size, tuple(documents))

    async def _get_json(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        async with self._semaphore:
            if self._closed:
                raise CannotConnect("Integration is unloaded")
            try:
                async with self._session.get(
                    f"{self.base_url}/api/{path}",
                    params=params,
                    headers={"Authorization": f"Token {self._token}", "Accept": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=15, connect=5),
                    allow_redirects=False,
                ) as response:
                    if response.status == 401:
                        raise InvalidAuth("API token rejected")
                    if response.status == 403:
                        raise Forbidden("Document access denied")
                    if response.status == 429:
                        raise RateLimited("Too many requests")
                    if response.status >= 500:
                        raise CannotConnect("Paperless server error")
                    if response.status != 200:
                        raise InvalidResponse("Unexpected API status")
                    if response.content_type != "application/json":
                        raise InvalidResponse("Expected JSON from the Paperless API")
                    data = bytearray()
                    async for chunk in response.content.iter_chunked(65536):
                        data.extend(chunk)
                        if len(data) > MAX_RESPONSE_BYTES:
                            raise InvalidResponse("API response exceeds size limit")
                    payload = json.loads(data)
                    if not isinstance(payload, dict):
                        raise InvalidResponse("Expected a JSON object")
                    return payload
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                raise CannotConnect("Unable to reach Paperless") from err
            except (ValueError, UnicodeError) as err:
                raise InvalidResponse("Invalid JSON response") from err
