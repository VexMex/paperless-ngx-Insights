"""Real HA authentication, signed-path expiry and streaming attachment contract."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.paperless_ngx_insights.const import DOMAIN
from custom_components.paperless_ngx_insights.http import download_filename


async def install(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"url": "http://paperless.test", "token": "fixture"}
    )
    entry.add_to_hass(hass)
    with patch(
        f"custom_components.{DOMAIN}.client.PaperlessClient.validate_connection",
        new_callable=AsyncMock,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
    return entry, f"/api/{DOMAIN}/{entry.entry_id}/documents/42/download/pdf"


@asynccontextmanager
async def synthetic_download(number, kind):
    async def chunks(size):
        assert size == 65536
        for _ in range(400):
            yield b"x" * size

    yield (
        SimpleNamespace(
            content_length=5 + 400 * 65536,
            content=SimpleNamespace(iter_chunked=chunks),
            content_disposition=SimpleNamespace(filename="../../evil\r\n.html"),
        ),
        b"%PDF-",
    )


async def test_signed_download_stream_and_expiry(
    hass, hass_ws_client, hass_client_no_auth, freezer
):
    entry, path = await install(hass)
    ws = await hass_ws_client(hass)
    await ws.send_json(
        {
            "id": 1,
            "type": DOMAIN + "/download",
            "entry_id": entry.entry_id,
            "document_id": 42,
            "kind": "pdf",
        }
    )
    result = await ws.receive_json()
    assert result["success"]
    signed = result["result"]["url"]
    assert signed.startswith(path + "?authSig=")
    client = await hass_client_no_auth()
    assert (await client.get(path)).status == 401
    assert (await client.get(signed.replace("/42/", "/43/"))).status == 401
    with patch.object(hass.data[DOMAIN][entry.entry_id], "download", synthetic_download):
        response = await client.get(signed)
        assert response.status == 200
        assert response.content_type == "application/pdf"
        assert response.headers["Content-Disposition"].startswith("attachment;")
        assert "\r" not in response.headers["Content-Disposition"]
        assert response.headers["Cache-Control"] == "no-store, private"
        total = 0
        async for chunk in response.content.iter_chunked(65536):
            total += len(chunk)
        assert total == 5 + 400 * 65536
    freezer.tick(31)
    assert (await client.get(signed)).status == 401


async def test_non_admin_cannot_sign_or_download(
    hass, hass_ws_client, hass_client, hass_read_only_access_token
):
    entry, path = await install(hass)
    ws = await hass_ws_client(hass, access_token=hass_read_only_access_token)
    await ws.send_json(
        {"id": 1, "type": DOMAIN + "/download", "entry_id": entry.entry_id, "document_id": 42}
    )
    assert (await ws.receive_json())["success"] is False
    client = await hass_client(hass_read_only_access_token)
    assert (await client.get(path)).status == 403


async def test_download_unloaded_entry_and_invalid_id(hass, hass_client, hass_access_token):
    entry, path = await install(hass)
    client = await hass_client(hass_access_token)
    assert (await client.get(path.replace("/42/", "/0/"))).status == 400
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert (await client.get(path)).status == 404


@pytest.mark.parametrize(
    "value", [None, "../", 'a\r\n";evil.exe', "C:\\folder\\report.pdf", "../../Rechnung ä.pdf"]
)
def test_safe_filename(value):
    name = download_filename(value, 42, "pdf")
    assert name.endswith(".pdf")
    assert not any(char in name for char in '\r\n/\\"')
