"""Config flow for Birthday Calendar integration."""

from __future__ import annotations

import logging
from hashlib import sha256
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CALENDAR_NAME,
    CONF_DAYS,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CALENDAR_NAME, default="Birthdays"): str,
        vol.Required(CONF_URL): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_DAYS, default=30): int,
    }
)


def _entry_unique_id(data: dict[str, Any]) -> str:
    """Return a stable, non-sensitive identifier for an address book."""
    identifier = f"{data[CONF_URL].rstrip('/')}\0{data[CONF_USERNAME]}"
    return sha256(identifier.encode()).hexdigest()


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)

    try:
        async with session.request(
            "PROPFIND",
            data[CONF_URL],
            headers={
                "Depth": "0",
                "Authorization": aiohttp.encode_basic_auth(
                    data[CONF_USERNAME], data[CONF_PASSWORD]
                ),
            },
        ) as response:
            if response.status == 401:
                raise InvalidAuth
            # 200 and 207 are successful CardDAV responses
            if response.status not in (200, 207):
                raise CannotConnect
    except aiohttp.ClientError as exc:
        raise CannotConnect from exc

    return {"title": data[CONF_CALENDAR_NAME]}


# pylint: disable=abstract-method
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Birthday Calendar."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(_entry_unique_id(user_input))
            self._abort_if_unique_id_configured()
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
