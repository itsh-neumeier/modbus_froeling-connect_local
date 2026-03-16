# Froeling Connect local

Home Assistant custom integration for **local** Froeling controller access via **Modbus TCP**.

This project is designed for Home Assistant `2026.3+`, HACS installation, and long-term maintainability.

## Features

- Native Home Assistant integration (`config_flow`, `options_flow`)
- Local Modbus TCP polling (no cloud dependency)
- Device profile selection from dropdown during setup
- Profile definitions in YAML (`device_profiles/*.yaml`)
- Model-specific profile inheritance with overrides and excludes
- Batched register reads via `DataUpdateCoordinator`
- Reused TCP connection with timeout/error handling
- Safe defaults:
  - user-safe sensors enabled
  - write/service entities disabled by default
- EN/DE translations including entity states/options
- HACS metadata, branding, CI, security policy, changelog

## Supported Profiles

- `lambdatronic_s3200` - Generic Lambdatronic S3200 profile
- `sp_dual` - SP Dual profile
- `sp_dual_compact` - Derived profile with SP Dual Compact overrides

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant.
2. Add custom repository: `https://github.com/itsh-neumeier/modbus_froeling-connect_local`
3. Category: `Integration`
4. Install **Froeling Connect local**.
5. Restart Home Assistant.

### Manual

1. Copy `custom_components/froeling_connect_local` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. Go to `Settings -> Devices & Services -> Add Integration`.
2. Search for `Froeling Connect local`.
3. Enter:
   - host
   - port (default `502`)
   - slave ID (default `2`)
   - number of heating circuits (1-12)
   - domestic hot water boiler available
   - buffer tank available
   - dedicated DHW heating (DHW heat pump) available
   - buffer volume in liters
   - boiler nominal power in kW (for runtime estimation)
   - device profile
   - polling interval
   - timeout
4. Confirm. A connection probe is performed before entry creation.

### Options flow

Use `Configure` on the integration card to adjust host/port/slave/profile/heating setup/interval/timeout later.

### Device Model In Home Assistant

The integration creates a parent gateway device and child devices (`via_device`) for plant modules:

- boiler
- feed/extraction unit (Austragung)
- pellet unit
- heating circuits
- buffer tank
- optional DHW heat pump

### Buffer Runtime Estimation

If a buffer tank is enabled, the integration exposes an estimated runtime sensor:

- `sensor.buffer_estimated_time_to_full`

The estimate uses:

- configured `buffer_liters`
- configured `boiler_power_kw`
- current `buffer_charge_percent`
- fixed assumption of `40 K` usable temperature spread

## Entity Mapping

### Common status and telemetry sensors

| Entity key | Register | Type | Notes |
|---|---:|---|---|
| `system_state` | 34001 | enum sensor | friendly text states |
| `boiler_state` | 34002 | enum sensor | friendly text states |
| `outside_temperature` | 31001 | sensor | °C |
| `boiler_temperature` | 30001 | sensor | °C |
| `flue_gas_temperature` | 30002 | sensor | °C |
| `oxygen_residual` | 30004 | sensor | % |
| `boiler_pump_speed` | 30068 | sensor | % |
| `hk1_flow_temperature_actual` | 31031 | sensor | °C |
| `hk1_flow_temperature_target` | 31032 | sensor | °C |
| `hk2_flow_temperature_actual` | 31061 | sensor | °C |
| `hk2_flow_temperature_target` | 31062 | sensor | °C |
| `buffer_top_temperature` | 32001 | sensor | °C |
| `buffer_middle_temperature` | 32002 | sensor | °C |
| `buffer_bottom_temperature` | 32003 | sensor | °C |
| `buffer_charge_percent` | 32007 | sensor | % |
| `pellet_level_percent` | 30022 | sensor | % |
| `daily_energy_kwh` | 30085 | sensor | kWh |
| `total_energy_kwh` | 30086 | sensor | kWh |

### Binary sensors

| Entity key | Register | Type |
|---|---:|---|
| `heat_demand_active` | 30057 | binary_sensor |
| `buffer_heat_recovery_active` | 42002 | binary_sensor |
| `legionella_cycle_active` | 41637 | binary_sensor |
| `gateway_connected` | diagnostic binary_sensor |

### Write/config entities (disabled by default)

| Entity key | Register | Platform |
|---|---:|---|
| `automatic_ignition` | 40136 | switch |
| `hk1_enabled` | 48029 | switch |
| `hk2_enabled` | 48030 | switch |
| `boiler_target_temperature` | 40001 | number |
| `hk1_modbus_target_temperature` | 48001 | number |
| `hk2_modbus_target_temperature` | 48002 | number |
| `dhw_modbus_target_temperature` | 48019 | number |
| `dhw_extra_charge` | 41636 | switch |
| `pellet_stock_remaining_t` | 40320 | number |
| `hk1_operating_mode` | 48047 | select |
| `hk2_operating_mode` | 48048 | select |
| `fuel_selection` | 40441 | select |

### SP Dual Compact additions

| Entity key | Register | Type |
|---|---:|---|
| `ignition_runtime_hours` | 30047 | sensor |
| `stoker_runtime_hours` | 30040 | sensor |

## Example Automations

### Alert on boiler fault state

```yaml
automation:
  - alias: Froeling Boiler Fault Alert
    trigger:
      - platform: state
        entity_id: sensor.froeling_boiler_state
        to: "fault"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "Froeling boiler reports a fault state."
```

### Limit operating mode changes to daytime

```yaml
automation:
  - alias: Froeling HK1 Daytime Mode
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.froeling_hk1_operating_mode
        data:
          option: automatic
```

## Diagnostics and Robustness

- Grouped block reads per register type for lower network overhead
- Shared coordinator lock to avoid concurrent Modbus calls
- Connection reuse with reconnect fallback
- Dedicated diagnostic entities:
  - gateway connectivity
  - roundtrip latency
  - read error counter
  - last error text
  - last successful update timestamp

## Security

- Runtime dependencies are pinned by range and audited in CI (`pip-audit`)
- Static analysis in CI: `ruff`, `bandit`
- Security reporting process: see [SECURITY.md](SECURITY.md)

## Development

```bash
python -m pip install -r requirements-dev.txt
ruff check .
bandit -c pyproject.toml -r custom_components/froeling_connect_local
pytest -q
pip-audit -r requirements.txt
```

## Release Process

1. Update code and tests
2. Run checks
3. Bump version in `manifest.json`
4. Update `CHANGELOG.md`
5. Commit + push
6. Create and push tag `vX.Y.Z`
7. Publish GitHub Release

## License

MIT. See [LICENSE](LICENSE).
