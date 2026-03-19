# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-03-19

### Added
- Added new SP Dual device-mapped entities for key Fröling Connect values:
  - operating hours
  - burner starts
  - ember preservation hours
  - return temperature
  - primary air
  - induced draft control output
  - secondary air
  - maintenance hours
  - heating / part-load / logwood hours
  - remaining heating hours until ash emptying
- Added diagnostic `gateway_alive` binary sensor.
- Added dedicated `restart_gateway` button entity.
- Added automatic Modbus connection reset when no fresh data arrives for `3 x scan_interval`.

### Changed
- Moved pellet stock and pellet consumption entities to the `Austragung` device for a more Fröling-like device layout.
- Enabled important SP Dual setpoints by default to better match the Fröling Connect UI:
  - boiler target temperature
  - HK1 curve values
  - HK1 setback / pump / frost / overheat settings
  - DHW target and recharge threshold
  - buffer release temperature and buffer delta
- Reworked `README.md` and `README.de.md` into the same structure/style used in the `dahua_vto` repository.
- Refined DE/EN translations for SP Dual labels and diagnostics.

## [0.4.3] - 2026-03-16

### Changed
- Renamed buffer temperature entities to enforce a logical top-to-bottom sort order in Home Assistant device views:
  - `Puffer Temperatur 1 oben`
  - `Puffer Temperatur 2 mitte`
  - `Puffer Temperatur 3 unten`

## [0.4.2] - 2026-03-16

### Fixed
- Added automatic entity-registry recovery for existing installations:
  - `select.hk1_operating_mode`
  - `select.hk2_operating_mode`
  - `switch.dhw_extra_charge`
- Previously integration-disabled entries for these translation keys are now re-enabled during setup.

## [0.4.1] - 2026-03-16

### Changed
- Enabled `select.hk1_operating_mode` and `select.hk2_operating_mode` by default so `Extra heat` and `Party` mode are immediately available in the UI.
- Moved `switch.dhw_extra_charge` to the dedicated BWP device for clearer device grouping.
- Updated switch naming to `BWP extra laden` (DE) / `DHW heat pump extra charge` (EN).

### Fixed
- Fixed profile filtering so `dhw_extra_charge` remains available when DHW boiler is disabled but BWP is present (`has_dhw=false`, `has_dhw_heat_pump=true`).

## [0.4.0] - 2026-03-16

### Added
- Added writable `switch.dhw_extra_charge` (extra DHW charge) based on register `41636`.

### Changed
- Renamed German buffer runtime sensor label to: `Geschätzte Zeit bis Puffer voll bei Betrieb`.
- Improved DE translations for multiple entity names and option/state labels.
- Updated DHW heat pump installed sensor wording to presence semantics (`Vorhanden` / `Nicht vorhanden`).

### Fixed
- Fixed installation filtering so dedicated DHW heat pump entities are kept when DHW boiler is disabled (`has_dhw=false`, `has_dhw_heat_pump=true`).
- This restores visibility of the dedicated BWP device and its telemetry entities in the device tree.

## [0.3.2] - 2026-03-16

### Changed
- Reordered Config/Options Flow fields to prioritize: slave ID, device profile, boiler power, buffer enable + liters, heating circuit count, and dedicated DHW heating.
- Changed heating circuit input to a plain numeric field (`1..12`) instead of a selector control.
- Updated DHW labels for clearer distinction between DHW boiler and dedicated DHW heat pump.
- Removed leading zeroes from numbered device friendly names (for example `Boiler 1`, `Puffer 1`, `Heizkreis 1`).
- Updated translated buffer source state labels to `Puffer 1..4`.

## [0.3.1] - 2026-03-16

### Fixed
- Hardened Config Flow schema creation with compatibility fallbacks for selector APIs.
- Added safe fallback behavior for profile dropdown rendering to prevent UI load failures.
- Prevented 500 errors during integration setup when selector capabilities differ between HA runtime versions.

## [0.3.0] - 2026-03-15

### Added
- Live-validated SP Dual register expansion (based on Modbus reads from device):
  - Kessel-/Austragungs-/Pellet-/Boiler-1-/BWP-/Puffer-Datenpunkte
  - additional config/setpoint entities for HK1, DHW, buffer, pellet feed
- New config/options parameters for runtime estimation:
  - `buffer_liters`
  - `boiler_power_kw`
- New diagnostic sensor `buffer_estimated_time_to_full` (estimated runtime to 100% buffer level)

### Changed
- Device hierarchy aligned to multi-device layout (gateway + dedicated child devices for Kessel, Austragung, Pellet, Heizkreis, Boiler 1, Puffer 1, optional BWP)
- Switched brand assets to official Froeling logos from froeling.com
- Manufacturer metadata normalized to `Fröling GmbH`
- EN/DE translation coverage extended for all added entities and options

## [0.2.0] - 2026-03-15

### Added
- New `sp_dual` profile in addition to `sp_dual_compact`
- Extended config/options flow fields for installation topology:
  - number of heating circuits
  - DHW availability
  - buffer tank availability
  - DHW heat pump availability
- Runtime entity filtering based on installation options
- Separate child devices (via gateway) for boiler, feed unit (Austragung), pellet unit, heating circuits, and optional DHW heat pump

### Changed
- Renamed GitHub repository to `modbus_froeling-connect_local`
- Updated documentation and integration metadata links to the new repository URL

## [0.1.1] - 2026-03-15

### Fixed
- Hassfest compliance for `CONFIG_SCHEMA` declaration in `__init__.py`
- Manifest key ordering and metadata (`integration_type`) for Home Assistant validation

## [0.1.0] - 2026-03-15

### Added
- Initial production-ready HACS custom integration for local Froeling Modbus TCP access
- Full config flow and options flow with profile dropdown
- YAML profile system with inheritance, overrides and excludes
- Platforms: sensor, binary_sensor, number, select, switch, button
- Batched Modbus polling coordinator with connection reuse and diagnostics
- EN/DE translations including enum states/options
- Branding assets in integration and root `brand/`
- CI pipeline with hassfest, ruff, bandit, pip-audit, pytest
- MIT license and security policy

[Unreleased]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.4.3...v0.5.0
[0.4.3]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/releases/tag/v0.1.0
