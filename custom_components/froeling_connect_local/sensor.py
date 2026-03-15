"""Sensor platform for Froeling Connect local."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_BOILER_POWER_KW,
    CONF_BUFFER_LITERS,
    CONF_HAS_BUFFER,
    DEFAULT_BOILER_POWER_KW,
    DEFAULT_BUFFER_DELTA_K,
    DEFAULT_BUFFER_LITERS,
    DEFAULT_HAS_BUFFER,
)
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
    if bool(coordinator.entry.data.get(CONF_HAS_BUFFER, DEFAULT_HAS_BUFFER)):
        entities.append(FroelingBufferEstimatedFullTimeSensor(coordinator))

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


class FroelingBufferEstimatedFullTimeSensor(FroelingCoordinatorDiagnosticEntity, SensorEntity):
    """Estimate runtime until buffer reaches 100% based on configured plant power."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "h"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "buffer_estimated_time_to_full")
        self._attr_device_info = coordinator.get_device_info("buffer_1")

    @property
    def native_value(self) -> float | None:
        charge = self.coordinator.data.get("buffer_charge_percent")
        if charge is None:
            return None

        boiler_power_kw = float(
            self.coordinator.entry.data.get(
                CONF_BOILER_POWER_KW,
                DEFAULT_BOILER_POWER_KW,
            ),
        )
        if boiler_power_kw <= 0:
            return None

        buffer_liters = float(
            self.coordinator.entry.data.get(
                CONF_BUFFER_LITERS,
                DEFAULT_BUFFER_LITERS,
            ),
        )
        if buffer_liters <= 0:
            return None

        # 1 liter water ~= 1.163 Wh per Kelvin
        full_energy_kwh = (
            buffer_liters
            * DEFAULT_BUFFER_DELTA_K
            * 1.163
            / 1000
        )
        missing_percent = max(0.0, 100.0 - float(charge))
        missing_energy_kwh = full_energy_kwh * (missing_percent / 100.0)
        if missing_energy_kwh <= 0:
            return 0.0
        return round(missing_energy_kwh / boiler_power_kw, 1)

    @property
    def extra_state_attributes(self) -> dict[str, float]:
        return {
            "assumed_delta_t_k": float(DEFAULT_BUFFER_DELTA_K),
            "configured_buffer_liters": float(
                self.coordinator.entry.data.get(
                    CONF_BUFFER_LITERS,
                    DEFAULT_BUFFER_LITERS,
                ),
            ),
            "configured_boiler_power_kw": float(
                self.coordinator.entry.data.get(
                    CONF_BOILER_POWER_KW,
                    DEFAULT_BOILER_POWER_KW,
                ),
            ),
        }
