# Fröling Connect local

Home-Assistant-Custom-Integration für **lokalen** Zugriff auf Fröling-Regler über **Modbus TCP**.

Dieses Projekt ist für Home Assistant `2026.3+`, HACS-Installation und langfristige Wartbarkeit ausgelegt.

## Funktionen

- Native Home-Assistant-Integration (`config_flow`, `options_flow`)
- Lokales Modbus-TCP-Polling (keine Cloud-Abhängigkeit)
- Geräteprofil-Auswahl per Dropdown bei der Einrichtung
- Profildefinitionen in YAML (`device_profiles/*.yaml`)
- Modellabhängige Vererbung mit Overrides und Excludes
- Geblockte Register-Reads via `DataUpdateCoordinator`
- Wiederverwendete TCP-Verbindung mit Timeout/Fehlerbehandlung
- Sichere Defaults:
  - nutzerrelevante Sensoren aktiv
  - Schreib-/Service-Entitäten standardmäßig deaktiviert
- EN/DE Übersetzungen inkl. States/Options
- HACS-Metadaten, Branding, CI, Security-Policy, Changelog

## Unterstützte Profile

- `lambdatronic_s3200` - Generisches Lambdatronic-S3200-Profil
- `sp_dual` - SP-Dual-Profil
- `sp_dual_compact` - Abgeleitetes Profil mit SP-Dual-Compact-Overrides

## Installation

### HACS (empfohlen)

1. HACS in Home Assistant öffnen.
2. Custom Repository hinzufügen: `https://github.com/itsh-neumeier/modbus_froeling-connect_local`
3. Kategorie: `Integration`
4. **Fröling Connect local** installieren.
5. Home Assistant neu starten.

### Manuell

1. `custom_components/froeling_connect_local` in dein Home-Assistant-Verzeichnis `custom_components` kopieren.
2. Home Assistant neu starten.

## Konfiguration

1. `Einstellungen -> Geräte & Dienste -> Integration hinzufügen`
2. Nach `Fröling Connect local` suchen
3. Eingaben:
   - Host
   - Port (Standard `502`)
   - Slave-ID (Standard `2`)
   - Anzahl Heizkreise (1-12)
   - Brauchwasser-Boiler vorhanden
   - Pufferspeicher vorhanden
   - Dedizierte Warmwassererwärmung (Brauchwasser-WP) vorhanden
   - Puffervolumen in Litern
   - Kessel-Nennleistung in kW (für Laufzeitschätzung)
   - Geräteprofil
   - Abfrageintervall
   - Timeout
4. Bestätigen. Vor dem Anlegen wird ein Verbindungs-Check ausgeführt.

### Options Flow

Über `Konfigurieren` an der Integrationskarte können Host/Port/Slave/Profil/Anlagen-Setup/Intervall/Timeout später angepasst werden.

### Gerätemodell in Home Assistant

Die Integration legt ein Gateway als Parent-Device an und gruppiert darunter Child-Devices (`via_device`) für:

- Kessel
- Austragung/Fördereinheit
- Pellet-Einheit
- Heizkreise
- Pufferspeicher
- optionale Brauchwasser-Wärmepumpe

### Laufzeitschätzung Puffer

Wenn ein Pufferspeicher aktiviert ist, stellt die Integration einen geschätzten Laufzeitsensor bereit:

- `sensor.buffer_estimated_time_to_full`

Die Schätzung nutzt:

- konfiguriertes `buffer_liters`
- konfiguriertes `boiler_power_kw`
- aktuellen `buffer_charge_percent`
- feste Annahme von `40 K` nutzbarer Temperaturspreizung

## Entitäts-Mapping

### Gemeinsame Status- und Telemetrie-Sensoren

| Entity key | Register | Typ | Hinweis |
|---|---:|---|---|
| `system_state` | 34001 | Enum-Sensor | Klartext-Status |
| `boiler_state` | 34002 | Enum-Sensor | Klartext-Status |
| `outside_temperature` | 31001 | Sensor | °C |
| `boiler_temperature` | 30001 | Sensor | °C |
| `flue_gas_temperature` | 30002 | Sensor | °C |
| `oxygen_residual` | 30004 | Sensor | % |
| `boiler_pump_speed` | 30068 | Sensor | % |
| `hk1_flow_temperature_actual` | 31031 | Sensor | °C |
| `hk1_flow_temperature_target` | 31032 | Sensor | °C |
| `hk2_flow_temperature_actual` | 31061 | Sensor | °C |
| `hk2_flow_temperature_target` | 31062 | Sensor | °C |
| `buffer_top_temperature` | 32001 | Sensor | °C |
| `buffer_middle_temperature` | 32002 | Sensor | °C |
| `buffer_bottom_temperature` | 32003 | Sensor | °C |
| `buffer_charge_percent` | 32007 | Sensor | % |
| `pellet_level_percent` | 30022 | Sensor | % |
| `daily_energy_kwh` | 30085 | Sensor | kWh |
| `total_energy_kwh` | 30086 | Sensor | kWh |

### Binary-Sensoren

| Entity key | Register | Typ |
|---|---:|---|
| `heat_demand_active` | 30057 | binary_sensor |
| `buffer_heat_recovery_active` | 42002 | binary_sensor |
| `legionella_cycle_active` | 41637 | binary_sensor |
| `gateway_connected` | Diagnose-binary_sensor |

### Schreib-/Config-Entitäten (standardmäßig deaktiviert)

| Entity key | Register | Plattform |
|---|---:|---|
| `automatic_ignition` | 40136 | switch |
| `hk1_enabled` | 48029 | switch |
| `hk2_enabled` | 48030 | switch |
| `boiler_target_temperature` | 40001 | number |
| `hk1_modbus_target_temperature` | 48001 | number |
| `hk2_modbus_target_temperature` | 48002 | number |
| `dhw_modbus_target_temperature` | 48019 | number |
| `pellet_stock_remaining_t` | 40320 | number |
| `hk1_operating_mode` | 48047 | select |
| `hk2_operating_mode` | 48048 | select |
| `fuel_selection` | 40441 | select |

### SP Dual Compact zusätzliche Entitäten

| Entity key | Register | Typ |
|---|---:|---|
| `ignition_runtime_hours` | 30047 | Sensor |
| `stoker_runtime_hours` | 30040 | Sensor |

## Beispiel-Automationen

### Alarm bei Kessel-Fehlerzustand

```yaml
automation:
  - alias: Fröling Kessel Fehler Alarm
    trigger:
      - platform: state
        entity_id: sensor.froeling_boiler_state
        to: "fault"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "Fröling meldet einen Kessel-Fehlerzustand."
```

### Betriebsart tagsüber auf Automatik setzen

```yaml
automation:
  - alias: Fröling HK1 Tagesmodus
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

## Diagnostik und Robustheit

- Geblockte Register-Reads pro Registertyp für weniger Netzwerk-Overhead
- Gemeinsamer Coordinator-Lock gegen parallele Modbus-Zugriffe
- Connection-Reuse mit Reconnect-Fallback
- Diagnose-Entitäten:
  - Gateway-Verbindung
  - Roundtrip-Latenz
  - Lese-Fehlerzähler
  - letzter Fehlertext
  - Zeitstempel letzter erfolgreicher Aktualisierung

## Sicherheit

- Laufzeit-Dependencies mit Versionsbereich und CI-Audit (`pip-audit`)
- Statische Analyse in CI: `ruff`, `bandit`
- Security-Meldungsprozess: siehe [SECURITY.md](SECURITY.md)

## Entwicklung

```bash
python -m pip install -r requirements-dev.txt
ruff check .
bandit -c pyproject.toml -r custom_components/froeling_connect_local
pytest -q
pip-audit -r requirements.txt
```

## Release-Prozess

1. Code und Tests aktualisieren
2. Checks ausführen
3. Version in `manifest.json` erhöhen
4. `CHANGELOG.md` aktualisieren
5. Commit + Push
6. Tag `vX.Y.Z` erstellen und pushen
7. GitHub Release veröffentlichen

## Lizenz

MIT. Siehe [LICENSE](LICENSE).
