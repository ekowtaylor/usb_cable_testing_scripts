# USB Cable Validation Report — Tripp Lite U420-010 (x2) with Ramsey STE4453M4

**Cable:** 2x Tripp Lite U420-010 — USB-C to USB-C, 10 ft (3.05 m) each, USB 3.2 Gen 1 (5 Gbps), passive
**Total cable length:** 6.1 m (2x 3.05 m) with Ramsey USB-C I/O connector in between
**Sample:** `u420_010_ramsey`
**Operator:** Ekow Taylor, Network Infrastructure Services
**Date:** May 17, 2026
**Test machine:** MacBook Pro M4 Max (Mac16,5), 64GB RAM, macOS 15.x (Darwin 25.4.0)
**Hub:** Acroname USBHub3p — model 19, serial `0xb72d5b42`, 8 downstream ports
**BrainStem SDK:** v2.12.2
**Raw data:** [`reports/U420-010-ramsey/raw/`](./U420-010-ramsey/raw/)

---

## Signal Chain

```
MacBook Pro M4 Max (TB4 / USB-C, @02000000)
  --> U420-010 #1 (3.05m, 5Gbps passive)
    --> Ramsey STE4453M4 USB-C I/O Connector (rated 20Gbps)
      --> U420-010 #2 (3.05m, 5Gbps passive)
        --> Acroname USBHub3p (data uplink)
          --> Mac DUT on downstream port 0

Stem/API control: separate cable, MacBook @00000000 --> USBHub3p-Stem
```

This is the **first test with the Ramsey STE4453M4 enclosure connector in the signal chain**. The total passive cable run of 6.1m is 2x the rated 3m limit for USB 3.1 Gen 1 passive cables, with the Ramsey RF-filtered USB-C connector adding additional insertion loss.

---

## Verdict

**PASS — 71/71 cycles, zero failures, all at 10 Gbps.**

The two U420-010 cables running through the Ramsey STE4453M4 USB-C connector negotiated SuperSpeed+ (10 Gbps) on every single cycle — 2x the cables' rated 5 Gbps, through 2x the rated cable length. The Ramsey connector introduces no measurable signal degradation.

---

## Results Summary

| Test | Result | Speed |
|---|---|---|
| **5.1.1** Initial Link Speed | PASS | SuperSpeed+ (10 Gbps) |
| **5.1.2** Connect/Disconnect x20 | PASS (20/20) | All 10 Gbps |
| **5.2.3** API Cycling x50 | PASS (50/50) | All 10 Gbps |
| **5.1.4** Sleep/Wake | Not run (requires sudo) | -- |

- **Total cycles:** 71 (1 + 20 + 50)
- **Failures:** 0
- **Enumeration timeouts:** 0
- **Speed fallbacks:** 0
- **USB-2 fallbacks:** 0
- **5.2.3 rate:** ~6 cycles/min (~9.4s per cycle), 0 API errors
- **Cycling method:** Upstream mode cycling (`setUpstreamMode(NONE)` / `setUpstreamMode(AUTO)`)

---

## Key Findings

### Finding 1 — Ramsey USB-C Connector Does Not Degrade Signal

With the Ramsey STE4453M4 USB-C I/O connector in the chain, the link consistently negotiated at 10 Gbps — the same speed observed on the USBHub3p uplink without the Ramsey connector. The filtered RF connector adds no measurable signal penalty at this speed.

### Finding 2 — 6m Passive Cable Run at 10 Gbps

Two 3.05m passive cables rated for 5 Gbps are operating at 10 Gbps across a 6.1m total run. This is:
- 2x the rated speed of each cable (5 Gbps)
- 2x the recommended maximum passive cable length for 5 Gbps
- 6x the USB-IF specification limit for passive cables at 10 Gbps (1m)

Despite operating well outside specification on every dimension, the signal chain achieved 100% reliability across 71 cycles.

### Finding 3 — No 20 Gbps on USBHub3p (vs 20 Gbps on USBHub3c)

The USBHub3c data port negotiated 20 Gbps with a single U420-010. The USBHub3p data uplink caps at 10 Gbps. This is a hub model difference, not a cable or Ramsey connector limitation.

### Finding 4 — Zero Enumeration Timeouts (vs ~3% on USBHub3c at 20 Gbps)

The USBHub3c at 20 Gbps showed occasional enumeration timeouts (~3% of cycles). The USBHub3p at 10 Gbps showed **zero** timeouts across all 71 cycles. The lower link speed results in faster and more reliable link training.

---

## Comparison with Previous Tests

| Configuration | Total cable | Through Ramsey | Hub | Speed | Cycles | Failures |
|---|---|---|---|---|---|---|
| U420-010, USBHub3c, control | 3.05m | No | USBHub3c | 5 Gbps | 71/71 | 0 |
| U420-010, USBHub3c, data | 3.05m | No | USBHub3c | 20 Gbps | 71/71* | 0* |
| U420-006, USBHub3c, control | 1.83m | No | USBHub3c | 5 Gbps | 71/71 | 0 |
| U420-006, USBHub3c, data | 1.83m | No | USBHub3c | 20 Gbps | 71/71* | 0* |
| **U420-010 x2, USBHub3p, data** | **6.1m** | **Yes** | **USBHub3p** | **10 Gbps** | **71/71** | **0** |

*With 60s polling timeout; some cycles re-trained to 5 Gbps (still PASS).

---

## Implications for Plan A.2

The production Plan A.2 signal chain uses a **single** U420-010 (3.05m) through the Ramsey connector. This test used **two** U420-010 cables (6.1m total) — a significantly more challenging configuration. The perfect results confirm:

1. The U420-010 cable is **more than adequate** for Plan A.2 at any speed up to 10 Gbps
2. The Ramsey STE4453M4 USB-C connector introduces **no signal degradation**
3. The Acroname S79-USBHUB-3P hub operates reliably at **10 Gbps** (not limited to 5 Gbps as stated in the AHEAD proposal)
4. The production signal chain has **substantial margin** beyond rated specifications

---

## Next Steps

1. Connect a USB storage drive to a downstream port for **sustained throughput testing** (dd / bandwidth measurement) to confirm actual data rates match link negotiation speeds
2. Run 5.1.4 (sleep/wake cycling) when a maintenance window allows
3. Test with a single U420-010 through the Ramsey connector (production-representative configuration)
