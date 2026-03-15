"""Device profile loading and register decoding utilities."""

from __future__ import annotations

import copy
from collections.abc import Iterable
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROFILE_DIR = Path(__file__).parent / "device_profiles"


class ProfileError(RuntimeError):
    """Raised when a profile cannot be loaded."""


@dataclass(frozen=True, slots=True)
class DeviceDefinition:
    """Metadata for one logical Home Assistant device."""

    key: str
    name: str
    model: str
    manufacturer: str = "Fröling GmbH"


@dataclass(frozen=True, slots=True)
class EntityProfile:
    """Register-backed entity definition from a YAML profile."""

    key: str
    platform: str
    register: int
    register_type: str
    value_type: str
    scale: float = 1.0
    precision: int = 0
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    device_key: str = "gateway"
    writeable: bool = False
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    options: dict[int, str] | None = None
    signed: bool = True
    entity_category: str | None = None
    enabled_by_default: bool = True
    icon: str | None = None
    true_value: int = 1
    false_value: int = 0
    bitmask: int | None = None

    @property
    def option_tokens(self) -> list[str]:
        """Return sorted enum token list for sensor/select options."""
        if not self.options:
            return []
        return [self.options[key] for key in sorted(self.options)]

    @property
    def reverse_options(self) -> dict[str, int]:
        """Return reverse enum lookup for write operations."""
        if not self.options:
            return {}
        return {token: raw for raw, token in self.options.items()}

    def decode_value(self, raw_value: int | None) -> bool | float | int | str | None:
        """Decode a raw Modbus register value into an HA-native value."""
        if raw_value is None:
            return None

        if self.bitmask is not None:
            masked = raw_value & self.bitmask
            return bool(masked)

        if self.value_type == "bool":
            return raw_value == self.true_value

        if self.value_type == "enum":
            if self.options and raw_value in self.options:
                return self.options[raw_value]
            return f"unknown_{raw_value}"

        value = raw_value
        if self.signed and value > 32767:
            value -= 65536

        scaled = value / self.scale
        if self.value_type == "int":
            return int(round(scaled))
        return round(scaled, self.precision)

    def encode_value(self, value: bool | float | int | str) -> int:
        """Encode a Home Assistant value to a raw Modbus register value."""
        if not self.writeable:
            raise ValueError(f"Entity {self.key} is read-only")

        if self.value_type == "bool":
            raw = self.true_value if bool(value) else self.false_value
            return int(raw)

        if self.value_type == "enum":
            if isinstance(value, str):
                try:
                    return self.reverse_options[value]
                except KeyError as err:
                    raise ValueError(f"Unsupported option '{value}' for {self.key}") from err
            if isinstance(value, int):
                return value
            raise ValueError(f"Unsupported enum value type for {self.key}: {type(value)!r}")

        numeric = float(value)
        if self.min_value is not None and numeric < self.min_value:
            raise ValueError(f"Value {numeric} below minimum {self.min_value} for {self.key}")
        if self.max_value is not None and numeric > self.max_value:
            raise ValueError(f"Value {numeric} above maximum {self.max_value} for {self.key}")

        raw = int(round(numeric * self.scale))
        if self.signed and raw < 0:
            raw = 65536 + raw
        return raw


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """Fully resolved profile after applying base/override rules."""

    profile_id: str
    name: str
    description: str
    manufacturer: str
    model: str
    devices: dict[str, DeviceDefinition]
    entities: dict[str, EntityProfile]

    def entities_for_platform(self, platform: str) -> list[EntityProfile]:
        """Return profile entities for a Home Assistant platform."""
        return [entity for entity in self.entities.values() if entity.platform == platform]


@lru_cache(maxsize=16)
def list_profiles() -> dict[str, str]:
    """Return profile_id -> display name mapping from YAML files."""
    profiles: dict[str, str] = {}
    for path in sorted(PROFILE_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        profile_id = str(raw.get("id") or path.stem)
        profile_name = str(raw.get("name") or profile_id)
        profiles[profile_id] = profile_name
    if not profiles:
        raise ProfileError("No profile definitions found")
    return profiles


@lru_cache(maxsize=16)
def load_profile(profile_id: str) -> DeviceProfile:
    """Load and resolve a profile by id."""
    raw = _resolve_profile(profile_id, stack=[])

    devices_data = raw.get("devices", {})
    devices: dict[str, DeviceDefinition] = {}
    for device_key, device in devices_data.items():
        devices[device_key] = DeviceDefinition(
            key=device_key,
            name=str(device["name"]),
            model=str(device.get("model") or raw.get("model") or raw.get("name") or profile_id),
            manufacturer=str(
                device.get("manufacturer")
                or raw.get("manufacturer")
                or "Fröling GmbH"
            ),
        )

    entities: dict[str, EntityProfile] = {}
    for entity_data in raw.get("entities", []):
        key = str(entity_data["key"])
        options_raw = entity_data.get("options")
        options: dict[int, str] | None = None
        if options_raw:
            options = {int(raw_key): str(token) for raw_key, token in options_raw.items()}

        entities[key] = EntityProfile(
            key=key,
            platform=str(entity_data["platform"]),
            register=int(entity_data["register"]),
            register_type=str(entity_data.get("register_type", "input")),
            value_type=str(entity_data.get("value_type", "float")),
            scale=float(entity_data.get("scale", 1)),
            precision=int(entity_data.get("precision", 0)),
            unit=entity_data.get("unit"),
            device_class=entity_data.get("device_class"),
            state_class=entity_data.get("state_class"),
            device_key=str(entity_data.get("device_key", "gateway")),
            writeable=bool(entity_data.get("writeable", False)),
            min_value=(
                float(entity_data["min_value"])
                if entity_data.get("min_value") is not None
                else None
            ),
            max_value=(
                float(entity_data["max_value"])
                if entity_data.get("max_value") is not None
                else None
            ),
            step=(
                float(entity_data["step"])
                if entity_data.get("step") is not None
                else None
            ),
            options=options,
            signed=bool(entity_data.get("signed", True)),
            entity_category=entity_data.get("entity_category"),
            enabled_by_default=bool(entity_data.get("enabled_by_default", True)),
            icon=entity_data.get("icon"),
            true_value=int(entity_data.get("true_value", 1)),
            false_value=int(entity_data.get("false_value", 0)),
            bitmask=(
                int(entity_data["bitmask"])
                if entity_data.get("bitmask") is not None
                else None
            ),
        )

    return DeviceProfile(
        profile_id=profile_id,
        name=str(raw.get("name") or profile_id),
        description=str(raw.get("description") or ""),
        manufacturer=str(raw.get("manufacturer") or "Fröling GmbH"),
        model=str(raw.get("model") or raw.get("name") or profile_id),
        devices=devices,
        entities=entities,
    )


def apply_installation_options(
    profile: DeviceProfile,
    *,
    heating_circuits: int,
    has_dhw: bool,
    has_buffer: bool,
    has_dhw_heat_pump: bool,
) -> DeviceProfile:
    """Return a profile filtered by installation-specific options."""
    filtered_entities: dict[str, EntityProfile] = {}
    for key, entity in profile.entities.items():
        if heating_circuits < 2 and key.startswith("hk2_"):
            continue
        if not has_dhw and (key.startswith("dhw_") or key.startswith("legionella_")):
            continue
        if not has_buffer and key.startswith("buffer_"):
            continue
        if not has_dhw_heat_pump and key.startswith("dhw_heat_pump_"):
            continue
        filtered_entities[key] = entity

    used_device_keys = {
        "gateway",
        *{entity.device_key for entity in filtered_entities.values()},
    }
    filtered_devices = {
        key: value
        for key, value in profile.devices.items()
        if key in used_device_keys
    }

    return replace(profile, devices=filtered_devices, entities=filtered_entities)


def register_to_address(register_type: str, register: int) -> int:
    """Convert Modbus register number to 0-based address for pymodbus."""
    if register_type == "input":
        return register - 30001
    if register_type == "holding":
        return register - 40001
    raise ValueError(f"Unsupported register_type '{register_type}'")


def grouped_read_ranges(entities: Iterable[EntityProfile], max_block_size: int = 32) -> list[tuple[str, int, int]]:
    """Build grouped read ranges by register type for efficient polling."""
    per_type: dict[str, list[int]] = {"input": [], "holding": []}
    for entity in entities:
        per_type.setdefault(entity.register_type, []).append(entity.register)

    ranges: list[tuple[str, int, int]] = []
    for register_type, registers in per_type.items():
        if not registers:
            continue

        ordered = sorted(set(registers))
        start = ordered[0]
        end = ordered[0]

        for reg in ordered[1:]:
            if reg == end + 1 and (reg - start + 1) <= max_block_size:
                end = reg
                continue
            ranges.append((register_type, start, end - start + 1))
            start = reg
            end = reg

        ranges.append((register_type, start, end - start + 1))

    return ranges


def _resolve_profile(profile_id: str, stack: list[str]) -> dict[str, Any]:
    if profile_id in stack:
        chain = " -> ".join([*stack, profile_id])
        raise ProfileError(f"Circular profile inheritance detected: {chain}")

    path = PROFILE_DIR / f"{profile_id}.yaml"
    if not path.exists():
        raise ProfileError(f"Profile '{profile_id}' not found at {path}")

    current = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    current.setdefault("id", profile_id)

    base_profile = current.get("base_profile")
    if not base_profile:
        return current

    base = _resolve_profile(str(base_profile), [*stack, profile_id])
    merged = _merge_profiles(base, current)
    merged["id"] = profile_id
    return merged


def _merge_profiles(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)

    for key in ("name", "description", "manufacturer", "model", "devices"):
        if key in override:
            if isinstance(override[key], dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **override[key]}
            else:
                merged[key] = copy.deepcopy(override[key])

    entity_map: dict[str, dict[str, Any]] = {
        str(entity["key"]): copy.deepcopy(entity)
        for entity in merged.get("entities", [])
    }

    for excluded_key in override.get("exclude_entities", []) or []:
        entity_map.pop(str(excluded_key), None)

    for override_entity in override.get("override_entities", []) or []:
        key = str(override_entity["key"])
        base_entity = entity_map.get(key, {})
        entity_map[key] = {**base_entity, **copy.deepcopy(override_entity)}

    for new_entity in override.get("entities", []) or []:
        key = str(new_entity["key"])
        entity_map[key] = copy.deepcopy(new_entity)

    merged["entities"] = list(entity_map.values())
    return merged
