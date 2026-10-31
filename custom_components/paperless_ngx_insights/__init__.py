"""Set up the read-only Paperless-ngx Insights integration."""

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .client import Forbidden, InvalidAuth, InvalidResponse, PaperlessClient, PaperlessError
from .const import CONF_TOKEN, CONF_URL, DOMAIN
from .http import PreviewView, ThumbnailView
from .websocket import async_register_commands

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register API commands once; all requests still require a loaded entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/{DOMAIN}/frontend", str(Path(__file__).parent / "www"), True)]
    )
    async_register_commands(hass)
    hass.http.register_view(PreviewView(hass))
    hass.http.register_view(ThumbnailView(hass))
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Validate access before making this entry available to cards."""
    client = PaperlessClient(
        async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_TOKEN]
    )
    try:
        await client.validate_connection()
    except InvalidAuth as err:
        raise ConfigEntryAuthFailed("Paperless API token rejected") from err
    except (Forbidden, InvalidResponse) as err:
        raise ConfigEntryError("Paperless API access or response is invalid") from err
    except PaperlessError as err:
        raise ConfigEntryNotReady("Paperless is temporarily unavailable") from err
    entry.runtime_data = client
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove access without closing Home Assistant's shared HTTP session."""
    if client := hass.data.get(DOMAIN, {}).pop(entry.entry_id, None):
        client.close()
    return True
