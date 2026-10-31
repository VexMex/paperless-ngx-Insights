"""Exercise the registered HTTP route with real HA auth middleware."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.paperless_ngx_insights.client import (
    Forbidden,
    InvalidAuth,
    PreviewTooLarge,
    PreviewUnavailable,
    RateLimited,
)
from custom_components.paperless_ngx_insights.const import DOMAIN


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
    return entry, f"/api/{DOMAIN}/{entry.entry_id}/documents/42/preview"


async def test_preview_authentication_and_admin(
    hass, hass_client, hass_client_no_auth, hass_read_only_access_token
):
    entry, path = await install(hass)
    anonymous = await hass_client_no_auth()
    assert (await anonymous.get(path)).status == 401
    client = await hass_client(hass_read_only_access_token)
    with patch.object(
        hass.data[DOMAIN][entry.entry_id], "preview", new_callable=AsyncMock
    ) as fetch:
        assert (await client.get(path)).status == 403
        fetch.assert_not_awaited()


async def test_pdf_headers_and_body(hass, hass_client, hass_access_token):
    entry, path = await install(hass)
    client = await hass_client(hass_access_token)
    with patch.object(
        hass.data[DOMAIN][entry.entry_id], "preview", return_value=b"%PDF-1.7\nfixture"
    ):
        response = await client.get(path)
    assert response.status == 200
    assert await response.read() == b"%PDF-1.7\nfixture"
    assert response.content_type == "application/pdf"
    assert response.headers["Cache-Control"] == "no-store, private"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "fixture" not in response.headers["Content-Disposition"]


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (Forbidden(), 403),
        (PreviewTooLarge(), 413),
        (PreviewUnavailable(), 415),
        (RateLimited(), 429),
        (InvalidAuth(), 502),
    ],
)
async def test_errors_are_safe(hass, hass_client, hass_access_token, error, status):
    entry, path = await install(hass)
    client = await hass_client(hass_access_token)
    with patch.object(hass.data[DOMAIN][entry.entry_id], "preview", side_effect=error):
        response = await client.get(path)
    assert response.status == status
    assert await response.read() == b""


async def test_ids_and_unload_during_request(hass, hass_client, hass_access_token):
    entry, path = await install(hass)
    client = await hass_client(hass_access_token)
    upstream = hass.data[DOMAIN][entry.entry_id]
    with patch.object(upstream, "preview", new_callable=AsyncMock) as fetch:
        for number in ["0", "-1", "2147483648", "abc"]:
            assert (await client.get(path.replace("/42/", f"/{number}/"))).status == 400
        fetch.assert_not_awaited()

    async def unloaded(_):
        hass.data[DOMAIN].pop(entry.entry_id)
        return b"%PDF-fixture"

    with patch.object(upstream, "preview", side_effect=unloaded):
        assert (await client.get(path)).status == 403
    assert (await client.get(path)).status == 404
