"""Minimal diagnostics deliberately excluding URLs, tokens, and document data."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    return {
        "loaded": entry.entry_id in hass.data.get(DOMAIN, {}),
        "access": "administrators_only",
        "document_cache": False,
        "search_mode": "multiword_and_single_substring",
    }
