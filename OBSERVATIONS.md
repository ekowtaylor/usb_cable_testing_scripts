# Testing Observations & Notes

**Date:** May 15, 2026
**Author:** Ekow Taylor, Network Infrastructure Services
**Reference:** AHEAD Proposal v1.1 (May 3, 2026), prepared by Joe Arauzo, Client Director

This document captures observations from hands-on cable validation testing that are
relevant to the AHEAD USB Signal Chain Analysis and the Ramsey STE4453M3 to
STE4453M4 transition. These are empirical findings, not conclusions — further testing
is recommended where noted.

---

## 1. Acroname S79-USBHUB-3P Negotiates Above 5Gbps

**AHEAD proposal states:** *"The internal Acroname hub supports USB 3.1 Gen 1 at 5Gbps"*
and identifies it as the *"speed-governing component"* capping throughput at 5Gbps.

**Observed:** The hub's data ports negotiate well above 5Gbps. Only the control (Stem)
port is speed-limited.

| Hub Model | Interface | Observed Speed |
|---|---|---|
| USBHub3c (serial 68D1A7BE) | Control (Stem) | 5 Gbps |
| USBHub3c (serial 68D1A7BE) | Data uplink (Up0) | **20 Gbps** |
| USBHub3p (serial 0xb72d5b42) | Control (Stem) | 12 Mbps |
| USBHub3p (serial 0xb72d5b42) | Data uplink (3[A]) | **10 Gbps** |
| USBHub3p (serial 0xb72d5b42) | Downstream port (iPhone) | **10 Gbps** |
| USBHub3p (serial 0xfdd9afb6) | Data uplink (3[A]) | **10 Gbps** |

**Caveat:** These are link negotiation speeds. The hub's internal switching fabric may
still impose a lower throughput ceiling. Sustained bandwidth testing (dd, iperf, or
similar) is required to confirm actual data throughput rates through the hub.

**Implication:** If sustained throughput matches negotiation speed, the S79-USBHUB-3P
is not the 5Gbps bottleneck described in the proposal.

---

## 2. U420-010 (3m Cable) Has Significant Signal Margin

**AHEAD proposal states:** *"The Tripp Lite U420-010 operates at the practical limit for
passive 5Gbps cables"* and recommends validation at 3m given EMI conditions in
dense rack environments.

**Observed:**
- On USBHub3c control port (5Gbps): **70/70 cycles, zero failures** across tests
  5.1.1, 5.1.2 (20 cycles), and 5.2.3 (50 cycles)
- On USBHub3c data port: negotiated **20 Gbps** — 4x the cable's rated speed
- No speed fallbacks observed on any test cycle
- The cable is not operating near its electrical limits at 3m

**Implication:** The U420-010 is well-qualified for Plan A.2 deployments at 5Gbps.
The 3m length is not a concern for signal integrity at the production speed.

---

## 3. Plan B Hub Replacement May Not Be Required

**AHEAD proposal states:** Plan B requires replacing the S79-USBHUB-3P with the
Acroname S85-USB-C-Switch to achieve 10Gbps throughput.

**Observed:** The S79-USBHUB-3P (USBHub3p model) negotiated 10 Gbps on both
the uplink and downstream ports without any hub replacement. An iPhone connected
to a downstream port achieved 10 Gbps through the existing hub.

**Caveat:** Link negotiation speed does not guarantee sustained throughput at 10Gbps.
The hub's internal architecture may still limit actual data transfer rates. This must be
verified with bandwidth testing before concluding that the hub swap is unnecessary.

**If confirmed:** This would significantly reduce Plan B's component changes and cost
— eliminating the hub replacement from the bill of materials.

---

## 4. USBHub3p Uplink Enumeration Instability on Direct Mac Connections

**Observed:** The USBHub3p's USB 3.x uplink was unreliable when connected directly
to a MacBook Pro M4 Max USB-C port. Behaviors included:

- Device connects as generic `IOUSBHostDevice` and never completes enumeration
- Brief enumeration followed by immediate disconnect
- Only USB 2.x interface (`USBHub3p-2[A]`) establishes, no USB 3.x (`USBHub3p-3[A]`)
- Repeated plug/unplug cycles produce inconsistent results

This was observed on:
- Two separate USBHub3p units (serials 0xb72d5b42 and 0xfdd9afb6)
- Multiple XHCI controllers on the same Mac (@01000000 and @02000000)
- With the U420-006 cable

**Workaround:** Routing the uplink through a USB-C dock resolved the issue — the
hub enumerated fully and stably at 10 Gbps.

**The USBHub3c did not exhibit this issue** — it enumerated reliably on direct Mac
connections every time.

**Implication for deployments:** If Mac mini M4 USB-C ports behave similarly to the
MacBook Pro M4 Max, direct USBHub3p connections under Plans A.2 and B could
be affected. Testing with the actual Mac mini M4 (Z1JX0007R) is recommended
before volume deployment.

---

## 5. Hub Control (Stem) Port vs Data Port — Critical Distinction

**Not addressed in AHEAD proposal.** The Acroname hub exposes two distinct USB
interfaces to the host, each with different speed capabilities:

| Interface | Purpose | USBHub3c Speed | USBHub3p Speed |
|---|---|---|---|
| Control (Stem) | BrainStem API management | 5 Gbps | 12 Mbps |
| Data (uplink) | DUT data path | 20 Gbps | 10 Gbps |

The control port is severely speed-limited compared to the data port. The production
signal chain connects through the data uplink, not the Stem, so the Stem speed is
not operationally relevant — but it does mean that speed measurements taken via the
Stem port will underreport the hub's actual data path capability.

---

## 6. No Fine-Grained Speed Control via BrainStem API

**Observed:** The Acroname BrainStem API does not support capping a port at a
specific speed tier (e.g., limiting to 5Gbps while the hardware can negotiate 10 or
20Gbps).

| API Method | Result |
|---|---|
| `setSuperSpeedDataDisable()` | Drops to USB 2.0 (480Mbps) — no 5Gbps option |
| `setSuperSpeedDataEnable()` | Enables full speed (10 or 20Gbps depending on hub) |
| `setConnectMode()` | UNIMPLEMENTED (error 21) |
| `setPortMode()` with lane flags | UNIMPLEMENTED (error 21) |
| Boost mode controls | UNIMPLEMENTED (error 21) |

**Implication:** Speed-controlled testing (e.g., validating behavior at exactly 5Gbps on
the data port) is not possible through the API. The control (Stem) port happens to be
capped at 5Gbps on the USBHub3c, which served as a natural 5Gbps test point for
the U420-010 validation.

---

## 7. macOS `system_profiler SPUSBDataType` Returns Empty Output

**Observed:** On the MacBook Pro M4 Max (macOS 15.x, build 25E253),
`system_profiler SPUSBDataType` produces no output. This is the standard macOS
tool for inspecting USB devices.

**Workaround:** All scripts use `ioreg -p IOUSB -l` instead, which reliably returns
USB device data including the `USBSpeed` property that maps to USB speed tiers.

**Implication for other teams:** Any automated tooling that relies on
`system_profiler SPUSBDataType` for USB device detection may need to be updated
to use `ioreg` on M4 Max hardware.

---

## 8. BrainStem API Session Corruption

**Observed:** Abruptly terminating a Python script during an active BrainStem API
session (via kill, Ctrl+C, or process crash) leaves the hub in a `CONNECTION_ERROR`
(error code 25) state. The hub remains discoverable via `brainstem.discover.findAllModules()`
but `connectFromSpec()` fails.

**Recovery:** Requires physically unplugging and replugging the control (Stem) cable.
No software-only recovery was found.

**Occurred:** Twice during this testing session — once when a failing 500-cycle test
was killed, and once when a stale background process was terminated.

**Implication:** Test scripts and automation should implement signal handlers for
graceful BrainStem session cleanup. Running multiple test scripts simultaneously
against the same hub should be avoided — stale processes competing for the API
connection caused inflated failure rates during testing.

---

## Summary Table

| # | Observation | Impact | Action Needed |
|---|---|---|---|
| 1 | Hub data ports negotiate 10-20Gbps | Challenges "5Gbps cap" assumption | Sustained throughput testing |
| 2 | U420-010 passes all tests at 5Gbps, negotiates 20Gbps | Cable qualified for Plan A.2 | None — validated |
| 3 | Existing hub may support 10Gbps | Could simplify Plan B | Bandwidth testing to confirm |
| 4 | USBHub3p uplink unstable on direct Mac connections | Risk for Mac mini deployments | Test on Mac mini M4 hardware |
| 5 | Stem vs data port speed difference | Speed measurements depend on port | Document in test procedures |
| 6 | No API speed capping | Can't force 5Gbps on data port | Use Stem port for 5Gbps testing |
| 7 | system_profiler broken on M4 Max | Tooling may need updates | Use ioreg instead |
| 8 | BrainStem session corruption on kill | Hub requires physical replug | Add signal handlers to scripts |
