"""Data coordinator and Modbus transport for Froeling Connect local."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from pymodbus.client import ModbusTcpClient

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SLAVE,
    CONF_TIMEOUT,
    DOMAIN,
    gateway_stale_after,
)
from .device_profile import (
    DeviceProfile,
    EntityProfile,
    grouped_read_ranges,
    register_to_address,
)

_LOGGER = logging.getLogger(__name__)


class FroelingLocalDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate batched polling and writes to a Froeling Modbus endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        profile: DeviceProfile,
    ) -> None:
        update_interval = timedelta(seconds=int(entry.data[CONF_SCAN_INTERVAL]))
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=update_interval,
        )
        self.entry = entry
        self.profile = profile
        self._slave = int(entry.data[CONF_SLAVE])
        self._io_lock = asyncio.Lock()
        self._read_ranges = grouped_read_ranges(profile.entities.values())
        self._gateway = _FroelingModbusGateway(
            host=str(entry.data[CONF_HOST]),
            port=int(entry.data[CONF_PORT]),
            timeout=int(entry.data[CONF_TIMEOUT]),
        )

        self.connected = False
        self.last_error: str | None = None
        self.last_success = None
        self.read_error_count = 0
        self.last_roundtrip_ms: float | None = None
        self._device_info_cache: dict[str, DeviceInfo] = {}

    async def async_setup(self) -> None:
        """Perform first refresh during setup."""
        await self.async_config_entry_first_refresh()

    async def async_shutdown(self) -> None:
        """Close active Modbus connections on unload."""
        await self.hass.async_add_executor_job(self._gateway.close)

    async def async_reconnect(self) -> None:
        """Force a reconnect for diagnostics/recovery."""
        async with self._io_lock:
            await self.hass.async_add_executor_job(self._gateway.reset_connection)
        await self.async_request_refresh()

    async def async_write_entity(self, entity: EntityProfile, value: bool | float | int | str) -> None:
        """Write one register-backed entity value."""
        if not entity.writeable:
            raise ValueError(f"Entity {entity.key} is read-only")
        if entity.register_type != "holding":
            raise ValueError(f"Entity {entity.key} is writeable but not a holding register")

        raw_value = entity.encode_value(value)
        address = register_to_address(entity.register_type, entity.register)

        async with self._io_lock:
            await self.hass.async_add_executor_job(
                self._gateway.write_register,
                address,
                raw_value,
                self._slave,
            )

        await self.async_request_refresh()

    def get_device_info(self, device_key: str) -> DeviceInfo:
        """Create (and cache) Home Assistant device metadata."""
        if device_key in self._device_info_cache:
            return self._device_info_cache[device_key]

        definition = self.profile.devices.get(device_key)
        if definition is None:
            definition = self.profile.devices["gateway"]
            device_key = "gateway"

        base_ident = (DOMAIN, self.entry.entry_id, device_key)
        gateway_ident = (DOMAIN, self.entry.entry_id, "gateway")

        if device_key == "gateway":
            info = DeviceInfo(
                identifiers={base_ident},
                name=definition.name,
                manufacturer=definition.manufacturer,
                model=definition.model,
                configuration_url=f"http://{self.entry.data[CONF_HOST]}",
            )
        else:
            info = DeviceInfo(
                identifiers={base_ident},
                name=definition.name,
                manufacturer=definition.manufacturer,
                model=definition.model,
                via_device=gateway_ident,
            )

        self._device_info_cache[device_key] = info
        return info

    async def _async_update_data(self) -> dict[str, Any]:
        """Read all profile registers in grouped Modbus blocks."""
        started = time.perf_counter()
        register_values: dict[int, int] = {}
        errors: list[str] = []
        should_reset_connection = self._should_auto_reset_connection()

        async with self._io_lock:
            if should_reset_connection:
                _LOGGER.warning(
                    "No successful Modbus update for %.1f seconds. Resetting connection before next poll.",
                    self._last_success_age_seconds(),
                )
                await self.hass.async_add_executor_job(self._gateway.reset_connection)

            for register_type, start_register, count in self._read_ranges:
                address = register_to_address(register_type, start_register)
                try:
                    values = await self.hass.async_add_executor_job(
                        self._gateway.read_registers,
                        register_type,
                        address,
                        count,
                        self._slave,
                    )
                except Exception as err:  # pragma: no cover - network path
                    msg = (
                        f"{register_type} read failed for {start_register}"
                        f" ({count} regs): {err!r}"
                    )
                    errors.append(msg)
                    continue

                for index, raw_value in enumerate(values):
                    register_values[start_register + index] = raw_value

        self.last_roundtrip_ms = round((time.perf_counter() - started) * 1000, 1)

        if not register_values:
            self.connected = False
            self.read_error_count += 1
            self.last_error = errors[0] if errors else "No Modbus data returned"
            raise UpdateFailed(self.last_error)

        if errors:
            self.read_error_count += len(errors)
            self.last_error = errors[-1]
            _LOGGER.warning("Partial Modbus read errors: %s", " | ".join(errors))
        else:
            self.last_error = None

        decoded: dict[str, Any] = {}
        for entity in self.profile.entities.values():
            raw_value = register_values.get(entity.register)
            decoded[entity.key] = entity.decode_value(raw_value)

        self.connected = True
        self.last_success = dt_util.utcnow()
        return decoded

    def _should_auto_reset_connection(self) -> bool:
        """Return True when the gateway should be reset before polling."""
        last_success = self.last_success
        if last_success is None:
            return False
        return (dt_util.utcnow() - last_success) > self._stale_after

    def _last_success_age_seconds(self) -> float:
        """Return the age of the latest successful update in seconds."""
        last_success = self.last_success
        if last_success is None:
            return 0.0
        return round((dt_util.utcnow() - last_success).total_seconds(), 1)

    @property
    def _stale_after(self) -> timedelta:
        """Return the max age after which the connection should be reset."""
        scan_interval = int(self.entry.data[CONF_SCAN_INTERVAL])
        timeout = int(self.entry.data[CONF_TIMEOUT])
        return gateway_stale_after(scan_interval, timeout)


class _FroelingModbusGateway:
    """Synchronous pymodbus client wrapper with compatibility fallbacks."""

    def __init__(self, host: str, port: int, timeout: int) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._client = ModbusTcpClient(host=host, port=port, timeout=timeout)

    def reset_connection(self) -> None:
        """Close and re-open the TCP client."""
        self.close()
        self._client = ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout)

    def close(self) -> None:
        """Close the underlying TCP connection."""
        try:
            self._client.close()
        except Exception:  # pragma: no cover - defensive close
            return

    def read_registers(
        self,
        register_type: str,
        address: int,
        count: int,
        slave: int,
    ) -> list[int]:
        """Read an input or holding register block."""
        self._ensure_connected()
        if register_type == "input":
            method = self._client.read_input_registers
        elif register_type == "holding":
            method = self._client.read_holding_registers
        else:
            raise ValueError(f"Unsupported register type: {register_type}")

        response = self._call_read(method, address, count, slave)
        if response is None or response.isError():
            raise RuntimeError(f"Modbus read error at address {address}")
        return [int(value) for value in response.registers]

    def write_register(self, address: int, value: int, slave: int) -> None:
        """Write one holding register."""
        self._ensure_connected()

        response = self._call_write(self._client.write_register, address, value, slave)
        if response is None or response.isError():
            raise RuntimeError(f"Modbus write error at address {address}")

    def _ensure_connected(self) -> None:
        if self._client.connected:
            return
        if not self._client.connect():
            raise RuntimeError(f"Unable to connect to Modbus endpoint {self.host}:{self.port}")

    @staticmethod
    def _call_read(method: Any, address: int, count: int, slave: int) -> Any:
        for keyword in ("slave", "unit", "device_id"):
            try:
                return method(address=address, count=count, **{keyword: slave})
            except TypeError:
                continue
        return method(address=address, count=count)

    @staticmethod
    def _call_write(method: Any, address: int, value: int, slave: int) -> Any:
        for keyword in ("slave", "unit", "device_id"):
            try:
                return method(address=address, value=value, **{keyword: slave})
            except TypeError:
                continue
        return method(address=address, value=value)


async def async_probe_connection(
    hass: HomeAssistant,
    host: str,
    port: int,
    slave: int,
    connect_timeout: int,
    register_type: str,
    probe_register: int,
) -> None:
    """Probe one register to validate settings in config/options flow."""
    gateway = _FroelingModbusGateway(
        host=host,
        port=port,
        timeout=connect_timeout,
    )

    def _probe() -> None:
        address = register_to_address(register_type, probe_register)
        gateway.read_registers(register_type, address, 1, slave)
        gateway.close()

    await hass.async_add_executor_job(_probe)
