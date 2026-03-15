# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/itsh-neumeier/modbus_froeling-connect_local/releases/tag/v0.1.0
