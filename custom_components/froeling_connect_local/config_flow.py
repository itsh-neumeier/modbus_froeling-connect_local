"""Config flow for Froeling Connect local."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BOILER_POWER_KW,
    CONF_BUFFER_LITERS,
    CONF_HAS_BUFFER,
    CONF_HAS_DHW,
    CONF_HAS_DHW_HEAT_PUMP,
    CONF_HEATING_CIRCUITS,
    CONF_NAME,
    CONF_PROFILE,
    CONF_SCAN_INTERVAL,
    CONF_SCHEMA_VERSION,
    CONF_SLAVE,
    CONF_TIMEOUT,
    CONFIG_SCHEMA_VERSION,
    DEFAULT_BOILER_POWER_KW,
    DEFAULT_BUFFER_LITERS,
    DEFAULT_HAS_BUFFER,
    DEFAULT_HAS_DHW,
    DEFAULT_HAS_DHW_HEAT_PUMP,
    DEFAULT_HEATING_CIRCUITS,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_PROFILE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import async_probe_connection
from .device_profile import ProfileError, list_profiles, load_profile


class FroelingConnectLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Froeling Connect local."""

    VERSION = CONFIG_SCHEMA_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get options flow for this handler."""
        return FroelingConnectLocalOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._validate_input(user_input)
            if not errors:
                unique_id = _build_unique_id(
                    host=user_input[CONF_HOST],
                    port=user_input[CONF_PORT],
                    slave=user_input[CONF_SLAVE],
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={**user_input, CONF_SCHEMA_VERSION: CONFIG_SCHEMA_VERSION},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
        )

    async def _validate_input(self, user_input: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}

        try:
            profile = load_profile(str(user_input[CONF_PROFILE]))
        except ProfileError:
            errors["base"] = "invalid_profile"
            return errors

        probe_entity = next(iter(profile.entities.values()), None)
        if probe_entity is None:
            errors["base"] = "invalid_profile"
            return errors

        try:
            await async_probe_connection(
                hass=self.hass,
                host=str(user_input[CONF_HOST]),
                port=int(user_input[CONF_PORT]),
                slave=int(user_input[CONF_SLAVE]),
                connect_timeout=int(user_input[CONF_TIMEOUT]),
                register_type=probe_entity.register_type,
                probe_register=probe_entity.register,
            )
        except Exception:
            errors["base"] = "cannot_connect"

        return errors


class FroelingConnectLocalOptionsFlow(OptionsFlow):
    """Handle options for an existing entry."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._validate_input(user_input)
            if not errors:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=user_input[CONF_NAME],
                    data={
                        **self.config_entry.data,
                        **user_input,
                        CONF_SCHEMA_VERSION: CONFIG_SCHEMA_VERSION,
                    },
                )
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})

        defaults = user_input or self.config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(defaults),
            errors=errors,
        )

    async def _validate_input(self, user_input: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}

        try:
            profile = load_profile(str(user_input[CONF_PROFILE]))
        except ProfileError:
            errors["base"] = "invalid_profile"
            return errors

        probe_entity = next(iter(profile.entities.values()), None)
        if probe_entity is None:
            errors["base"] = "invalid_profile"
            return errors

        try:
            await async_probe_connection(
                hass=self.hass,
                host=str(user_input[CONF_HOST]),
                port=int(user_input[CONF_PORT]),
                slave=int(user_input[CONF_SLAVE]),
                connect_timeout=int(user_input[CONF_TIMEOUT]),
                register_type=probe_entity.register_type,
                probe_register=probe_entity.register,
            )
        except Exception:
            errors["base"] = "cannot_connect"

        return errors


def _build_unique_id(host: str, port: int, slave: int) -> str:
    return f"{host}:{port}:{slave}"


def _build_schema(defaults: dict[str, Any] | None) -> vol.Schema:
    profile_choices = list_profiles()
    data = defaults or {}

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): str,
            vol.Required(CONF_PORT, default=data.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                int,
                vol.Range(min=1, max=65535),
            ),
            vol.Required(CONF_SLAVE, default=data.get(CONF_SLAVE, DEFAULT_SLAVE)): vol.All(
                int,
                vol.Range(min=1, max=247),
            ),
            vol.Required(
                CONF_HEATING_CIRCUITS,
                default=data.get(CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=2,
                    mode=selector.NumberSelectorMode.BOX,
                    step=1,
                ),
            ),
            vol.Required(CONF_HAS_DHW, default=data.get(CONF_HAS_DHW, DEFAULT_HAS_DHW)): bool,
            vol.Required(
                CONF_HAS_BUFFER,
                default=data.get(CONF_HAS_BUFFER, DEFAULT_HAS_BUFFER),
            ): bool,
            vol.Required(
                CONF_HAS_DHW_HEAT_PUMP,
                default=data.get(CONF_HAS_DHW_HEAT_PUMP, DEFAULT_HAS_DHW_HEAT_PUMP),
            ): bool,
            vol.Required(
                CONF_BUFFER_LITERS,
                default=data.get(CONF_BUFFER_LITERS, DEFAULT_BUFFER_LITERS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=100,
                    max=10000,
                    mode=selector.NumberSelectorMode.BOX,
                    step=10,
                    unit_of_measurement="L",
                ),
            ),
            vol.Required(
                CONF_BOILER_POWER_KW,
                default=data.get(CONF_BOILER_POWER_KW, DEFAULT_BOILER_POWER_KW),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=100,
                    mode=selector.NumberSelectorMode.BOX,
                    step=0.5,
                    unit_of_measurement="kW",
                ),
            ),
            vol.Required(
                CONF_PROFILE,
                default=data.get(CONF_PROFILE, DEFAULT_PROFILE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=profile_id, label=label)
                        for profile_id, label in profile_choices.items()
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)),
            vol.Required(CONF_TIMEOUT, default=data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)): vol.All(
                int,
                vol.Range(min=2, max=30),
            ),
        }
    )
