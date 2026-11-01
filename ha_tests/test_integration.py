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


@pytest.mark.parametrize("token", [None, "", "   "])
async def test_reconfigure_can_retain_secret(hass, token):
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DATA["url"], data=DATA)
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    assert "fixture-token" not in str(result)
    values = {"url": DATA["url"], "web_url": "https://paperless.browser.test"}
    if token is not None:
        values["token"] = token
    with (
        patch(VALIDATE, new_callable=AsyncMock),
        patch.object(hass.config_entries, "async_reload", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], values)
    assert result["type"] is FlowResultType.ABORT
    assert entry.data["token"] == DATA["token"]
    assert entry.data["web_url"] == values["web_url"]


@pytest.mark.parametrize("source", [SOURCE_RECONFIGURE, SOURCE_REAUTH])
async def test_invalid_update_preserves_working_connection(hass, source):
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DATA["url"], data=DATA)
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source, "entry_id": entry.entry_id},
        data=DATA if source == SOURCE_REAUTH else None,
    )
    with (
        patch(VALIDATE, side_effect=InvalidAuth()),
        patch.object(hass.config_entries, "async_reload", new_callable=AsyncMock) as reload,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**DATA, "token": "invalid-fixture"}
            if source == SOURCE_RECONFIGURE
            else {"token": "invalid-fixture"},
        )
    assert result["errors"] == {"base": "invalid_auth"}
    assert entry.data == DATA
    reload.assert_not_awaited()


async def test_reload_resources_and_remove_last_entry(hass):
    from homeassistant.components.lovelace.const import LOVELACE_DATA

    entries = [
        MockConfigEntry(
            domain=DOMAIN,
            unique_id=f"http://fixture-{i}.test",
            data={**DATA, "url": f"http://fixture-{i}.test"},
        )
        for i in range(2)
    ]
    for entry in entries:
        entry.add_to_hass(hass)
    with patch(VALIDATE, new_callable=AsyncMock):
        for entry in entries:
            assert await hass.config_entries.async_setup(entry.entry_id)
        collection = hass.data[LOVELACE_DATA].resources
        own = list(collection.async_items())
        assert len(own) == 1
        resource_id = own[0]["id"]
        assert own[0]["url"].endswith("?v=0.1.0-dev.6")
        await collection.async_update_item(
            resource_id, {"url": own[0]["url"].split("?")[0] + "?v=old"}
        )
        unrelated = await collection.async_create_item(
            {"url": "/local/unrelated.js", "res_type": "module"}
        )
        old_client = entries[0].runtime_data
        assert await hass.config_entries.async_reload(entries[0].entry_id)
        assert entries[0].runtime_data is not old_client
        with pytest.raises(CannotConnect):
            await old_client.search("old")
        assert len(list(collection.async_items())) == 2
        assert next(item for item in collection.async_items() if item["id"] == resource_id)[
            "url"
        ].endswith("?v=0.1.0-dev.6")
        assert await hass.config_entries.async_remove(entries[0].entry_id)
        assert len(list(collection.async_items())) == 2
        assert await hass.config_entries.async_remove(entries[1].entry_id)
        assert [item["id"] for item in collection.async_items()] == [unrelated["id"]]
