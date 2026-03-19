"""Constants for the Froeling Connect local integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "froeling_connect_local"
NAME = "Froeling Connect local"

CONF_PROFILE = "profile"
CONF_SLAVE = "slave"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_TIMEOUT = "timeout"
CONF_NAME = "name"
CONF_HEATING_CIRCUITS = "heating_circuits"
CONF_HAS_DHW = "has_dhw"
CONF_HAS_BUFFER = "has_buffer"
CONF_HAS_DHW_HEAT_PUMP = "has_dhw_heat_pump"
CONF_BUFFER_LITERS = "buffer_liters"
CONF_BOILER_POWER_KW = "boiler_power_kw"

DEFAULT_NAME = "Froeling"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 2
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 5
DEFAULT_PROFILE = "lambdatronic_s3200"
DEFAULT_HEATING_CIRCUITS = 2
DEFAULT_HAS_DHW = True
DEFAULT_HAS_BUFFER = True
DEFAULT_HAS_DHW_HEAT_PUMP = False
DEFAULT_BUFFER_LITERS = 3000
DEFAULT_BOILER_POWER_KW = 22.0
DEFAULT_BUFFER_DELTA_K = 40
DEFAULT_GATEWAY_STALE_MULTIPLIER = 3

MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 300

CONF_SCHEMA_VERSION = "schema_version"
CONFIG_SCHEMA_VERSION = 4

ATTRIBUTION = "Data provided by local Froeling Modbus interface"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.BUTTON,
]

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)


def gateway_stale_after(scan_interval: int, timeout: int) -> timedelta:
    """Return the max age after which the gateway is considered stale."""
    return timedelta(
        seconds=max(
            scan_interval * DEFAULT_GATEWAY_STALE_MULTIPLIER,
            timeout * 2,
        ),
    )
