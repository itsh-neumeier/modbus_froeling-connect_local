"""The Froeling Connect local integration."""

from __future__ import annotations

import logging

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
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
    PLATFORMS,
)
from .coordinator import FroelingLocalDataUpdateCoordinator
from .device_profile import ProfileError, apply_installation_options, load_profile

_LOGGER = logging.getLogger(__name__)


FroelingConfigEntry = ConfigEntry[FroelingLocalDataUpdateCoordinator]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up integration from YAML (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: FroelingConfigEntry) -> bool:
    """Set up Froeling Connect local from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    try:
        base_profile = load_profile(str(entry.data[CONF_PROFILE]))
        profile = apply_installation_options(
            base_profile,
            heating_circuits=int(
                entry.data.get(CONF_HEATING_CIRCUITS, DEFAULT_HEATING_CIRCUITS),
            ),
            has_dhw=bool(entry.data.get(CONF_HAS_DHW, DEFAULT_HAS_DHW)),
            has_buffer=bool(entry.data.get(CONF_HAS_BUFFER, DEFAULT_HAS_BUFFER)),
            has_dhw_heat_pump=bool(
                entry.data.get(CONF_HAS_DHW_HEAT_PUMP, DEFAULT_HAS_DHW_HEAT_PUMP),
            ),
        )
    except ProfileError as err:
        raise ConfigEntryNotReady(f"Invalid profile '{entry.data.get(CONF_PROFILE)}': {err}") from err

    coordinator = FroelingLocalDataUpdateCoordinator(hass=hass, entry=entry, profile=profile)

    try:
        await coordinator.async_setup()
    except Exception as err:  # pragma: no cover - network path
        await coordinator.async_shutdown()
        raise ConfigEntryNotReady(f"Unable to connect to {entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}: {err}") from err

    entry.runtime_data = coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FroelingConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.async_shutdown()

    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate older config entries to latest schema version."""
    if entry.version > CONFIG_SCHEMA_VERSION:
        _LOGGER.error(
            "Cannot downgrade config entry %s from %s to %s",
            entry.entry_id,
            entry.version,
            CONFIG_SCHEMA_VERSION,
        )
        return False

    if entry.version == CONFIG_SCHEMA_VERSION:
        return True

    _LOGGER.info("Migrating %s from version %s", entry.entry_id, entry.version)

    new_data = {
        CONF_NAME: entry.data.get(CONF_NAME, DEFAULT_NAME),
        CONF_HOST: entry.data[CONF_HOST],
        CONF_PORT: entry.data.get(CONF_PORT, DEFAULT_PORT),
        CONF_SLAVE: entry.data.get(CONF_SLAVE, DEFAULT_SLAVE),
        CONF_TIMEOUT: entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        CONF_SCAN_INTERVAL: entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        CONF_PROFILE: entry.data.get(CONF_PROFILE, DEFAULT_PROFILE),
        CONF_HEATING_CIRCUITS: entry.data.get(
            CONF_HEATING_CIRCUITS,
            DEFAULT_HEATING_CIRCUITS,
        ),
        CONF_HAS_DHW: entry.data.get(CONF_HAS_DHW, DEFAULT_HAS_DHW),
        CONF_HAS_BUFFER: entry.data.get(CONF_HAS_BUFFER, DEFAULT_HAS_BUFFER),
        CONF_HAS_DHW_HEAT_PUMP: entry.data.get(
            CONF_HAS_DHW_HEAT_PUMP,
            DEFAULT_HAS_DHW_HEAT_PUMP,
        ),
        CONF_SCHEMA_VERSION: CONFIG_SCHEMA_VERSION,
    }

    hass.config_entries.async_update_entry(entry, data=new_data, version=CONFIG_SCHEMA_VERSION)

    _LOGGER.info("Migration for %s completed", entry.entry_id)
    return True
