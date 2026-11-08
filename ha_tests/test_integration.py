"""Real HA framework tests: config flow, lifecycle, diagnostics and access gates."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.paperless_ngx_insights.client import (
    CannotConnect,
    Forbidden,
    InvalidAuth,
    InvalidResponse,
)
from custom_components.paperless_ngx_insights.const import CONF_ALLOWED_USERS, DOMAIN
from custom_components.paperless_ngx_insights.diagnostics import async_get_config_entry_diagnostics

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


async def test_search_and_entry_list_respect_sharing(
    hass, hass_ws_client, hass_read_only_access_token, hass_read_only_user
):
    shared = MockConfigEntry(
        domain=DOMAIN,
        data=DATA,
        options={CONF_ALLOWED_USERS: [hass_read_only_user.id]},
    )
    private = MockConfigEntry(domain=DOMAIN, data=DATA)
    with patch(VALIDATE, new_callable=AsyncMock):
        for entry in (shared, private):
            entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(entry.entry_id)
    ws = await hass_ws_client(hass, access_token=hass_read_only_access_token)

    async def command(number, kind, **kwargs):
        await ws.send_json({"id": number, "type": f"{DOMAIN}/{kind}", **kwargs})
        return await ws.receive_json()

    listed = await command(1, "entries")
    assert listed["result"] == [{"entry_id": shared.entry_id, "title": shared.title}]
    denied = await command(2, "search", entry_id=private.entry_id, text="")
    assert denied["error"]["code"] == "unauthorized"

    class SearchResult:
        def as_dict(self):
            return {"count": 0, "documents": []}

    async def revoke_during_search(*args, **kwargs):
        hass.config_entries.async_update_entry(shared, options={})
        return SearchResult()

    client = hass.data[DOMAIN][shared.entry_id]
    with patch.object(client, "search", return_value=SearchResult()):
        assert (await command(3, "search", entry_id=shared.entry_id, text=""))["success"]
    with patch.object(client, "search", side_effect=revoke_during_search):
        denied = await command(4, "search", entry_id=shared.entry_id, text="")
        assert denied["error"]["code"] == "unauthorized"
    assert (await command(5, "entries"))["result"] == []


@pytest.mark.parametrize(
    ("source", "change"),
    [
        (SOURCE_REAUTH, {"token": "replacement-token"}),
        (SOURCE_RECONFIGURE, {"token": "replacement-token"}),
        (SOURCE_RECONFIGURE, {"url": "http://new-paperless.test"}),
    ],
)
async def test_reauth_and_reconfigure(hass, source, change):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DATA["url"],
        data=DATA,
        options={CONF_ALLOWED_USERS: ["shared-user"]},
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source, "entry_id": entry.entry_id},
        data=DATA if source == SOURCE_REAUTH else None,
    )
    assert result["type"] is FlowResultType.FORM
    new_data = {**DATA, **change}
    user_input = change if source == SOURCE_REAUTH else new_data
    with (
        patch(VALIDATE, new_callable=AsyncMock),
        patch.object(hass.config_entries, "async_reload", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input)
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert entry.data == new_data
    assert CONF_ALLOWED_USERS not in entry.options


@pytest.mark.parametrize("token", [None, "", "   "])
async def test_reconfigure_can_retain_secret(hass, token):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DATA["url"],
        data=DATA,
        options={CONF_ALLOWED_USERS: ["shared-user"]},
    )
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
    assert entry.options[CONF_ALLOWED_USERS] == ["shared-user"]


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
    from homeassistant.loader import async_get_integration

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
        assert await hass.config_entries.async_setup(entries[0].entry_id)
        await hass.async_block_till_done()
        assert entries[1].state.value == "loaded"
        collection = hass.data[LOVELACE_DATA].resources
        own = list(collection.async_items())
        assert len(own) == 1
        resource_id = own[0]["id"]
        version = (await async_get_integration(hass, DOMAIN)).version
        assert own[0]["url"].endswith("?v=" + version)
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
        ].endswith("?v=" + version)
        assert await hass.config_entries.async_remove(entries[0].entry_id)
        assert len(list(collection.async_items())) == 2
        assert await hass.config_entries.async_remove(entries[1].entry_id)
        assert [item["id"] for item in collection.async_items()] == [unrelated["id"]]
