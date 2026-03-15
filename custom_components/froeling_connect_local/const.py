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

DEFAULT_NAME = "Froeling"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 2
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 5
DEFAULT_PROFILE = "lambdatronic_s3200"

MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 300

CONF_SCHEMA_VERSION = "schema_version"
CONFIG_SCHEMA_VERSION = 2

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