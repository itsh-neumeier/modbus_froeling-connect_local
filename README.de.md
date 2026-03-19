# Fröling Connect local - Home-Assistant-Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge&logo=home-assistant)](https://hacs.xyz/)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2026.3%2B-18BCF2?style=for-the-badge&logo=home-assistant)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-0B0F19.svg?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/github/v/release/itsh-neumeier/modbus_froeling-connect_local?style=for-the-badge)](https://github.com/itsh-neumeier/modbus_froeling-connect_local/releases)

> English documentation: [README.md](README.md)

Vollständige Home-Assistant-Integration für lokale Fröling-Regler über Modbus TCP, mit sauberer Gerätezuordnung für Kessel, Heizkreise, Boiler, Puffer, Austragung und optionale Brauchwasser-Wärmepumpe.

* * *

## Unterstützte Systeme

| Profil | Regler / System | Status |
|---|---|---|
| `sp_dual` | Fröling SP Dual | Live getestet |
| `sp_dual_compact` | Fröling SP Dual Compact | Profilbasiert, von SP Dual abgeleitet |
| `lambdatronic_s3200` | Generischer Lambdatronic S3200 | Basisprofil |

* * *

## Funktionen

### Geräte

| Home-Assistant-Gerät | Typisches Fröling-Modul |
|---|---|
| Gateway | Hauptregler / Touch-Regler |
| Kessel | Kesselwerte und Feuerungszustand |
| Heizkreis 1 / 2 | Vorlauftemperaturen, Betriebsarten, Heizkurve |
| Boiler 1 | Brauchwasser-Boiler |
| Puffer 1 | Puffertemperaturen, Ladezustand, Pumpenansteuerung |
| Austragung | Pelletlager / Austragung / Zähler |
| BWP | Dedizierte Brauchwasser-Wärmepumpe, falls vorhanden |

### Entitäten

| Plattform | Beispiele |
|---|---|
| `sensor` | Kesselzustand, Kesseltemperatur, Abgastemperatur, Puffertemperaturen, Pelletzähler, Betriebsstunden |
| `binary_sensor` | Gateway verbunden, Gateway alive, Wärmeanforderung, Legionellenzyklus |
| `number` | Kessel-Solltemperatur, Heizkurvenwerte, Puffer- und Boiler-Sollwerte |
| `select` | Heizkreis-Betriebsart, Brennstoffauswahl |
| `switch` | Automatische Zündung, BWP extra laden, automatische Pelletsaustragung deaktivieren |
| `button` | Gateway neu verbinden, Gateway neu starten |

### Diagnostik Und Auto-Recovery

| Funktion | Beschreibung |
|---|---|
| `gateway_connected` | Aktueller Zustand der Modbus-Verbindung |
| `gateway_alive` | Zeigt an, ob vor kurzem frische Daten eingetroffen sind |
| `last_success` | Zeitstempel der letzten erfolgreichen Aktualisierung |
| `read_error_count` | Kumulierte Modbus-Lesefehler |
| Auto-Reset | Wenn länger als `3 x scan_interval` keine frischen Daten kommen, wird die TCP-Verbindung vor dem nächsten Poll automatisch zurückgesetzt |
| Manuelle Aktionen | `Gateway neu verbinden` und `Gateway neu starten` stehen als Diagnose-Entitäten bereit |

### Profile Und Zuordnung

| Funktion | Beschreibung |
|---|---|
| YAML-Profile | Gerätemodelle liegen in `custom_components/froeling_connect_local/device_profiles/` |
| Vererbung | Profile können ein Basisprofil erweitern und Entitäten überschreiben oder ausschließen |
| Installationsfilter | Heizkreise, Boiler, Puffer und BWP werden abhängig vom Setup ein- oder ausgeblendet |
| Fröling-nahe Gruppierung | Wichtige Werte landen direkt auf dem passenden HA-Gerät und nicht nur am Gateway |

* * *

## Installation

### Option A: HACS (empfohlen)

1. HACS -> Integrationen -> `...` -> Benutzerdefinierte Repositories
2. URL: `https://github.com/itsh-neumeier/modbus_froeling-connect_local` | Kategorie: Integration
3. Integration installieren -> Home Assistant neu starten
4. Einstellungen -> Geräte & Dienste -> `+ Integration hinzufügen` -> `Froeling Connect local`

### Option B: Manuell

1. `custom_components/froeling_connect_local/` in dein Home-Assistant-Konfigurationsverzeichnis kopieren
2. Home Assistant neu starten
3. Einstellungen -> Geräte & Dienste -> `+ Integration hinzufügen` -> `Froeling Connect local`

* * *

## Konfiguration

Der Config Flow deckt sowohl die Modbus-Verbindung als auch den Anlagenaufbau ab:

1. Host, Port, Slave-ID, Abfrageintervall und Timeout eingeben
2. Geräteprofil auswählen
3. Anlagenaufbau festlegen:
   - Anzahl der Heizkreise
   - Brauchwasser-Boiler vorhanden
   - Pufferspeicher vorhanden
   - Dedizierte Brauchwasser-Wärmepumpe vorhanden
4. Optional eintragen:
   - Puffervolumen in Litern
   - Kessel-Nennleistung in kW
5. Setup abschließen; vor dem Anlegen der Integration wird der Regler getestet

### Laufzeitschätzung Für Den Puffer

Wenn ein Pufferspeicher aktiviert ist, stellt die Integration `sensor.buffer_estimated_time_to_full` bereit.

Die Schätzung nutzt:

- konfiguriertes `buffer_liters`
- konfiguriertes `boiler_power_kw`
- aktuellen `buffer_charge_percent`
- feste Annahme von `40 K` nutzbarer Temperaturspreizung

* * *

## Wichtige SP-Dual-Entitäten

### Kessel

| Entität | Register |
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

### Heizkreis 1

| Entität | Register |
|---|---:|
| `sensor.hk1_flow_temperature_actual` | `31031` |
| `sensor.hk1_flow_temperature_target` | `31032` |
| `select.hk1_operating_mode` | `48047` |
| `number.hk1_curve_temp_plus10` | `41032` |
| `number.hk1_curve_temp_minus10` | `41033` |
| `number.hk1_setback_delta` | `41034` |
| `number.hk1_pump_off_target_temp` | `41040` |
| `number.hk1_overheat_protection_temp` | `41048` |

### Boiler 1

| Entität | Register |
|---|---:|
| `sensor.dhw_temperature_top` | `31631` |
| `sensor.dhw_pump_speed` | `31633` |
| `number.dhw_target_temperature` | `41632` |
| `number.dhw_reheat_below` | `41633` |

### Puffer 1

| Entität | Register |
|---|---:|
| `sensor.buffer_top_temperature` | `32001` |
| `sensor.buffer_middle_temperature` | `32002` |
| `sensor.buffer_bottom_temperature` | `32003` |
| `sensor.buffer_pump_speed` | `32004` |
| `sensor.buffer_charge_percent` | `32007` |
| `sensor.buffer_estimated_time_to_full` | abgeleitet |
| `sensor.buffer_release_temperature` | `42001` |
| `number.buffer_delta_kessel_to_layer` | `42003` |

### Austragung

| Entität | Register |
|---|---:|
| `sensor.pellet_level_percent` | `30022` |
| `sensor.pellet_consumption_reset_kg` | `30082` |
| `sensor.pellet_consumption_reset_t` | `30083` |
| `sensor.pellet_consumption_total_t` | `30084` |
| `number.pellet_stock_remaining_t` | `40320` |
| `number.pellet_stock_minimum_t` | `40336` |
| `switch.automatic_pellet_extraction_disabled` | `40265` |

* * *

## Automationsbeispiele

> Nutzung: YAML in den Home-Assistant-Automationseditor einfügen und die Entity-IDs auf deine Installation anpassen.

### Meldung, wenn der Regler keine frischen Daten mehr liefert

```yaml
alias: "Fröling - Regler hängt"
description: "Benachrichtigt, wenn keine frischen Daten mehr ankommen"
mode: single
triggers:
  - trigger: state
    entity_id: binary_sensor.sp_dual_gateway_alive
    to: "off"
actions:
  - action: notify.mobile_app_my_phone
    data:
      title: "Fröling offline"
      message: >
        Keine frischen Fröling-Daten mehr empfangen.
        Letzte erfolgreiche Aktualisierung:
        {{ states('sensor.sp_dual_last_success') }}
```

### Gateway automatisch neu starten, wenn es hängt

```yaml
alias: "Fröling - Gateway automatisch neu starten"
description: "Drückt den Restart-Button, wenn das Gateway nicht mehr alive ist"
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

### Meldung, wenn die Asche bald geleert werden sollte

```yaml
alias: "Fröling - Aschewarnung"
description: "Benachrichtigt vor der Warnung zum Ascheleeren"
mode: single
triggers:
  - trigger: numeric_state
    entity_id: sensor.sp_dual_remaining_heating_hours_until_ash_empty
    below: 24
actions:
  - action: notify.mobile_app_my_phone
    data:
      title: "Fröling Aschewarnung"
      message: >
        Verbleibende Heizstunden bis Asche entleeren:
        {{ states('sensor.sp_dual_remaining_heating_hours_until_ash_empty') }} h
```

* * *

## Entwicklung

```bash
python -m pip install -r requirements-dev.txt
ruff check .
bandit -c pyproject.toml -r custom_components/froeling_connect_local
pytest -q
pip-audit -r requirements.txt
```

* * *

## Lizenz

MIT. Siehe [LICENSE](LICENSE).
