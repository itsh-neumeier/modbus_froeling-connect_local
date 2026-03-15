"""Number platform for Froeling Connect local."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FroelingLocalDataUpdateCoordinator
from .device_profile import EntityProfile
from .entity import FroelingEntity

_NUMBER_DEVICE_CLASS_MAP: dict[str, NumberDeviceClass] = {
    "temperature": NumberDeviceClass.TEMPERATURE,
}

_NUMBER_UNIT_MAP = {
    "C": UnitOfTemperature.CELSIUS,
    "°C": UnitOfTemperature.CELSIUS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Froeling numbers from config entry."""
    coordinator: FroelingLocalDataUpdateCoordinator = entry.runtime_data

    entities = [
        FroelingNumberEntity(coordinator, profile)
        for profile in coordinator.profile.entities_for_platform("number")
    ]
    async_add_entities(entities)


class FroelingNumberEntity(FroelingEntity, NumberEntity):
    """Writable number entity backed by a holding register."""

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator, profile: EntityProfile) -> None:
        super().__init__(coordinator, profile)

        self._attr_native_min_value = profile.min_value
        self._attr_native_max_value = profile.max_value
        self._attr_native_step = profile.step if profile.step is not None else 1 / profile.scale
        self._attr_native_unit_of_measurement = _NUMBER_UNIT_MAP.get(
            profile.unit,
            profile.unit,
        )

        if profile.device_class:
            self._attr_device_class = _NUMBER_DEVICE_CLASS_MAP.get(profile.device_class)

    @property
    def native_value(self):
        return self.coordinator_value()

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_entity(self.profile, value)
