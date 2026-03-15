"""Shared entity helpers for Froeling Connect local."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import FroelingLocalDataUpdateCoordinator
from .device_profile import EntityProfile

_ENTITY_CATEGORY_MAP: dict[str, EntityCategory] = {
    "config": EntityCategory.CONFIG,
    "diagnostic": EntityCategory.DIAGNOSTIC,
}


class FroelingEntity(
    CoordinatorEntity[FroelingLocalDataUpdateCoordinator],
    Entity,
):
    """Generic register-backed entity."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator, profile: EntityProfile) -> None:
        super().__init__(coordinator)
        self.profile = profile

        self._attr_unique_id = f"{coordinator.entry.entry_id}_{profile.key}"
        self._attr_translation_key = profile.key
        self._attr_entity_registry_enabled_default = profile.enabled_by_default
        self._attr_device_info = coordinator.get_device_info(profile.device_key)
        self._attr_icon = profile.icon

        if profile.entity_category:
            self._attr_entity_category = _ENTITY_CATEGORY_MAP.get(profile.entity_category)

    @property
    def available(self) -> bool:
        value = self.coordinator.data.get(self.profile.key)
        return super().available and value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "register": self.profile.register,
            "register_type": self.profile.register_type,
            "profile": self.coordinator.profile.profile_id,
        }

    def coordinator_value(self) -> Any:
        """Return decoded value from coordinator payload."""
        return self.coordinator.data.get(self.profile.key)


class FroelingCoordinatorDiagnosticEntity(
    CoordinatorEntity[FroelingLocalDataUpdateCoordinator],
    Entity,
):
    """Entity exposing gateway diagnostics from coordinator properties."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: FroelingLocalDataUpdateCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = coordinator.get_device_info("gateway")