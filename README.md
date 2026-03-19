# Froeling Connect local - Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge&logo=home-assistant)](https://hacs.xyz/)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2026.3%2B-18BCF2?style=for-the-badge&logo=home-assistant)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-0B0F19.svg?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/github/v/release/itsh-neumeier/modbus_froeling-connect_local?style=for-the-badge)](https://github.com/itsh-neumeier/modbus_froeling-connect_local/releases)

> German documentation: [README.de.md](README.de.md)

Full Home Assistant integration for local Fröling controllers via Modbus TCP, with multi-device mapping for boiler, heating circuits, DHW tank, buffer tank, pellet extraction, and optional DHW heat pump modules.

* * *

## Supported Systems

| Profile | Controller / System | Status |
|---|---|---|
| `sp_dual` | Fröling SP Dual | Live-tested |
| `sp_dual_compact` | Fröling SP Dual Compact | Profile-based, derived from SP Dual |
| `lambdatronic_s3200` | Generic Lambdatronic S3200 | Base profile |

* * *

## Features

### Devices

| Home Assistant device | Typical Fröling module |
|---|---|
| Gateway | Main controller / Touch controller |
| Boiler | Boiler core values and firing state |
| Heating Circuit 1 / 2 | Flow temperatures, operating mode, curve values |
| DHW Tank 1 | DHW boiler / domestic hot water |
| Buffer Tank 1 | Buffer temperatures, charge state, pump control |
| Pellet Extraction | Pellet storage / extraction / counters |
| DHW Heat Pump | Dedicated DHW heat pump, if configured |

### Entities

| Platform | Examples |
|---|---|
| `sensor` | Boiler state, boiler temperature, flue gas temperature, buffer temperatures, pellet counters, operating hours |
| `binary_sensor` | Gateway connected, gateway alive, heat demand, legionella cycle |
| `number` | Boiler target temperature, heating curve values, buffer and DHW setpoints |
| `select` | Heating circuit mode, fuel selection |
| `switch` | Automatic ignition, extra DHW charge, automatic pellet extraction disable |
| `button` | Reconnect gateway, restart gateway |

### Diagnostics And Auto-Recovery

| Function | Description |
|---|---|
| `gateway_connected` | Current Modbus connection state |
| `gateway_alive` | Indicates whether fresh data has arrived recently |
| `last_success` | Timestamp of the last successful polling cycle |
| `read_error_count` | Cumulative Modbus read errors |
| Auto-reset | If no fresh data arrives for `3 x scan_interval`, the TCP connection is reset automatically before the next poll |
| Manual actions | `Reconnect gateway` and `Restart gateway` buttons are available as diagnostic entities |

### Profiles And Mapping

| Feature | Description |
|---|---|
| YAML profiles | Device definitions live in `custom_components/froeling_connect_local/device_profiles/` |
| Inheritance | Profiles can extend a base profile and override or exclude entities |
| Installation filters | Heating circuit, DHW, buffer, and DHW heat pump entities are filtered based on setup options |
| Fröling-like grouping | Important values are grouped on the matching HA device instead of ending up only on the gateway |

* * *

## Installation

### Option A: HACS (recommended)

1. HACS -> Integrations -> `...` -> Custom repositories
2. URL: `https://github.com/itsh-neumeier/modbus_froeling-connect_local` | Category: Integration
3. Install integration -> Restart Home Assistant
4. Settings -> Devices & Services -> `+ Add Integration` -> `Froeling Connect local`

### Option B: Manual

1. Copy `custom_components/froeling_connect_local/` into your Home Assistant config directory
2. Restart Home Assistant
3. Settings -> Devices & Services -> `+ Add Integration` -> `Froeling Connect local`

* * *

## Configuration

The config flow covers the installation layout and the Modbus connection:

1. Enter host, port, slave ID, polling interval, and timeout
2. Select the device profile
3. Define the installation topology:
   - number of heating circuits
   - DHW boiler present
   - buffer tank present
   - dedicated DHW heat pump present
4. Optionally enter:
   - buffer volume in liters
   - boiler nominal power in kW
5. Finish setup; the integration probes the controller before the entry is created

### Buffer Runtime Estimation

If a buffer tank is enabled, the integration exposes `sensor.buffer_estimated_time_to_full`.

The estimate uses:

- configured `buffer_liters`
- configured `boiler_power_kw`
- current `buffer_charge_percent`
- fixed assumption of `40 K` usable temperature spread

* * *

## Important SP Dual Entities

### Boiler

| Entity | Register |
|---|---:|
| `sensor.boiler_state` | `34002` |
| `sensor.boiler_temperature` | `30001` |
| `sensor.flue_gas_temperature` | `30002` |
| `sensor.oxygen_residual` | `30004` |
| `sensor.return_temperature` | `30010` |
| `sensor.primary_air` | `30012` |
| `sensor.induced_draft_control_output` | `30013` |
| `sensor.secondary_air` | `30014` |
| `sensor.operating_hours` | `30021` |
| `sensor.ember_preservation_hours` | `30025` |
| `sensor.hours_since_last_maintenance` | `30056` |
| `sensor.hours_in_heating` | `30064` |
| `sensor.hours_in_part_load` | `30075` |
| `sensor.hours_in_logwood_operation` | `30077` |
| `sensor.remaining_heating_hours_until_ash_empty` | `30087` |
| `number.boiler_target_temperature` | `40001` |
| `select.fuel_selection` | `40441` |

### Heating Circuit 1

| Entity | Register |
|---|---:|
| `sensor.hk1_flow_temperature_actual` | `31031` |
| `sensor.hk1_flow_temperature_target` | `31032` |
| `select.hk1_operating_mode` | `48047` |
| `number.hk1_curve_temp_plus10` | `41032` |
| `number.hk1_curve_temp_minus10` | `41033` |
| `number.hk1_setback_delta` | `41034` |
| `number.hk1_pump_off_target_temp` | `41040` |
| `number.hk1_overheat_protection_temp` | `41048` |

### DHW Tank 1

| Entity | Register |
|---|---:|
| `sensor.dhw_temperature_top` | `31631` |
| `sensor.dhw_pump_speed` | `31633` |
| `number.dhw_target_temperature` | `41632` |
| `number.dhw_reheat_below` | `41633` |

### Buffer Tank 1

| Entity | Register |
|---|---:|
| `sensor.buffer_top_temperature` | `32001` |
| `sensor.buffer_middle_temperature` | `32002` |
| `sensor.buffer_bottom_temperature` | `32003` |
| `sensor.buffer_pump_speed` | `32004` |
| `sensor.buffer_charge_percent` | `32007` |
| `sensor.buffer_estimated_time_to_full` | derived |
| `sensor.buffer_release_temperature` | `42001` |
| `number.buffer_delta_kessel_to_layer` | `42003` |

### Pellet Extraction

| Entity | Register |
|---|---:|
| `sensor.pellet_level_percent` | `30022` |
| `sensor.pellet_consumption_reset_kg` | `30082` |
| `sensor.pellet_consumption_reset_t` | `30083` |
| `sensor.pellet_consumption_total_t` | `30084` |
| `number.pellet_stock_remaining_t` | `40320` |
| `number.pellet_stock_minimum_t` | `40336` |
| `switch.automatic_pellet_extraction_disabled` | `40265` |

* * *

## Automation Examples

> How to use: Paste the YAML into the Home Assistant automation editor and replace the entity IDs with your own.

### Alert if the controller stops updating

```yaml
alias: "Froeling - Controller stalled"
description: "Notify if the controller has not delivered fresh data"
mode: single
triggers:
  - trigger: state
    entity_id: binary_sensor.sp_dual_gateway_alive
    to: "off"
actions:
  - action: notify.mobile_app_my_phone
    data:
      title: "Froeling offline"
      message: >
        No fresh Fröling data received.
        Last success: {{ states('sensor.sp_dual_last_success') }}
```

### Restart the gateway automatically after it goes stale

```yaml
alias: "Froeling - Auto restart gateway"
description: "Press the restart button when the gateway is no longer alive"
mode: single
triggers:
  - trigger: state
    entity_id: binary_sensor.sp_dual_gateway_alive
    to: "off"
    for: "00:01:00"
actions:
  - action: button.press
    target:
      entity_id: button.sp_dual_restart_gateway
```

### Notify when ash emptying is approaching

```yaml
alias: "Froeling - Ash warning"
description: "Notify when ash emptying warning is near"
mode: single
triggers:
  - trigger: numeric_state
    entity_id: sensor.sp_dual_remaining_heating_hours_until_ash_empty
    below: 24
actions:
  - action: notify.mobile_app_my_phone
    data:
      title: "Fröling ash warning"
      message: >
        Remaining heating hours until ash emptying:
        {{ states('sensor.sp_dual_remaining_heating_hours_until_ash_empty') }} h
```

* * *

## Development

```bash
python -m pip install -r requirements-dev.txt
ruff check .
bandit -c pyproject.toml -r custom_components/froeling_connect_local
pytest -q
pip-audit -r requirements.txt
```

* * *

## License

MIT. See [LICENSE](LICENSE).
