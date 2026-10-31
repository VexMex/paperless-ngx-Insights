"""Real HA framework tests: config flow, lifecycle, diagnostics and access gates."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import Unauthorized
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.paperless_ngx_insights.client import (
    CannotConnect,
    Forbidden,
    InvalidAuth,
    InvalidResponse,
)
from custom_components.paperless_ngx_insights.const import DOMAIN
from custom_components.paperless_ngx_insights.diagnostics import async_get_config_entry_diagnostics
from custom_components.paperless_ngx_insights.websocket import websocket_entries, websocket_search

DATA = {"url": "http://paperless.test:8810", "token": "fixture-token", "web_url": ""}
VALIDATE = f"custom_components.{DOMAIN}.client.PaperlessClient.validate_connection"


async def start_form(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    return result


async def test_user_flow(hass):
    result = await start_form(hass)
    with (
        patch(VALIDATE, new_callable=AsyncMock),
        patch(f"custom_components.{DOMAIN}.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == DATA
    assert result["result"].unique_id == DATA["url"]


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (InvalidAuth(), "invalid_auth"),
        (Forbidden(), "forbidden"),
        (CannotConnect(), "cannot_connect"),
        (InvalidResponse(), "invalid_response"),
    ],
)
async def test_flow_errors(hass, error, code):
    result = await start_form(hass)
    with patch(VALIDATE, side_effect=error):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": code}


async def test_duplicate(hass):
    MockConfigEntry(domain=DOMAIN, unique_id=DATA["url"], data=DATA).add_to_hass(hass)
    result = await start_form(hass)
    with patch(VALIDATE, new_callable=AsyncMock):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_setup_unload_and_diagnostics(hass):
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DATA["url"], data=DATA)
    entry.add_to_hass(hass)
    with patch(VALIDATE, new_callable=AsyncMock):
        assert await hass.config_entries.async_setup(entry.entry_id)
    client = hass.data[DOMAIN][entry.entry_id]
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["loaded"] is True
    assert "fixture-token" not in str(diagnostics)
    assert DATA["url"] not in str(diagnostics)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.entry_id not in hass.data[DOMAIN]
    with pytest.raises(CannotConnect):
        await client.search("invoice")


@pytest.mark.parametrize("user", [None, SimpleNamespace(is_admin=False)])
@pytest.mark.parametrize("handler", [websocket_entries, websocket_search])
def test_commands_reject_non_admin(user, handler):
    with pytest.raises(Unauthorized):
        handler(None, SimpleNamespace(user=user), {"id": 1})


@pytest.mark.parametrize("source", [SOURCE_REAUTH, SOURCE_RECONFIGURE])
async def test_reauth_and_reconfigure(hass, source):
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DATA["url"], data=DATA)
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source, "entry_id": entry.entry_id},
        data=DATA if source == SOURCE_REAUTH else None,
    )
    assert result["type"] is FlowResultType.FORM
    new_data = {**DATA, "token": "replacement-token"}
    user_input = {"token": "replacement-token"} if source == SOURCE_REAUTH else new_data
    with (
        patch(VALIDATE, new_callable=AsyncMock),
        patch.object(hass.config_entries, "async_reload", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input)
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert entry.data["token"] == "replacement-token"
