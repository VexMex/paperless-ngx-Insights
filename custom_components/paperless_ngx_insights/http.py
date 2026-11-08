"""Authenticated PDF previews; no public URLs or upstream credentials in URLs."""

import asyncio
import re

from aiohttp import ClientError, web
from aiohttp.helpers import content_disposition_header
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.http.const import KEY_HASS_REFRESH_TOKEN_ID, KEY_HASS_USER
from homeassistant.core import HomeAssistant

from .access import can_access
from .client import (
    Forbidden,
    InvalidAuth,
    PaperlessError,
    PreviewTooLarge,
    PreviewUnavailable,
    RateLimited,
)
from .const import DOMAIN

HEADERS = {
    "Cache-Control": "no-store, private",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


class PreviewView(HomeAssistantView):
    """Authorize every document request independently of dashboard visibility."""

    url = f"/api/{DOMAIN}/{{entry_id}}/documents/{{document_id}}/preview"
    name = f"api:{DOMAIN}:preview"
    requires_auth = True
    thumbnail = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str, document_id: str) -> web.Response:
        user = request.get(KEY_HASS_USER)
        if not can_access(self.hass, entry_id, user):
            return web.Response(status=403, headers=HEADERS)
        if not document_id.isascii() or not document_id.isdecimal() or len(document_id) > 10:
            return web.Response(status=400, headers=HEADERS)
        number = int(document_id)
        if not 1 <= number <= 2147483647:
            return web.Response(status=400, headers=HEADERS)
        client = self.hass.data.get(DOMAIN, {}).get(entry_id)
        if client is None:
            return web.Response(status=404, headers=HEADERS)
        try:
            if self.thumbnail:
                body, mime = await client.thumbnail(number)
            else:
                body = await client.preview(number)
                mime = "application/pdf"
        except InvalidAuth:
            if user.is_admin:
                if entry := self.hass.config_entries.async_get_entry(entry_id):
                    entry.async_start_reauth(self.hass)
            return web.Response(status=502, headers=HEADERS)
        except Forbidden:
            return web.Response(status=403, headers=HEADERS)
        except PreviewTooLarge:
            return web.Response(status=413, headers=HEADERS)
        except PreviewUnavailable:
            return web.Response(status=415, headers=HEADERS)
        except RateLimited:
            return web.Response(status=429, headers=HEADERS)
        except PaperlessError:
            return web.Response(status=502, headers=HEADERS)
        if self.hass.data.get(DOMAIN, {}).get(entry_id) is not client or not can_access(
            self.hass, entry_id, user
        ):
            return web.Response(status=403, headers=HEADERS)
        return web.Response(
            body=body,
            content_type=mime,
            headers={**HEADERS, "Content-Disposition": 'inline; filename="preview"'},
        )


class ThumbnailView(PreviewView):
    """The same per-request permission gates apply to raster thumbnails."""

    url = f"/api/{DOMAIN}/{{entry_id}}/documents/{{document_id}}/thumbnail"
    name = f"api:{DOMAIN}:thumbnail"
    thumbnail = True


def download_filename(value: str | None, document_id: int, kind: str) -> str:
    """Keep a useful filename without paths, control characters or header syntax."""
    value = (value or "").replace("\\", "/").rsplit("/", 1)[-1]
    value = re.sub(r"[^\w .()-]", "_", value).strip(" .")[:180]
    if not value:
        value = f"document-{document_id}.{'pdf' if kind == 'pdf' else 'bin'}"
    if kind == "pdf" and not value.lower().endswith(".pdf"):
        value += ".pdf"
    return value


class DownloadView(HomeAssistantView):
    """A real attachment stream; no whole-file byte array or browser Blob."""

    url = f"/api/{DOMAIN}/{{entry_id}}/documents/{{document_id}}/download/{{kind}}"
    name = f"api:{DOMAIN}:download"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str, document_id: str, kind: str):
        user = request.get(KEY_HASS_USER)
        if not can_access(self.hass, entry_id, user):
            return web.Response(status=403, headers=HEADERS)
        if (
            kind not in {"pdf", "original"}
            or not document_id.isascii()
            or not document_id.isdecimal()
            or len(document_id) > 10
            or not 1 <= int(document_id) <= 2147483647
        ):
            return web.Response(status=400, headers=HEADERS)
        client = self.hass.data.get(DOMAIN, {}).get(entry_id)
        if client is None:
            return web.Response(status=404, headers=HEADERS)
        refresh_id = request.get(KEY_HASS_REFRESH_TOKEN_ID)

        def authorized() -> bool:
            return can_access(self.hass, entry_id, user) and (
                not refresh_id or self.hass.auth.async_get_refresh_token(refresh_id) is not None
            )

        stream = None
        try:
            async with client.download(int(document_id), kind) as (upstream, prefix):
                if self.hass.data.get(DOMAIN, {}).get(entry_id) is not client:
                    return web.Response(status=404, headers=HEADERS)
                if not authorized():
                    return web.Response(status=403, headers=HEADERS)
                disposition = upstream.content_disposition
                filename = download_filename(
                    disposition.filename if disposition else None, int(document_id), kind
                )
                stream = web.StreamResponse(
                    headers={
                        **HEADERS,
                        "Content-Type": "application/pdf"
                        if kind == "pdf"
                        else "application/octet-stream",
                        "Content-Disposition": content_disposition_header(
                            "attachment", filename=filename
                        ),
                        "Content-Security-Policy": "sandbox",
                    }
                )
                if upstream.content_length is not None:
                    stream.content_length = upstream.content_length
                await stream.prepare(request)
                if prefix:
                    if (
                        not authorized()
                        or self.hass.data.get(DOMAIN, {}).get(entry_id) is not client
                    ):
                        raise ConnectionError("Download access revoked")
                    await stream.write(prefix)
                async for chunk in upstream.content.iter_chunked(65536):
                    if (
                        self.hass.data.get(DOMAIN, {}).get(entry_id) is not client
                        or not authorized()
                    ):
                        raise ConnectionError("Download access revoked")
                    await stream.write(chunk)
                await stream.write_eof()
                return stream
        except (PaperlessError, ClientError, ConnectionError, asyncio.TimeoutError) as error:
            if stream is not None and stream.prepared:
                if request.transport:
                    request.transport.close()
                return stream
            if isinstance(error, InvalidAuth) and user.is_admin:
                if entry := self.hass.config_entries.async_get_entry(entry_id):
                    entry.async_start_reauth(self.hass)
            status = (
                403
                if isinstance(error, Forbidden)
                else 404
                if isinstance(error, PreviewUnavailable)
                else 429
                if isinstance(error, RateLimited)
                else 502
            )
            return web.Response(status=status, headers=HEADERS)
