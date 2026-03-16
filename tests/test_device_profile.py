"""Tests for device profile loading and overrides."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path("custom_components/froeling_connect_local/device_profile.py")
SPEC = importlib.util.spec_from_file_location("device_profile", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
apply_installation_options = MODULE.apply_installation_options
load_profile = MODULE.load_profile


def test_base_profile_has_entities() -> None:
    profile = load_profile("lambdatronic_s3200")

    assert profile.profile_id == "lambdatronic_s3200"
    assert "system_state" in profile.entities
    assert "boiler_target_temperature" in profile.entities


def test_derived_profile_overrides_and_excludes() -> None:
    profile = load_profile("sp_dual_compact")

    assert profile.profile_id == "sp_dual_compact"
    assert "hk2_operating_mode" not in profile.entities
    assert profile.entities["pellet_level_percent"].scale == 207
    assert "ignition_runtime_hours" in profile.entities


def test_sp_dual_profile_exists() -> None:
    profile = load_profile("sp_dual")

    assert profile.profile_id == "sp_dual"
    assert profile.model == "SP Dual"
    assert "fuel_selection" in profile.entities


def test_installation_options_filter_entities() -> None:
    profile = load_profile("sp_dual")
    adapted = apply_installation_options(
        profile,
        heating_circuits=1,
        has_dhw=False,
        has_buffer=False,
        has_dhw_heat_pump=False,
    )

    assert "hk2_operating_mode" not in adapted.entities
    assert "dhw_modbus_target_temperature" not in adapted.entities
    assert "buffer_top_temperature" not in adapted.entities


def test_dhw_heat_pump_entities_keep_when_dhw_disabled() -> None:
    profile = load_profile("sp_dual")
    adapted = apply_installation_options(
        profile,
        heating_circuits=1,
        has_dhw=False,
        has_buffer=True,
        has_dhw_heat_pump=True,
    )

    assert "dhw_heat_pump_return_temperature" in adapted.entities
    assert "dhw_heat_pump_installed" not in adapted.entities
