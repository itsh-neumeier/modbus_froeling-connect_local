"""Sensor platform for Froeling Connect local."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FroelingLocalDataUpdateCoordinator
from .device_profile import EntityProfile
from .entity import FroelingCoordinatorDiagnosticEntity, FroelingEntity

_DEVICE_CLASS_MAP: dict[str, SensorDeviceClass] = {
    "temperature": SensorDeviceClass.TEMPERATURE,
    "energy": SensorDeviceClass.ENERGY,
    "power": SensorDeviceClass.POWER,
    "duration": SensorDeviceClass.DURATION,
}

_STATE_CLASS_MAP: dict[str, SensorStateClass] = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total": SensorStateClass.TOTAL,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}

_UNIT_MAP = {
    "C": UnitOfTemperature.CELSIUS,
    "°C": UnitOfTemperature.CELSIUS,
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "W": UnitOfPower.WATT,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Froeling sensors from config entry."""
    coordinator: FroelingLocalDataUpdateCoordinator = entry.runtime_data

    entities: list[SensorEntity] = []
    for profile in coordinator.profile.entities_for_platform("sensor"):
        if profile.value_type == "enum":
            entities.append(FroelingEnumSensor(coordinator, profile))
        else:
            entities.append(FroelingNumericSensor(coordinator, profile))

    entities.extend(
        [
            FroelingRoundtripMsSensor(coordinator),
            FroelingReadErrorCountSensor(coordinator),
            FroelingLastErrorSensor(coordinator),
            FroelingLastSuccessSensor(coordinator),
        ]
    )

    async_add_entities(entities)


class FroelingNumericSensor(FroelingEntity, SensorEntity):
    """Numeric sensor backed by one register."""

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator, profile: EntityProfile) -> None:
        super().__init__(coordinator, profile)

        if profile.device_class:
            self._attr_device_class = _DEVICE_CLASS_MAP.get(profile.device_class)

        if profile.state_class:
            self._attr_state_class = _STATE_CLASS_MAP.get(profile.state_class)

        if profile.unit:
            self._attr_native_unit_of_measurement = _UNIT_MAP.get(profile.unit, profile.unit)

        if profile.value_type == "float":
            self._attr_suggested_display_precision = profile.precision

    @property
    def native_value(self):
        return self.coordinator_value()


class FroelingEnumSensor(FroelingEntity, SensorEntity):
    """Enum text sensor with translated state tokens."""

    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator, profile: EntityProfile) -> None:
        super().__init__(coordinator, profile)
        self._attr_options = profile.option_tokens

    @property
    def native_value(self):
        return self.coordinator_value()


class FroelingRoundtripMsSensor(FroelingCoordinatorDiagnosticEntity, SensorEntity):
    """Expose latest Modbus polling duration."""

    _attr_native_unit_of_measurement = "ms"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "roundtrip_ms")

    @property
    def native_value(self):
        return self.coordinator.last_roundtrip_ms


class FroelingReadErrorCountSensor(FroelingCoordinatorDiagnosticEntity, SensorEntity):
    """Expose cumulative Modbus read errors."""

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "read_error_count")

    @property
    def native_value(self):
        return self.coordinator.read_error_count


class FroelingLastErrorSensor(FroelingCoordinatorDiagnosticEntity, SensorEntity):
    """Expose most recent read error."""

    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "last_error")

    @property
    def native_value(self):
        return self.coordinator.last_error


class FroelingLastSuccessSensor(FroelingCoordinatorDiagnosticEntity, SensorEntity):
    """Expose timestamp of last successful polling cycle."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "last_success")

    @property
    def native_value(self):
        return self.coordinator.last_success
