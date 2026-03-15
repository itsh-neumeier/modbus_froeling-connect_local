"""Select platform for Froeling Connect local."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FroelingLocalDataUpdateCoordinator
from .device_profile import EntityProfile
from .entity import FroelingEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Froeling selects from config entry."""
    coordinator: FroelingLocalDataUpdateCoordinator = entry.runtime_data

    entities = [
        FroelingSelectEntity(coordinator, profile)
        for profile in coordinator.profile.entities_for_platform("select")
    ]
    async_add_entities(entities)


class FroelingSelectEntity(FroelingEntity, SelectEntity):
    """Writable enum select entity backed by holding register."""

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator, profile: EntityProfile) -> None:
        super().__init__(coordinator, profile)
        self._attr_options = profile.option_tokens

    @property
    def current_option(self) -> str | None:
        value = self.coordinator_value()
        if value is None:
            return None
        return str(value)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_write_entity(self.profile, option)