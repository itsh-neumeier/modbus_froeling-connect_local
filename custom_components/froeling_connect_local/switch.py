"""Switch platform for Froeling Connect local."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FroelingLocalDataUpdateCoordinator
from .entity import FroelingEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Froeling switches from config entry."""
    coordinator: FroelingLocalDataUpdateCoordinator = entry.runtime_data

    entities = [
        FroelingSwitchEntity(coordinator, profile)
        for profile in coordinator.profile.entities_for_platform("switch")
    ]
    async_add_entities(entities)


class FroelingSwitchEntity(FroelingEntity, SwitchEntity):
    """Writable bool switch entity backed by holding register."""

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator_value()
        if value is None:
            return None
        return bool(value)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_entity(self.profile, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_entity(self.profile, False)