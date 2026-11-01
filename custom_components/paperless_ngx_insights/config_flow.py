"""UI configuration for Home Assistant 2026.10 and later."""

from collections.abc import Mapping
from typing import Any

import probatio
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import (
    CannotConnect,
    Forbidden,
    InvalidAddress,
    InvalidAuth,
    InvalidResponse,
    PaperlessClient,
    RateLimited,
    normalize_url,
    validate_token,
)
from .const import CONF_TOKEN, CONF_URL, CONF_WEB_URL, DOMAIN


def connection_schema(
    defaults: Mapping[str, Any] | None = None, *, reconfigure: bool = False
) -> probatio.Schema:
    """Never prefill the token in a browser-visible form."""
    values = defaults or {}
    return probatio.Schema(
        {
            probatio.Required(CONF_URL, default=values.get(CONF_URL, "")): str,
            (probatio.Optional if reconfigure else probatio.Required)(
                probatio.Secret(CONF_TOKEN)
            ): str,
            probatio.Optional(CONF_WEB_URL, default=values.get(CONF_WEB_URL, "")): str,
        }
    )


class PaperlessInsightsConfigFlow(ConfigFlow, domain=DOMAIN):
    """One entry per normalized Paperless address."""

    VERSION = 1

    async def _validate(self, user_input: dict[str, Any]) -> tuple[dict, dict[str, str]]:
        try:
            data = {
                CONF_URL: normalize_url(user_input[CONF_URL]),
                CONF_TOKEN: validate_token(user_input[CONF_TOKEN]),
                CONF_WEB_URL: (
                    normalize_url(user_input[CONF_WEB_URL])
                    if user_input.get(CONF_WEB_URL, "").strip()
                    else ""
                ),
            }
            client = PaperlessClient(
                async_get_clientsession(self.hass), data[CONF_URL], data[CONF_TOKEN]
            )
            await client.validate_connection()
        except InvalidAddress:
            return {}, {"base": "invalid_url"}
        except InvalidAuth:
            return {}, {"base": "invalid_auth"}
        except Forbidden:
            return {}, {"base": "forbidden"}
        except (CannotConnect, RateLimited):
            return {}, {"base": "cannot_connect"}
        except InvalidResponse:
            return {}, {"base": "invalid_response"}
        return data, {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Check credentials before creating an entry."""
        errors = {}
        if user_input is not None:
            data, errors = await self._validate(user_input)
            if not errors:
                await self.async_set_unique_id(data[CONF_URL])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Paperless-ngx Insights", data=data)
        return self.async_show_form(
            step_id="user", data_schema=connection_schema(user_input), errors=errors
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Start token renewal without exposing the existing token."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors = {}
        if user_input is not None:
            data, errors = await self._validate({**entry.data, **user_input})
            if not errors:
                return self.async_update_reload_and_abort(entry, data_updates=data)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=probatio.Schema({probatio.Required(probatio.Secret(CONF_TOKEN)): str}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change server address or credentials; check duplicates first."""
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            values = {**entry.data, **user_input}
            if not user_input.get(CONF_TOKEN, "").strip():
                values[CONF_TOKEN] = entry.data[CONF_TOKEN]
            data, errors = await self._validate(values)
            if not errors:
                if any(
                    other.entry_id != entry.entry_id and other.unique_id == data[CONF_URL]
                    for other in self._async_current_entries()
                ):
                    return self.async_abort(reason="already_configured")
                self.hass.config_entries.async_update_entry(entry, unique_id=data[CONF_URL])
                return self.async_update_reload_and_abort(entry, data_updates=data)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=connection_schema(user_input or entry.data, reconfigure=True),
            errors=errors,
        )
