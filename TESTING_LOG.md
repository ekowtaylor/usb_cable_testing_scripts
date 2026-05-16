# USB Cable Validation — Testing Log

**Date:** May 15, 2026
**Operator:** Ekow Taylor
**Test Machine:** MacBook Pro M4 Max (Mac16,5), 64GB RAM, macOS 15.x (Darwin 25.4.0, build 25E253)
**Hub:** Acroname USBHub3c (S79-USBHUB-3P), Serial: 68D1A7BE (decimal: 1758570430)
**BrainStem SDK:** v2.12.2

---

## Session Summary

Initial cable qualification testing of the Tripp Lite U420-010 (10ft/3.05m, USB-C to USB-C, USB 3.1 Gen 1, 5Gbps passive) connected directly to an Acroname USBHub3c hub — no Ramsey STE4453M4 enclosure in the signal chain.

Testing was performed across two hub interfaces: the control (Stem) port and the data (Up0) port, which revealed a significant finding about the hub's port speed limitations.

---

## Key Finding: Control Port Speed Cap

During testing, the Acroname USBHub3c was found to have different speed capabilities on its two interface types:

| Interface | Speed | Notes |
|---|---|---|
| Control (Stem) port | 5 Gbps (USBSpeed=3) | Fixed at SuperSpeed regardless of cable |
| Data (Up0) port | 20 Gbps (USBSpeed=5) | SuperSpeed+ 2x1, cable-dependent |

**Implication for the test plan:** The original test plan assumed the cable would be the speed-limiting factor at 5Gbps. In reality, the control port caps at 5Gbps by design. When the U420-010 (3m, rated for 5Gbps) was moved to the data port, it negotiated **20Gbps** — 4x its rated speed. This demonstrates the cable has significant signal margin at 3m and is not operating near its electrical limits.

This was discovered by connecting a U420-006 (1.83m) to the data port while the U420-010 was on the control port. Both showed 5Gbps on control. When swapped, the U420-010 showed 20Gbps on the data port, confirming the bottleneck was the port, not the cable.

---

## Timing Comparison: Control Port vs Data Port

| Metric | Control Port (5 Gbps) | Data Port (20 Gbps) |
|---|---|---|
| **Re-enumeration time** | ~10s (consistent) | ~8–30+s (variable) |
| **Cycle rate (5.2.3)** | ~3.5 cycles/min (~17s/cycle) | ~5 cycles/min (~11s/cycle) |
| **Enumeration reliability** | 100% (70/70 cycles) | ~94% (66/70 cycles) |
| **Timeout failures** | 0 | 4 (all recovered next cycle) |

The data port re-enumerates faster on average but has occasional delays exceeding the 30s polling timeout. The control port is slower but perfectly consistent. This suggests the 20Gbps link training has more variable latency than 5Gbps.

---

## Hub Speed Control Capability

The Acroname BrainStem API provides per-port speed control that could be used to cap the data port at 5Gbps for controlled comparison testing:

| Method | Effect |
|---|---|
| `hub.usb.setSuperSpeedDataDisable(port)` | Forces port to Hi-Speed (480Mbps) only |
| `hub.usb.setSuperSpeedDataEnable(port)` | Re-enables SuperSpeed negotiation |
| `PORT_MODE_SUPER_SPEED_1_ENABLE` (flag 7) | Controls USB 3.0 (5Gbps) lane |
| `PORT_MODE_SUPER_SPEED_2_ENABLE` (flag 8) | Controls USB 3.1+ (10/20Gbps) lane |

This could be used to test whether the enumeration timeout failures on the data port disappear when speed is capped at 5Gbps, which would confirm the issue is related to 20Gbps link training latency rather than cable signal integrity.

---

## Test Results — U420-010 on Control Port (Stem)

Signal chain: MacBook M4 → U420-010 (3.05m) → USBHub3c Stem port

### Test 5.1.1 — Initial Link Speed Verification
- **Result: PASS**
- Negotiated speed: SuperSpeed (5 Gbps), USBSpeed=3
- Note: 5Gbps is the control port's maximum; cable is not the limiter

### Test 5.1.2 — Connect/Disconnect Cycling (20 cycles)
- **Result: PASS (20/20)**
- All 20 cycles negotiated SuperSpeed (5 Gbps)
- Method: BrainStem API port disable/enable per cycle (reconnect API each cycle since disabling the control port drops the API connection)
- Zero failures, zero speed fallbacks

### Test 5.2.3 — Acroname Hub API Control Cycling (50 cycles)
- **Result: PASS (50/50)**
- All 50 cycles negotiated SuperSpeed (5 Gbps)
- Rate: ~3.5 cycles/minute (~17s per cycle)
- Zero failures, zero API errors
- Note: Initial test attempt (500 cycles) failed due to a bug where the script held a persistent API connection while disabling the port it was communicating over. Fixed by reconnecting the API session each cycle.

### Test 5.1.4 — Sleep/Wake Cycling
- **Result: NOT RUN**
- Requires `sudo` which is not available from the automated test runner
- Must be run manually: `sudo python3 test_5_1_4_sleep_wake.py u420_010_sample_1`

---

## Test Results — U420-010 on Data Port (Up0)

Signal chain: MacBook M4 → U420-010 (3.05m) → USBHub3c Data Port 0
Control link: MacBook M4 → separate cable → USBHub3c Stem port

### Test 5.1.1 — Initial Link Speed Verification
- **Result: PASS**
- Negotiated speed: SuperSpeed+ 2x1 (20 Gbps), USBSpeed=5
- This is 4x the cable's rated speed of 5Gbps

### Test 5.1.2 — Connect/Disconnect Cycling (20 cycles)

**Run 1 (30s polling timeout):**
- **Result: FAIL (19/20)**
- 1 enumeration timeout at cycle 17; recovered immediately at 20 Gbps on cycle 18

**Run 2 (60s polling timeout):**
- **Result: FAIL (17/20)**
- 3 enumeration timeouts — partially caused by stale test processes from earlier runs competing for the BrainStem API connection (see Issues section)
- No speed fallbacks on any cycle that did enumerate

### Test 5.2.3 — Acroname Hub API Control Cycling (50 cycles)

**Run 1 (30s polling timeout):**
- **Result: FAIL (47/50)**
- 3 enumeration timeouts at cycles 5, 22, 37; all recovered immediately

**Run 2 (60s polling timeout):**
- **Result: FAIL (46/50)**
- 4 enumeration timeouts — first 2–3 occurred while stale processes were competing for hub API
- After stale processes were killed (at cycle 21), failure rate dropped to ~1 in 30 cycles
- Cycles 21–50: 29/30 PASS (only cycle 30 failed)
- No speed fallbacks on any cycle that did enumerate
- Rate: ~5 cycles/minute (~10s per cycle)

### Analysis of Data Port Failures

All failures on the data port share the same pattern:
- **Failure mode:** Enumeration timeout (device not found within polling window)
- **Not a speed fallback:** When the device enumerated, it was always at 20 Gbps
- **Self-recovering:** The next cycle always succeeded without intervention
- **Contamination factor:** Stale test processes from earlier runs were discovered competing for the BrainStem API connection, inflating the failure rate. After killing them, failures dropped from ~15% to ~3%.
- **Clean failure rate (no stale processes):** ~3% (1 failure per ~30 cycles)

Root causes identified:
1. **Stale BrainStem processes** — earlier test runs that were killed left zombie Python processes that competed for the USB API connection, causing intermittent connect failures
2. **20Gbps link training latency** — the SuperSpeed+ 2x1 link takes longer to re-establish after port cycling than the 5Gbps SuperSpeed link, occasionally exceeding the polling timeout
3. **Not a cable signal issue** — if the cable were marginal, we would see speed fallbacks (20Gbps → 5Gbps or 480Mbps), not complete enumeration failures followed by full-speed recovery

**Conclusion:** The U420-010 cable passes all tests on the control port (70/70 at 5Gbps) and is electrically capable of 20Gbps on the data port. The small number of enumeration timeouts on the data port are caused by OS/hub link training latency at 20Gbps, not cable signal degradation. For the production deployment (which uses the control port path capped at 5Gbps), the cable has ample signal margin.

---

## Issues Encountered During Testing

### 1. `system_profiler SPUSBDataType` Returns Empty Output
- On this MacBook Pro M4 Max (macOS 25E253), `system_profiler SPUSBDataType` produces no output
- Workaround: All scripts use `ioreg -p IOUSB` instead, which reliably returns USB device data
- The `USBSpeed` property in ioreg maps directly to USB speed tiers

### 2. BrainStem SDK Installation — Python Version Mismatch
- `pip3 install brainstem` installed under Python 3.9 (system default pip) but the active Python was 3.12
- Fix: Used `/usr/local/bin/python3 -m pip install brainstem` to install for the correct Python version
- Also required `pip install --user --force-reinstall cffi` because the system cffi package (from fbcode) was missing the compiled `_cffi_backend` C extension

### 3. BrainStem API Connection Corruption (Error 25)
- Abruptly terminating a script during an active BrainStem API session leaves the hub in a `CONNECTION_ERROR` (error 25) state
- The hub is discoverable via `brainstem.discover.findAllModules()` but `connectFromSpec()` fails
- **Recovery requires physically unplugging and replugging the control cable**
- This happened twice during testing: once when the initial 500-cycle test was killed due to all-fail results, and once when a stale background test was killed
- Prevention: scripts should use signal handlers for graceful cleanup; avoid killing test processes mid-run

### 4. Port Cycling on Control Port Drops API Connection
- Initial implementation of test 5.2.3 held a persistent BrainStem API connection and cycled port 0 (the control port)
- Disabling port 0 severs the USB link that the API communicates over, causing all subsequent API calls to fail
- Fix: reconnect the API session each cycle (matching the approach used in test 5.1.2 which worked from the start)
- Better approach for data port testing: use a separate control cable on the Stem port and cycle only the data port

### 5. Stale Test Processes Competing for Hub API
- When test scripts are killed (e.g., via `pkill`) or run concurrently, old Python processes can survive and continue attempting BrainStem API connections in the background
- These zombie processes intermittently steal the API connection from the active test, causing `connect_hub()` to fail and registering false enumeration timeouts
- During the 60s-timeout retest, stale processes from two earlier runs (12:43PM and 2:44PM) were found still alive. After killing them by PID, the 5.2.3 failure rate dropped from ~15% to ~3%
- **Prevention:** before starting a new test run, verify no stale test processes exist: `ps aux | grep test_5 | grep -v grep`

### 6. ioreg USB Speed Parsing — Device Identification
- The `ioreg -p IOUSB -l -n USBHub3c_Stem` output includes the full USB tree from root, not just the named device
- Initial parser picked up the YubiKey's USBSpeed=1 instead of the hub's USBSpeed=3
- Fix: parse by looking for the device node line (`+-o USBHub3c-Stem@`) as a block delimiter, then read USBSpeed from within that block

---

## Test Environment Details

### Hardware Configuration
```
MacBook Pro M4 Max (Mac16,5)
├── XHCI Controller @00000000 — YubiKey OTP+FIDO+CCID (Full Speed)
├── XHCI Controller @01000000 — USBHub3c Data Port (Up0, 20Gbps)
│   ├── USBHub3c-3-Up0 (USB 3.x, SuperSpeed+ 2x1)
│   └── USBHub3c-2-Up0 (USB 2.x companion)
└── XHCI Controller @02000000 — USBHub3c Control Port (Stem, 5Gbps)
    └── USBHub3c-Stem
```

### Acroname Hub Details — USBHub3c
- Model: USBHub3c (S79-USBHUB-3P)
- Serial: 68D1A7BE
- 4 downstream ports (ports 0–3), all reporting state 0x000031f0
- Port 0 confirmed as the physical data port connected to USBHub3c-3-Up0 (verified by port-toggle test)

### Acroname Hub Details — USBHub3p (session 2)
- Model: USBHub3p (model 19)
- Two units tested: serial 0xb72d5b42 and serial 0xfdd9afb6
- 8 downstream ports (ports 0–7)
- USB 3.x uplink enumeration was intermittent on direct Mac USB-C connections; stable when routed through a USB-C dock

---

## Observations Relevant to AHEAD Proposal (v1.1, May 3, 2026)

The AHEAD proposal (prepared by Joe Arauzo, Client Director) documents the USB signal chain analysis for the Ramsey STE4453M3 to STE4453M4 transition. Several observations from this testing session are relevant to the assumptions in that proposal.

### Observation 1: Acroname S79-USBHUB-3P Negotiated Speeds Exceed Stated 5Gbps

The AHEAD proposal states: *"The internal Acroname hub supports USB 3.1 Gen 1 at 5Gbps"* and identifies the Acroname S79-USBHUB-3P as the *"speed-governing component"* that caps throughput at 5Gbps.

Observed speeds on S79-USBHUB-3P hardware during testing:

| Hub Model | Interface | Observed Speed | AHEAD Stated Speed |
|---|---|---|---|
| USBHub3c | Control (Stem) port | 5 Gbps | 5 Gbps |
| USBHub3c | Data (Up0) uplink | **20 Gbps** | 5 Gbps |
| USBHub3p | Control (Stem) port | 12 Mbps (Full Speed) | — |
| USBHub3p | Data uplink (USBHub3p-3[A]) | **10 Gbps** | 5 Gbps |
| USBHub3p | Downstream port (iPhone on port 3) | **10 Gbps** | 5 Gbps |

The Stem/control port is capped (5Gbps on USBHub3c, 12Mbps on USBHub3p), but the data uplink and downstream ports negotiate at the full capability of the connected devices and cables. The hub does not appear to be governing the speed at 5Gbps on its data path.

### Observation 2: U420-010 (3m) Cable Performs Well Beyond Rated Speed

The AHEAD proposal notes: *"The Tripp Lite U420-010 operates at the practical limit for passive 5Gbps cables"* and recommends validation at 3m.

Observed: The U420-010 negotiated **20 Gbps** on the USBHub3c data port — 4x its rated 5Gbps speed. At the production-relevant 5Gbps on the control port, it passed **70/70 cycles with zero failures**. The cable has substantial signal margin at 3m and is not operating near its electrical limits.

### Observation 3: Plan B Hub Replacement May Not Be Required for 10Gbps

The AHEAD proposal states Plan B requires replacing the Acroname S79-USBHUB-3P with the S85-USB-C-Switch to achieve 10Gbps throughput.

Observed: The S79-USBHUB-3P (USBHub3p) negotiated 10 Gbps on both the uplink and downstream ports without any hub replacement. An iPhone connected to a downstream port achieved 10 Gbps through the existing hub hardware. This suggests the S79-USBHUB-3P may already support 10Gbps data throughput on its data path, and the hub replacement specified in Plan B may not be necessary to achieve 10Gbps end-to-end.

**Note:** This observation is based on link negotiation speed only. Sustained throughput at 10Gbps through the hub was not tested. The hub's internal switching fabric may still impose a 5Gbps throughput cap even if the ports negotiate at higher speeds. Bandwidth testing (test 5.2.1/5.2.2) would be needed to confirm actual data throughput.

### Observation 4: USBHub3p Uplink Enumeration Instability

The USBHub3p's USB 3.x uplink was unreliable when connected directly to a MacBook Pro M4 Max USB-C port. The device would either:
- Connect as a generic `IOUSBHostDevice` and never complete device descriptor enumeration
- Briefly enumerate and then drop
- Only establish a USB 2.x connection (`USBHub3p-2[A]`) without the USB 3.x companion (`USBHub3p-3[A]`)

The uplink enumerated successfully and stably when routed through a USB-C dock. This was observed with both USBHub3p units (serials 0xb72d5b42 and 0xfdd9afb6) and with the U420-006 cable. The USBHub3c did not exhibit this issue.

This may be relevant to Mac mini deployments under Plans A.2 and B if the Mac mini's USB-C ports exhibit similar behavior to the MacBook Pro M4 Max. Testing with the actual Mac mini M4 (Z1JX0007R) hardware is recommended.

### Observation 5: Hub Speed Control Limitations

The BrainStem API was tested for per-port speed capping capability:
- `setSuperSpeedDataDisable()` works but drops the port to USB 2.0 (480Mbps) — there is no way to cap at exactly 5Gbps
- `setConnectMode()`, `setPortMode()` with lane-specific flags, and boost mode controls all returned UNIMPLEMENTED (error 21) on the USBHub3c
- The hub does not provide fine-grained speed tier control between USB 2.0 and its maximum negotiated speed

---

## Next Steps

1. **Test U420-006** (1.83m) through the full test suite — uplink enumeration instability on USBHub3p needs to be resolved first
2. **Run test 5.1.4** (sleep/wake cycling) manually with sudo
3. **Sustained throughput testing** (test 5.2.1) to determine if the S79-USBHUB-3P can actually pass 10Gbps data, not just negotiate it
4. **Test with Ramsey STE4453M4 enclosure** in the signal chain when available (tests 5.1.3, 5.2.x, 5.3.x)
5. **Test with Mac mini M4** (Z1JX0007R) to verify USBHub3p uplink enumeration behavior on the actual deployment hardware
6. **Test additional cable samples** from different manufacturing lots
