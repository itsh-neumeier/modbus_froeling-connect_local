# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/timo-neumeier/froeling-connect_local/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/timo-neumeier/froeling-connect_local/releases/tag/v0.1.0