# Wind Farm SCADA API Guide

Digital Wind Turbine Simulator — API Reference for Students & Researchers

> National Chin-Yi University of Technology (NCUT), DOF Lab
> Last updated: 2026-04-12

---

## Quick Start

### 1. Requirements

- Python 3.10+
- `pip install requests websocket-client pandas`

### 2. Start the Server

```bash
cd digiWindTurbine
python run.py                    # default port 8100
python run.py --port 9000        # custom port
python run.py --auto-port        # auto-find available port
```

### 3. Verify Connection

```python
import requests
r = requests.get("http://localhost:8100/api/health")
print(r.json())
# {"status": "ok", "mode": "simulation", "turbineCount": 14}
```

### 4. API Documentation (Interactive)

Open in browser: `http://localhost:8100/docs` (Swagger UI)

---

## Connection Info

| Item | Value |
|------|-------|
| Default Port | `8100` |
| Host Binding | `0.0.0.0` (all interfaces) |
| LAN Access | `http://<server-ip>:8100` |
| CORS | Open (`*`) |
| Authentication | None (open access) |
| WebSocket | `ws://<server-ip>:8100/ws/realtime` |

---

## SCADA Tag System

The simulator outputs **74 SCADA tags** per turbine, organized by subsystem:

| Subsystem | Tag Count | Description |
|-----------|-----------|-------------|
| WTUR | 2 | Turbine state & total power |
| WGEN | 7 | Generator (power, speed, voltage, current, temps) |
| WROT | 9 | Rotor / pitch (RPM, blade angles, temps, brake) |
| WCNV | 16 | Converter (DC voltage, frequency, reactive power, ride-through) |
| WGDC | 1 | Transformer temperature |
| WMET | 3 | Meteorological (wind speed, direction, ambient temp) |
| WNAC | 4 | Nacelle (temps, vibration X/Y) |
| WYAW | 3 | Yaw (alignment error, brake pressure, cable windup) |
| WVIB | 20 | Vibration spectral (5 bands x 2 directions + crest/kurtosis + 8 alarm thresholds) |
| WFAT | 7 | Fatigue loads (tower/blade moments, DEL, cumulative damage) |
| WSRV/MBUS | 2 | Service mode, local/remote control |

### Get Tag Registry

```python
r = requests.get("http://localhost:8100/api/i18n/tags/registry")
tags = r.json()  # List of {id, opc_tag, subsystem, data_type, unit, label_en, label_zh, sim_min, sim_max, ...}
```

### Key Tag IDs

```
# Power & Speed
WTUR_TotPwrAt      # Total active power (kW)
WGEN_GnSpd         # Generator speed (RPM)
WROT_RotSpd         # Rotor speed (RPM)
WMET_WSpeedNac      # Wind speed (m/s)

# Temperatures
WGEN_GnStaTmp1      # Generator stator temp (deg C)
WGEN_GnBrgTmp1      # Generator bearing temp (deg C)
WNAC_NacTmp         # Nacelle temp (deg C)

# Vibration Spectral
WVIB_Band1pX/Y      # 1P frequency band (mm/s)
WVIB_Band3pX/Y      # 3P blade-pass band (mm/s)
WVIB_BandGearX/Y    # Gear mesh band (mm/s)
WVIB_BandHfX/Y      # High-frequency band (mm/s)
WVIB_BandBbX/Y      # Broadband (mm/s)
WVIB_CrestFactor    # Peak/RMS ratio
WVIB_Kurtosis       # Signal kurtosis

# Vibration Alarms (0=normal, 1=warning, 2=alarm)
WVIB_Alarm1p / Alarm3p / AlarmGear / AlarmHf / AlarmBb / AlarmOverall
WVIB_Thresh1pWarn   # Current 1P warning threshold (mm/s)
WVIB_Thresh1pAlrm   # Current 1P alarm threshold (mm/s)

# Fatigue / Load
WFAT_TwrBsMy        # Tower base fore-aft moment (kNm)
WFAT_TwrBsMx        # Tower base side-to-side moment (kNm)
WFAT_BldRtMy        # Blade root flapwise moment (kNm)
WFAT_BldRtMx        # Blade root edgewise moment (kNm)
WFAT_DELTwr         # Tower DEL indicator (0-100)
WFAT_DELBld         # Blade DEL indicator (0-100)
WFAT_DmgAccum       # Cumulative damage fraction (0-1)

# Electrical Response
WCNV_ReactPwr       # Reactive power (kvar)
WCNV_PwrFactor      # Power factor
WCNV_FreqWattDerate # Frequency-watt derate factor
```

---

## API Endpoints

### Realtime Data

#### GET `/api/turbines`

Returns all turbines with current SCADA data.

```python
r = requests.get("http://localhost:8100/api/turbines")
turbines = r.json()  # List of TurbineReading objects

for t in turbines:
    print(f"{t['turbineId']}  Power={t['powerOutput']:.3f}MW  Wind={t['windSpeed']:.1f}m/s")
    # Full SCADA dict available at t['scadaTags']
```

#### GET `/api/turbines/{turbine_id}`

Single turbine (e.g., `WT001` to `WT014`).

```python
r = requests.get("http://localhost:8100/api/turbines/WT001")
t = r.json()
scada = t['scadaTags']  # dict of 74 tag_id -> float
print(f"Tower load = {scada['WFAT_TwrBsMy']:.1f} kNm")
```

#### GET `/api/turbines/farm-status`

Farm-level aggregated KPIs.

```python
r = requests.get("http://localhost:8100/api/turbines/farm-status")
farm = r.json()
# {"totalTurbines": 14, "operatingCount": 14, "totalPowerMW": 5.23, "avgWindSpeed": 8.1, ...}
```

#### GET `/api/export/snapshot`

All turbines in a single response (same data as `/api/turbines` but in `{count, data[]}` format).

---

### Historical Data

#### GET `/api/turbines/{turbine_id}/history`

Query stored history from SQLite.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | ISO datetime | — | Start time filter |
| `end` | ISO datetime | — | End time filter |
| `limit` | int | 100 | Max rows (1-10000) |

```python
r = requests.get("http://localhost:8100/api/turbines/WT001/history", params={
    "limit": 500,
    # "start": "2026-04-12T00:00:00",
    # "end": "2026-04-12T12:00:00",
})
data = r.json()
readings = data['data']    # List of history records with scada_json
events = data['events']    # List of events in same time range
```

#### GET `/api/turbines/{turbine_id}/trend`

In-memory trend buffer (up to 1 hour @ 1Hz, no persistence required).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tags` | comma-sep | all | SCADA tag IDs to include |
| `limit` | int | 100 | Max points (1-3600) |

```python
r = requests.get("http://localhost:8100/api/turbines/WT001/trend", params={
    "tags": "WTUR_TotPwrAt,WMET_WSpeedNac,WFAT_TwrBsMy",
    "limit": 300,
})
trend = r.json()
# {"turbineId": "WT001", "tags": [...], "count": 300, "data": [{timestamp, tag_values...}, ...]}
```

#### GET `/api/turbines/farm-trend`

Farm-level downsampled trend.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `range` | string | `1h` | `5m`, `1h`, `12h`, `1d` |
| `points` | int | 60 | Downsample target (10-500) |

---

### Data Export

#### GET `/api/export/history`

Server-side export with format selection.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `turbine_id` | string | required | e.g., `WT001` |
| `format` | string | `json` | `json` or `csv` |
| `start` | ISO datetime | — | Start filter |
| `end` | ISO datetime | — | End filter |
| `limit` | int | 500 | Max rows |

```python
# JSON format
r = requests.get("http://localhost:8100/api/export/history", params={
    "turbine_id": "WT001", "format": "json", "limit": 1000
})
data = r.json()

# CSV format (streamed file download)
r = requests.get("http://localhost:8100/api/export/history", params={
    "turbine_id": "WT001", "format": "csv", "limit": 1000
})
with open("WT001_history.csv", "wb") as f:
    for chunk in r.iter_content(8192):
        f.write(chunk)
```

#### GET `/api/export/events`

Export event log.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `turbine_id` | string | — | Filter by turbine |
| `event_type` | string | — | `fault`, `grid`, `operator`, `state`, `wind` |
| `format` | string | `json` | `json` or `csv` |
| `limit` | int | 200 | Max events |

---

### WebSocket Realtime Stream

All turbines broadcast every 2 seconds.

```python
import websocket
import json

ws = websocket.create_connection("ws://localhost:8100/ws/realtime")
while True:
    msg = ws.recv()
    turbines = json.loads(msg)  # List of 14 TurbineReading objects
    for t in turbines:
        scada = t.get("scadaTags", {})
        print(f"{t['turbineId']}  Power={t['powerOutput']:.3f}MW  "
              f"TwrMy={scada.get('WFAT_TwrBsMy', 0):.0f}kNm  "
              f"AlarmLv={scada.get('WVIB_AlarmOverall', 0)}")
```

---

### Simulation Control

#### POST `/api/config/wind`

Set wind profile.

```python
# Use preset profile
requests.post("http://localhost:8100/api/config/wind", json={"profile": "strong"})
# Profiles: calm, moderate, rated, strong, storm, gusty, ramp_up, ramp_down, auto

# Manual override
requests.post("http://localhost:8100/api/config/wind", json={
    "windSpeed": 15.0,
    "windDirection": 270.0,
    "ambientTemp": 25.0,
})

# Return to auto mode
requests.post("http://localhost:8100/api/config/wind/clear")
```

#### POST `/api/config/grid`

Set grid conditions.

```python
requests.post("http://localhost:8100/api/config/grid", json={"profile": "low_freq"})
# Profiles: nominal, low_freq, high_freq, undervoltage, overvoltage, weak_grid, recovery, auto
```

#### POST `/api/faults/inject`

Inject fault for diagnostic study.

```python
requests.post("http://localhost:8100/api/faults/inject", json={
    "scenarioId": "bearing_wear",
    "turbineId": "WT001",
    "severityRate": 0.005,
    "initialSeverity": 0.0,
})
# Available: bearing_wear, pitch_imbalance, gearbox_overheat, blade_icing,
#            generator_overspeed, yaw_misalignment, stator_winding_degradation,
#            hydraulic_leak, nacelle_cooling_failure, converter_cooling_fault, grid_voltage_sag
```

#### POST `/api/faults/clear`

```python
requests.post("http://localhost:8100/api/faults/clear", json={
    "turbineId": "WT001",
    "scenarioId": "bearing_wear",
})
```

#### POST `/api/control/command`

Operator commands.

```python
requests.post("http://localhost:8100/api/control/command", json={
    "turbineId": "WT001",
    "command": "stop",         # stop, emergency_stop, start, reset, service_on, service_off
})
```

---

### Multi-Turbine Event Comparison

```python
r = requests.get("http://localhost:8100/api/maintenance/events/compare", params={
    "turbine_ids": "WT001,WT002,WT003",
    "event_type": "fault",
    "limit": 50,
})
data = r.json()
# {"turbines": [...], "per_turbine": {...}, "timeline": [...], "summary": {...}}
```

---

## Complete Usage Example: Collect & Analyze

```python
import requests
import pandas as pd
import time

SERVER = "http://localhost:8100"

# 1. Set wind to strong
requests.post(f"{SERVER}/api/config/wind", json={"profile": "strong"})
print("Wind set to strong profile")

# 2. Collect 60 seconds of data
rows = []
for i in range(30):
    r = requests.get(f"{SERVER}/api/turbines/WT001")
    t = r.json()
    row = {"timestamp": t["timestamp"], "status": t["status"]}
    row.update(t.get("scadaTags", {}))
    rows.append(row)
    time.sleep(2)

# 3. Build DataFrame
df = pd.DataFrame(rows)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

# 4. Analyze
print(f"\nCollected {len(df)} samples")
print(df[['WTUR_TotPwrAt', 'WMET_WSpeedNac', 'WFAT_TwrBsMy', 'WVIB_BandHfX']].describe())

# 5. Save to CSV
df.to_csv("WT001_strong_wind.csv", encoding="utf-8-sig")
print("Saved to WT001_strong_wind.csv")

# 6. Inject fault and observe
requests.post(f"{SERVER}/api/faults/inject", json={
    "scenarioId": "bearing_wear",
    "turbineId": "WT001",
    "severityRate": 0.01,
})
print("\nBearing wear fault injected. Monitor vibration changes...")

# 7. Collect fault data
fault_rows = []
for i in range(30):
    r = requests.get(f"{SERVER}/api/turbines/WT001")
    t = r.json()
    row = {"timestamp": t["timestamp"]}
    row.update(t.get("scadaTags", {}))
    fault_rows.append(row)
    time.sleep(2)

df_fault = pd.DataFrame(fault_rows)
print(f"\nHF band before fault: {df['WVIB_BandHfX'].mean():.4f}")
print(f"HF band during fault: {df_fault['WVIB_BandHfX'].mean():.4f}")

# 8. Clear fault
requests.post(f"{SERVER}/api/faults/clear", json={"turbineId": "WT001"})
requests.post(f"{SERVER}/api/config/wind/clear")
```

---

## Example Script

A ready-to-use Python script with 8 example functions is available at:

```
examples/fetch_scada_data.py
```

Edit `SERVER_URL` at the top of the file, then run:

```bash
python examples/fetch_scada_data.py
```

---

## Turbine IDs

| ID | Name |
|----|------|
| WT001 ~ WT014 | WTG-01 ~ WTG-14 |

## Turbine States (TurState 1-9)

| State | Description |
|-------|-------------|
| 1 | Idle (stopped, locked) |
| 2 | Preheating |
| 3 | Ready / standby |
| 4 | Startup (pitching to work) |
| 5 | Synchronizing |
| 6 | **Producing** (normal operation) |
| 7 | Emergency stop |
| 8 | Fault lockout |
| 9 | Normal stop in progress |

## Fault Scenarios

| ID | Description |
|----|-------------|
| `bearing_wear` | Main bearing degradation |
| `pitch_imbalance` | Pitch angle mismatch between blades |
| `gearbox_overheat` | Gearbox temperature rise |
| `blade_icing` | Ice accumulation on blades |
| `generator_overspeed` | Generator overspeed condition |
| `yaw_misalignment` | Yaw system alignment error |
| `stator_winding_degradation` | Generator stator winding fault |
| `hydraulic_leak` | Hydraulic system pressure loss |
| `nacelle_cooling_failure` | Nacelle cooling system fault |
| `converter_cooling_fault` | Converter cooling degradation |
| `grid_voltage_sag` | Grid voltage dip event |
