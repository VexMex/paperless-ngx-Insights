"""Authenticated PDF previews; no public URLs or upstream credentials in URLs."""

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.http.const import KEY_HASS_USER
from homeassistant.core import HomeAssistant

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

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str, document_id: str) -> web.Response:
        user = request.get(KEY_HASS_USER)
        if user is None or not user.is_admin or not user.is_active:
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
            body = await client.preview(number)
        except InvalidAuth:
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
        if (
            self.hass.data.get(DOMAIN, {}).get(entry_id) is not client
            or not user.is_active
            or not user.is_admin
        ):
            return web.Response(status=403, headers=HEADERS)
        return web.Response(
            body=body,
            content_type="application/pdf",
            headers={**HEADERS, "Content-Disposition": 'inline; filename="preview.pdf"'},
        )
