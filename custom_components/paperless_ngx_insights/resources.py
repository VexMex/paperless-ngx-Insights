"""Versioned Lovelace resource management through HA's resource collection."""

import asyncio
import logging
from urllib.parse import urlsplit

from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
FRONTEND_PATH = f"/{DOMAIN}/frontend/paperless-ngx-insights.js"


async def async_manage_resource(hass: HomeAssistant, *, remove: bool = False) -> None:
    """Keep one versioned module; never edit YAML resources or other modules."""
    lock = hass.data.setdefault(f"{DOMAIN}_resource_lock", asyncio.Lock())
    async with lock:
        collection = hass.data[LOVELACE_DATA].resources
        if not isinstance(collection, ResourceStorageCollection):
            if not remove:
                _LOGGER.warning("YAML resources: register the Paperless card module manually")
            return
        await collection.async_get_info()
        owned = []
        for item in collection.async_items():
            url = urlsplit(item.get("url", ""))
            if not url.scheme and not url.netloc and url.path == FRONTEND_PATH:
                owned.append(item)
        if remove:
            for item in owned:
                await collection.async_delete_item(item["id"])
            return
        version = (await async_get_integration(hass, DOMAIN)).version
        url = f"{FRONTEND_PATH}?v={version}"
        if owned:
            if owned[0]["url"] != url or owned[0]["type"] != "module":
                await collection.async_update_item(
                    owned[0]["id"], {"url": url, "res_type": "module"}
                )
            for duplicate in owned[1:]:
                await collection.async_delete_item(duplicate["id"])
        else:
            await collection.async_create_item({"url": url, "res_type": "module"})
