"""On-demand document API with per-connection access checks."""

from datetime import timedelta
from typing import Any
from urllib.parse import quote

import probatio
from homeassistant.components import websocket_api
from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import HomeAssistant, callback

from .access import can_access
from .client import InvalidAuth, PaperlessError
from .const import CONF_URL, CONF_WEB_URL, DOMAIN, MAX_PAGE_SIZE, MAX_SEARCH_LENGTH


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, websocket_entries)
    websocket_api.async_register_command(hass, websocket_search)
    websocket_api.async_register_command(hass, websocket_download)


@websocket_api.websocket_command({probatio.Required("type"): f"{DOMAIN}/entries"})
def websocket_entries(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return configured, loaded entries without credentials or API addresses."""
    loaded = hass.data.get(DOMAIN, {})
    connection.send_result(
        msg["id"],
        [
            {"entry_id": entry.entry_id, "title": entry.title}
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.entry_id in loaded and can_access(hass, entry.entry_id, connection.user)
        ],
    )


@websocket_api.websocket_command(
    {
        probatio.Required("type"): f"{DOMAIN}/search",
        probatio.Required("entry_id"): str,
        probatio.Required("text"): probatio.All(str, probatio.Length(max=MAX_SEARCH_LENGTH)),
        probatio.Optional("mode", default="title"): probatio.In(["title", "text"]),
        probatio.Optional("page", default=1): probatio.All(int, probatio.Range(min=1, max=100000)),
        probatio.Optional("page_size", default=5): probatio.All(
            int, probatio.Range(min=1, max=MAX_PAGE_SIZE)
        ),
    }
)
@websocket_api.async_response
async def websocket_search(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Execute an isolated search; never store document content as entity state."""
    entry_id = msg["entry_id"]
    if not can_access(hass, entry_id, connection.user):
        connection.send_error(msg["id"], "unauthorized", "No access to this Paperless connection")
        return
    client = hass.data.get(DOMAIN, {}).get(entry_id)
    if client is None:
        connection.send_error(msg["id"], "not_loaded", "Paperless integration is not loaded")
        return
    try:
        result = await client.search(
            msg["text"], mode=msg["mode"], page=msg["page"], page_size=msg["page_size"]
        )
    except InvalidAuth:
        if connection.user.is_admin:
            if entry := hass.config_entries.async_get_entry(entry_id):
                entry.async_start_reauth(hass)
        connection.send_error(msg["id"], "invalid_auth", "Paperless authentication required")
        return
    except ValueError:
        connection.send_error(
            msg["id"],
            "invalid_search",
            "Check double quotes and use at most 32 search terms",
        )
        return
    except PaperlessError:
        connection.send_error(msg["id"], "search_failed", "Unable to search Paperless documents")
        return
    # A reload/unload during the request must not send a stale entry's results.
    if not can_access(hass, entry_id, connection.user):
        connection.send_error(msg["id"], "unauthorized", "No access to this Paperless connection")
        return
    if hass.data.get(DOMAIN, {}).get(entry_id) is not client:
        connection.send_error(msg["id"], "not_loaded", "Paperless integration was reloaded")
        return
    payload = result.as_dict()
    entry = hass.config_entries.async_get_entry(entry_id)
    payload["web_url"] = entry.data.get(CONF_WEB_URL) or entry.data[CONF_URL]
    connection.send_result(msg["id"], payload)


@websocket_api.websocket_command(
    {
        probatio.Required("type"): f"{DOMAIN}/download",
        probatio.Required("entry_id"): str,
        probatio.Required("document_id"): probatio.All(int, probatio.Range(min=1, max=2147483647)),
        probatio.Optional("kind", default="pdf"): probatio.In(["pdf", "original"]),
    }
)
def websocket_download(hass, connection, msg):
    """Issue a 30-second path bound to this HA login, never a Paperless token."""
    if not can_access(hass, msg["entry_id"], connection.user):
        connection.send_error(msg["id"], "unauthorized", "No access to this Paperless connection")
        return
    if type(msg["document_id"]) is not int or not connection.refresh_token_id:
        connection.send_error(msg["id"], "invalid_download", "A regular HA login is required")
        return
    if msg["entry_id"] not in hass.data.get(DOMAIN, {}):
        connection.send_error(msg["id"], "not_loaded", "Paperless integration is not loaded")
        return
    path = (
        f"/api/{DOMAIN}/{quote(msg['entry_id'], safe='')}/documents/"
        f"{msg['document_id']}/download/{msg['kind']}"
    )
    connection.send_result(
        msg["id"],
        {
            "url": async_sign_path(
                hass, path, timedelta(seconds=30), refresh_token_id=connection.refresh_token_id
            ),
            "expires_in": 30,
        },
    )
