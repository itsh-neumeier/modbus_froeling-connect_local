"""Button platform for Froeling Connect local."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FroelingLocalDataUpdateCoordinator
from .entity import FroelingCoordinatorDiagnosticEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Froeling diagnostic button entities."""
    coordinator: FroelingLocalDataUpdateCoordinator = entry.runtime_data
    async_add_entities([FroelingReconnectButton(coordinator)])


class FroelingReconnectButton(FroelingCoordinatorDiagnosticEntity, ButtonEntity):
    """Trigger manual Modbus reconnect and immediate refresh."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "reconnect_gateway")
        self._attr_icon = "mdi:lan-connect"

    async def async_press(self) -> None:
        await self.coordinator.async_reconnect()