# Froeling Connect local

Home-Assistant-Custom-Integration fuer **lokalen** Zugriff auf Fr\u00f6ling-Regler per **Modbus TCP**.

Dieses Projekt ist fuer Home Assistant `2026.3+`, HACS-Installation und langfristige Wartbarkeit ausgelegt.

## Funktionen

- Native Home-Assistant-Integration (`config_flow`, `options_flow`)
- Lokales Modbus-TCP-Polling (keine Cloud-Abhaengigkeit)
- Geraeteprofil-Auswahl per Dropdown bei der Einrichtung
- Profildefinitionen in YAML (`device_profiles/*.yaml`)
- Modellabhaengige Vererbung mit Overrides und Excludes
- Geblockte Register-Reads via `DataUpdateCoordinator`
- Wiederverwendete TCP-Verbindung mit Timeout/Fehlerbehandlung
- Sichere Defaults:
  - nutzerrelevante Sensoren aktiv
  - Schreib-/Service-Entitaeten standardmaessig deaktiviert
- EN/DE Uebersetzungen inkl. States/Options
- HACS-Metadaten, Branding, CI, Security-Policy, Changelog

## Unterstuetzte Profile

- `lambdatronic_s3200` - Generisches Lambdatronic-S3200-Profil
- `sp_dual_compact` - Abgeleitetes Profil mit SP-Dual-Compact-Overrides

## Installation

### HACS (empfohlen)

1. HACS in Home Assistant oeffnen.
2. Custom Repository hinzufuegen: `https://github.com/timo-neumeier/froeling-connect_local`
3. Kategorie: `Integration`
4. **Froeling Connect local** installieren.
5. Home Assistant neu starten.

### Manuell

1. `custom_components/froeling_connect_local` in dein Home-Assistant-Verzeichnis `custom_components` kopieren.
2. Home Assistant neu starten.

## Konfiguration

1. `Einstellungen -> Geraete & Dienste -> Integration hinzufuegen`
2. `Froeling Connect local` suchen
3. Eingaben:
   - Host
   - Port (Standard `502`)
   - Slave-ID (Standard `2`)
   - Geraeteprofil
   - Abfrageintervall
   - Timeout
4. Bestaetigen. Vor dem Anlegen wird ein Verbindungs-Check ausgefuehrt.

### Options Flow

Ueber `Konfigurieren` an der Integrationskarte koennen Host/Port/Slave/Profil/Intervall/Timeout geaendert werden.

## Entitaets-Mapping

### Gemeinsame Status- und Telemetrie-Sensoren

| Entity key | Register | Typ | Hinweis |
|---|---:|---|---|
| `system_state` | 34001 | Enum-Sensor | Klartext-Status |
| `boiler_state` | 34002 | Enum-Sensor | Klartext-Status |
| `outside_temperature` | 31001 | Sensor | \u00b0C |
| `boiler_temperature` | 30001 | Sensor | \u00b0C |
| `flue_gas_temperature` | 30002 | Sensor | \u00b0C |
| `oxygen_residual` | 30004 | Sensor | % |
| `boiler_pump_speed` | 30068 | Sensor | % |
| `hk1_flow_temperature_actual` | 31031 | Sensor | \u00b0C |
| `hk1_flow_temperature_target` | 31032 | Sensor | \u00b0C |
| `hk2_flow_temperature_actual` | 31061 | Sensor | \u00b0C |
| `hk2_flow_temperature_target` | 31062 | Sensor | \u00b0C |
| `buffer_top_temperature` | 32001 | Sensor | \u00b0C |
| `buffer_middle_temperature` | 32002 | Sensor | \u00b0C |
| `buffer_bottom_temperature` | 32003 | Sensor | \u00b0C |
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

### Schreib-/Config-Entitaeten (standardmaessig deaktiviert)

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

### SP Dual Compact zusaetzliche Entitaeten

| Entity key | Register | Typ |
|---|---:|---|
| `ignition_runtime_hours` | 30047 | Sensor |
| `stoker_runtime_hours` | 30040 | Sensor |

## Beispiel-Automationen

### Alarm bei Kessel-Fehlerzustand

```yaml
automation:
  - alias: Froeling Kessel Fehler Alarm
    trigger:
      - platform: state
        entity_id: sensor.froeling_boiler_state
        to: "fault"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "Froeling meldet einen Kessel-Fehlerzustand."
```

### Betriebsart tagsueber auf Automatik setzen

```yaml
automation:
  - alias: Froeling HK1 Tagesmodus
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

- Geblockte Register-Reads pro Registertyp fuer weniger Netzwerk-Overhead
- Gemeinsamer Coordinator-Lock gegen parallele Modbus-Zugriffe
- Connection-Reuse mit Reconnect-Fallback
- Diagnose-Entitaeten:
  - Gateway-Verbindung
  - Roundtrip-Latenz
  - Lese-Fehlerzaehler
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
2. Checks ausfuehren
3. Version in `manifest.json` erhoehen
4. `CHANGELOG.md` aktualisieren
5. Commit + Push
6. Tag `vX.Y.Z` erstellen und pushen
7. GitHub Release veroeffentlichen

## Lizenz

MIT. Siehe [LICENSE](LICENSE).