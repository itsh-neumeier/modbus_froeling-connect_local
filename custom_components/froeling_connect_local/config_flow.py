"""Config flow for Froeling Connect local."""

from __future__ import annotations

import inspect
import logging
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

_LOGGER = logging.getLogger(__name__)


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
    try:
        profile_choices = list_profiles()
    except Exception as err:  # pragma: no cover - defensive fallback for UI stability
        _LOGGER.exception("Unable to list device profiles, falling back to default: %s", err)
        profile_choices = {DEFAULT_PROFILE: DEFAULT_PROFILE}

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
            ): _number_selector(min_value=1, max_value=2, step=1, integer=True),
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
            ): _number_selector(min_value=100, max_value=10000, step=10, integer=True, unit="L"),
            vol.Required(
                CONF_BOILER_POWER_KW,
                default=data.get(CONF_BOILER_POWER_KW, DEFAULT_BOILER_POWER_KW),
            ): _number_selector(
                min_value=1,
                max_value=100,
                step=0.5,
                integer=False,
                unit="kW",
            ),
            vol.Required(
                CONF_PROFILE,
                default=data.get(CONF_PROFILE, DEFAULT_PROFILE),
            ): _profile_selector(profile_choices),
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


def _supports_kwarg(factory: Any, kwarg: str) -> bool:
    """Return True if a callable supports the given named argument."""
    try:
        return kwarg in inspect.signature(factory).parameters
    except (TypeError, ValueError):
        return False


def _number_selector(
    *,
    min_value: float,
    max_value: float,
    step: float,
    integer: bool,
    unit: str | None = None,
):
    """Build a NumberSelector with HA-version-compatible fallbacks."""
    number_selector = getattr(selector, "NumberSelector", None)
    number_selector_config = getattr(selector, "NumberSelectorConfig", None)
    if number_selector and number_selector_config:
        mode_enum = getattr(selector, "NumberSelectorMode", None)
        mode = getattr(mode_enum, "BOX", "box")
        kwargs: dict[str, Any] = {
            "min": min_value,
            "max": max_value,
            "mode": mode,
            "step": step,
        }
        if unit is not None and _supports_kwarg(number_selector_config, "unit_of_measurement"):
            kwargs["unit_of_measurement"] = unit
        try:
            return number_selector(number_selector_config(**kwargs))
        except Exception as err:  # pragma: no cover - defensive fallback
            _LOGGER.debug("Falling back from NumberSelector due to: %s", err)

    coerce = int if integer else vol.Coerce(float)
    return vol.All(coerce, vol.Range(min=min_value, max=max_value))


def _profile_selector(profile_choices: dict[str, str]):
    """Build a profile selector with compatibility fallback."""
    select_selector = getattr(selector, "SelectSelector", None)
    select_selector_config = getattr(selector, "SelectSelectorConfig", None)
    if select_selector and select_selector_config:
        mode_enum = getattr(selector, "SelectSelectorMode", None)
        mode = getattr(mode_enum, "DROPDOWN", "dropdown")
        option_dict = getattr(selector, "SelectOptionDict", None)
        if option_dict:
            options = [
                option_dict(value=profile_id, label=label)
                for profile_id, label in profile_choices.items()
            ]
        else:
            options = list(profile_choices.keys())
        try:
            return select_selector(
                select_selector_config(
                    options=options,
                    mode=mode,
                )
            )
        except Exception as err:  # pragma: no cover - defensive fallback
            _LOGGER.debug("Falling back from SelectSelector due to: %s", err)

    return vol.In(profile_choices)
