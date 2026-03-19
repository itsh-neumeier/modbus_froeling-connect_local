"""Binary sensor platform for Froeling Connect local."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HAS_DHW_HEAT_PUMP,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_HAS_DHW_HEAT_PUMP,
    gateway_stale_after,
)
from .coordinator import FroelingLocalDataUpdateCoordinator
from .device_profile import EntityProfile
from .entity import FroelingCoordinatorDiagnosticEntity, FroelingEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Froeling binary sensors from config entry."""
    coordinator: FroelingLocalDataUpdateCoordinator = entry.runtime_data

    entities: list[BinarySensorEntity] = [
        FroelingBinarySensorEntity(coordinator, profile)
        for profile in coordinator.profile.entities_for_platform("binary_sensor")
    ]
    entities.append(FroelingGatewayConnectedBinarySensor(coordinator))
    entities.append(FroelingGatewayAliveBinarySensor(coordinator))
    if bool(
        coordinator.entry.data.get(CONF_HAS_DHW_HEAT_PUMP, DEFAULT_HAS_DHW_HEAT_PUMP),
    ):
        entities.append(FroelingDhwHeatPumpInstalledBinarySensor(coordinator))

    async_add_entities(entities)


class FroelingBinarySensorEntity(FroelingEntity, BinarySensorEntity):
    """Register-backed bool entity."""

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator, profile: EntityProfile) -> None:
        super().__init__(coordinator, profile)
        if profile.device_class:
            self._attr_device_class = getattr(
                BinarySensorDeviceClass,
                profile.device_class.upper(),
                None,
            )

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator_value()
        if value is None:
            return None
        return bool(value)


class FroelingGatewayConnectedBinarySensor(FroelingCoordinatorDiagnosticEntity, BinarySensorEntity):
    """Connectivity flag for the Modbus gateway."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "gateway_connected")

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.connected


class FroelingGatewayAliveBinarySensor(FroelingCoordinatorDiagnosticEntity, BinarySensorEntity):
    """Report whether polling data is still fresh enough to consider the gateway alive."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "gateway_alive")
        self._attr_icon = "mdi:heart-pulse"
        self._cancel_timer = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._cancel_timer = async_track_time_interval(
            self.hass,
            self._handle_tick,
            timedelta(minutes=1),
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None
        await super().async_will_remove_from_hass()

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        if not self.coordinator.connected:
            return False

        last_success = self.coordinator.last_success
        if last_success is None:
            return False

        age = dt_util.utcnow() - last_success
        return age <= self._stale_after

    @property
    def extra_state_attributes(self) -> dict[str, float | None]:
        last_success = self.coordinator.last_success
        age_seconds: float | None = None
        if last_success is not None:
            age_seconds = round((dt_util.utcnow() - last_success).total_seconds(), 1)

        return {
            "stale_after_seconds": round(self._stale_after.total_seconds(), 1),
            "last_success_age_seconds": age_seconds,
        }

    @property
    def _stale_after(self) -> timedelta:
        scan_interval = int(self.coordinator.entry.data.get(CONF_SCAN_INTERVAL, 30))
        timeout = int(self.coordinator.entry.data.get(CONF_TIMEOUT, 5))
        return gateway_stale_after(scan_interval, timeout)

    @callback
    def _handle_tick(self, _now) -> None:
        self.async_write_ha_state()


class FroelingDhwHeatPumpInstalledBinarySensor(
    FroelingCoordinatorDiagnosticEntity,
    BinarySensorEntity,
):
    """Expose configured DHW heat pump presence and create dedicated BWP device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "dhw_heat_pump_installed")
        self._attr_device_info = coordinator.get_device_info("dhw_heat_pump")

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return bool(
            self.coordinator.entry.data.get(
                CONF_HAS_DHW_HEAT_PUMP,
                DEFAULT_HAS_DHW_HEAT_PUMP,
            ),
        )
