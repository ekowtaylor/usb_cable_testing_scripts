# USB Cable Validation Test Suite

**Document Owner:** Ekow Taylor, Network Infrastructure Services
**Revision:** 1.1 | **Date:** May 15, 2026 | **Status:** In Progress

## Purpose

This test suite validates USB-C cables for use in Plan A.2 MacBook M4 service shelf deployments connecting to the Ramsey STE4453M4 RF shielded test enclosure. It automates the electrical and signal-integrity tests defined in the USB Cable Validation Test Plan.

### Cables Under Test

| Attribute | U420-010 | U420-006 |
|---|---|---|
| **SKU** | U420-010 | U420-006 |
| **Manufacturer** | Tripp Lite | Tripp Lite |
| **Length** | 10ft (3.05m) | 6ft (1.83m) |
| **Connector** | USB-C male to USB-C male | USB-C male to USB-C male |
| **Rated Speed** | USB 3.1 Gen 1 (5Gbps) | USB 3.1 Gen 1 (5Gbps) |
| **Type** | Passive | Passive |

The U420-010 operates at the practical limit of passive USB 3.1 Gen 1 signaling at 3m. The U420-006 at 1.83m provides more signal margin and serves as a comparison baseline.

### Why These Cables Require Validation

The deployment environment — dense racks with significant electromagnetic interference from adjacent powered equipment — represents a more challenging signal environment than typical consumer or office installations. At 3m (U420-010), signal attenuation approaches the edge of the USB-IF specification budget for passive cables at 5Gbps.

## Signal Chain Under Test

```
Apple MacBook M4 (USB-C / Thunderbolt port)
  → Tripp Lite cable (USB-C to USB-C, 5Gbps passive)   ← CABLE UNDER TEST
    → Ramsey STE4453M4 USB-C I/O Interface (rated 20Gbps)
      → Acroname S79-USBHUB-3P / USBHub3c (5Gbps hub, inside enclosure)
        → DUT or USB storage device
```

**Speed-governing component:** Acroname USBHub3c (caps throughput at 5Gbps). The MacBook M4 TB4 port and STE4453M4 interface are both capable of higher speeds but will negotiate down to 5Gbps due to the hub.

> **Note:** Tests can also be run without the Ramsey enclosure for initial cable qualification (direct MacBook → cable → Acroname hub).

## Acroname USBHub3c Port Topology

The Acroname USBHub3c exposes two distinct USB interfaces to the host:

| Interface | ioreg Device Name | Function | Max Speed |
|---|---|---|---|
| **Control (Stem)** | `USBHub3c-Stem` / `USBHub3c_Stem` | BrainStem API management | 5 Gbps (capped) |
| **Data (Up0)** | `USBHub3c-3-Up0` (USB 3.x) / `USBHub3c-2-Up0` (USB 2.x companion) | Data transfer | 20 Gbps |

This distinction is critical: **the control port caps at 5Gbps regardless of cable capability**. To measure true cable signal performance, cables must be tested on the data port.

The BrainStem API communicates over the control (Stem) connection. When running port-cycling tests on the data port, a separate cable must remain connected to the Stem port to maintain API control.

## Prerequisites

### Hardware
- Apple MacBook M4 (with USB-C / Thunderbolt port)
- An Acroname BrainStem USB hub connected via USB-C. The suite auto-detects
  the model (tested with **USBHub3c** and **USBHub3p**); the hub class,
  serial, port count, and ioreg device-node names are resolved at runtime
  — nothing is hardcoded to a specific model.
- Cable samples under test (minimum 3, preferably from different manufacturing lots)
- USB 3.0+ storage device (for bandwidth tests 5.2.x — not required for link tests)

### Software
- macOS (tested on macOS 15.x / Darwin 25.4.0)
- Python 3.12+
- Acroname BrainStem SDK:
  ```bash
  pip3 install brainstem
  ```

## Test Descriptions

All test scripts support the following common flags:
- `sample_label` (positional) — identifies the cable sample (e.g., `u420_010_sample_1`)
- `--device control|data` — which hub interface to monitor for speed (default: `control`)
- `--port N` — which hub port to cycle for cycling tests (default: `0`)

### Test 5.1.1 — Initial Link Speed Verification

**Script:** `test_5_1_1_link_speed.py`
**Runtime:** ~1 second
**Objective:** Verify the cable negotiates SuperSpeed (5Gbps) or higher and does not fall back to USB 2.0.

**Method:** Queries `ioreg -p IOUSB` for the Acroname hub's `USBSpeed` property.

**Pass criteria:** USBSpeed >= 3 (SuperSpeed or better)
**Fail criteria:** USBSpeed < 3 (USB 2.0 fallback) or device not enumerated

```bash
python3 test_5_1_1_link_speed.py u420_010_sample_1 --device data
```

### Test 5.1.2 — Connect/Disconnect Cycling

**Script:** `test_5_1_2_connect_disconnect.py`
**Runtime:** ~5–7 minutes (20 cycles)
**Objective:** Verify the cable reliably re-negotiates SuperSpeed after repeated disconnection and reconnection.

**Method:** Uses the Acroname BrainStem API to disable and re-enable a hub port (simulating a cable disconnect/reconnect), then polls for re-enumeration and checks speed. Each cycle:
1. Disable hub port via `hub.usb.setPortDisable()` — simulates cable unplug
2. Wait 5 seconds
3. Re-enable port via `hub.usb.setPortEnable()` — simulates cable plug
4. Poll for re-enumeration (up to 30 seconds)
5. Verify SuperSpeed negotiation

**Pass criteria:** 20/20 cycles negotiate SuperSpeed or better
**Fail criteria:** Any single cycle results in USB 2.0 fallback or no enumeration

```bash
python3 test_5_1_2_connect_disconnect.py u420_010_sample_1 --port 0 --device data
```

### Test 5.1.4 — Sleep/Wake Cycling

**Script:** `test_5_1_4_sleep_wake.py`
**Runtime:** ~10 minutes (10 cycles)
**Objective:** Verify the USB link re-establishes at SuperSpeed after macOS sleep/wake transitions.

**Method:** Uses `pmset` to put the Mac to sleep with a scheduled wake, then verifies re-enumeration at SuperSpeed after wake. Each cycle:
1. Schedule a wake via `sudo pmset schedule wake`
2. Put Mac to sleep via `pmset sleepnow`
3. After wake, poll for hub re-enumeration (up to 60 seconds)
4. Verify SuperSpeed negotiation

**Pass criteria:** 10/10 wake cycles restore SuperSpeed within 60 seconds
**Fail criteria:** Any wake results in fallback, no re-enumeration, or delayed recovery >60 seconds

**Requires sudo (uses pmset):**
```bash
sudo python3 test_5_1_4_sleep_wake.py u420_010_sample_1 --device data
```

### Test 5.2.3 — Acroname Hub API Control Cycling

**Script:** `test_5_2_3_acroname_cycling.py`
**Runtime:** ~10 minutes at 50 cycles (default), scales linearly
**Objective:** Stress-test the cable's ability to maintain reliable SuperSpeed negotiation over many rapid connect/disconnect cycles.

**Method:** Same port disable/enable mechanism as 5.1.2 but with configurable cycle count:
1. Disable hub port — wait 5 seconds
2. Re-enable hub port
3. Poll for re-enumeration (up to 30 seconds)
4. Verify SuperSpeed negotiation
5. Progress reported every 10 cycles

**Pass criteria:** All cycles enumerate correctly at SuperSpeed, no API timeouts
**Fail criteria:** Any cycle fails to enumerate, reports wrong speed, or times out

```bash
python3 test_5_2_3_acroname_cycling.py u420_010_sample_1 --port 0 --device data --cycles 50
```

## Usage

### Running Individual Tests

```bash
# Test on control port (Stem) — caps at 5Gbps
python3 test_5_1_1_link_speed.py u420_010_sample_1 --device control

# Test on data port (Up0) — shows true cable capability
python3 test_5_1_1_link_speed.py u420_010_sample_1 --device data
```

### Running All Tests (except sleep/wake)

```bash
./run_all.sh [sample_label] [device] [port]
# Example: ./run_all.sh u420_010_sample_1 data 0
```

This runs tests 5.1.1, 5.1.2, and 5.2.3 sequentially. Test 5.1.4 (sleep/wake) must be run separately with sudo.

### Two-Cable Setup (Recommended for Data Port Testing)

To test a cable on the data port while maintaining BrainStem API control:
1. Connect a **control cable** from the Mac to the hub's Stem port
2. Connect the **cable under test** from the Mac (different USB-C port) to the hub's data port 0
3. Run tests with `--device data --port 0`

This allows port cycling without losing API connectivity.

## Results

All test results are logged to CSV files in the `results/` directory:

| File | Test |
|---|---|
| `results/5_1_1_link_speed.csv` | Initial Link Speed Verification |
| `results/5_1_2_connect_disconnect.csv` | Connect/Disconnect Cycling |
| `results/5_1_4_sleep_wake.csv` | Sleep/Wake Cycling |
| `results/5_2_3_acroname_cycling.csv` | Acroname Hub API Cycling |

Each CSV contains columns: `timestamp`, `cycle`, `status`, `speed_code`, `speed_label`, `notes`

Results from different cable samples and models accumulate in the same CSV files, distinguished by the `cycle` column which includes the sample label.

## Architecture

```
usb_cable_testing_scripts/
├── README.md                          # This file
├── TESTING_LOG.md                     # Detailed test session log and findings
├── .gitignore
├── usb_utils.py                       # Shared utilities (speed detection, logging)
├── test_5_1_1_link_speed.py           # Link speed verification
├── test_5_1_2_connect_disconnect.py   # Connect/disconnect cycling (20 cycles)
├── test_5_1_4_sleep_wake.py           # Sleep/wake cycling (requires sudo)
├── test_5_2_3_acroname_cycling.py     # Stress test (default 50 cycles)
├── run_all.sh                         # Sequential test runner
└── results/                           # CSV test results (gitignored)
```

### USB Speed Detection

All tests use `ioreg -p IOUSB` to query the Acroname hub's negotiated link speed. The `USBSpeed` property maps to:

| Code | Speed | Rate |
|---|---|---|
| 0 | Low Speed | 1.5 Mbps |
| 1 | Full Speed | 12 Mbps |
| 2 | High Speed | 480 Mbps |
| 3 | SuperSpeed | 5 Gbps |
| 4 | SuperSpeed+ | 10 Gbps |
| 5 | SuperSpeed+ 2x1 | 20 Gbps |

A passing result requires `USBSpeed >= 3`.

> **Note:** `system_profiler SPUSBDataType` may return empty output on some macOS configurations. The `ioreg` method is used as the primary detection mechanism.

#### Model-agnostic detection

Device-node names are **not** hardcoded. `usb_utils.py` scans `ioreg -p IOUSB -l`
for nodes whose vendor is `Acroname Inc.`, then classifies them by name:
the control interface always contains `Stem` (e.g. `USBHub3c-Stem`,
`USBHub3p-Stem`); everything else is the data path. For the data path the
**highest-speed** Acroname node is reported, so a USB-2 fallback (only the
USB-2 companion present, SuperSpeed node gone) is correctly reported as
High Speed instead of being misclassified as an enumeration timeout.

The BrainStem hub class is chosen from the discovered model code
(`USBHub3p` = model 19), falling back to probing known classes. Port range
varies by model (USBHub3c: 0–3, USBHub3p: 0–7); an out-of-range `--port`
prints a warning.

> **USBHub3p note:** on the 3p the Stem/control interface is a USB-2
> management port (enumerates at Full Speed, 12 Mbps) — it is *not* a
> 5 Gbps control port like the 3c's. On a 3p, run cable validation with
> `--device data` against a downstream data port; `--device control` will
> always fail the SuperSpeed criterion by design.

### BrainStem API Considerations

- The BrainStem API communicates over the hub's control (Stem) USB connection
- Abruptly killing a running test script (Ctrl+C, `kill`) while the API has an active session can leave the hub in a `CONNECTION_ERROR` state (error code 25)
- **Recovery:** physically unplug and replug the control cable to reset the hub
- Port cycling on the control port drops the API connection; the scripts handle this by reconnecting each cycle
- For data port testing, maintain a separate control cable connection for uninterrupted API access

## Decision Criteria

| Outcome | Action |
|---|---|
| All tests pass on all samples | Cable approved for volume procurement |
| Intermittent failures on 1 sample, others pass | Possible batch issue — order 5 additional samples from a different lot, retest failing scenarios |
| Link negotiation failures (5.1.x) | Cable cannot be relied upon — evaluate shorter cable or active alternative |
| Consistent failures on one cable model but not the other | Shorter cable (U420-006) may be required; document minimum viable cable length |
| Enumeration timeout failures only (no speed fallback) | May be OS-level USB re-enumeration delay, not cable issue — increase polling timeout and retest |

## Future Tests (Require Additional Equipment)

The following tests are defined in the full test plan but require the Ramsey STE4453M4 enclosure and production rack environment:

- **5.1.3** — Cold Boot Negotiation
- **5.2.1** — Baseline Throughput Measurement
- **5.2.2** — 72-Hour Soak Test with Data Integrity
- **5.3.1** — Bench Baseline vs. Rack Loaded Comparison
- **5.3.2** — Worst-Case Cable Routing
- **5.3.3** — Adjacent Equipment Power Cycling Interference
- **5.3.4** — Sliding Service Shelf Extension Under Load
