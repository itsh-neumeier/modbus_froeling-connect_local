"""Binary sensor platform for Froeling Connect local."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_HAS_DHW_HEAT_PUMP, DEFAULT_HAS_DHW_HEAT_PUMP
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


class FroelingDhwHeatPumpInstalledBinarySensor(
    FroelingCoordinatorDiagnosticEntity,
    BinarySensorEntity,
):
    """Expose configured DHW heat pump presence and create dedicated BWP device."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.RUNNING

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
