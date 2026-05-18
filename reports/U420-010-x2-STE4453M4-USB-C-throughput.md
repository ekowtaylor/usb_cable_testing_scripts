# USB Throughput Report — U420-010 (x2) through Ramsey STE4453M4 → USBHub3p → Netac SSD

**Objective:** Confirm that the SuperSpeed link negotiation seen in the prior tests (report `U420-010-x2-STE4453M4-USB-C.md`) translates into actual sustained data throughput to a downstream storage device.
**Sample:** `u420_010_ramsey`
**Operator:** Ekow Taylor, Network Infrastructure Services
**Date:** May 18, 2026
**Test machine:** MacBook Pro M4 Max
**Hub:** Acroname USBHub3p — model 19, serial `0xb72d5b42`, 8 downstream ports
**BrainStem SDK:** v2.12.2
**Drive:** Netac Portable SSD 1 TB, `/dev/disk4`, ExFAT `NETAC_SSD`
**Raw data:** [`./U420-010-x2-STE4453M4-USB-C-throughput/raw/throughput.txt`](./U420-010-x2-STE4453M4-USB-C-throughput/raw/throughput.txt)

---

## Signal Chain

```
MacBook Pro M4 Max
  --> U420-010 #1 (3.05m)
    --> Ramsey STE4453M4 USB-C I/O Connector
      --> U420-010 #2 (3.05m)
        --> Acroname USBHub3p (data uplink — enumerates SuperSpeed 5 Gbps to host)
          --> port 0 --> Netac Portable SSD 1TB   <-- throughput measured here

Stem/API control: separate cable, MacBook --> USBHub3p-Stem
```

---

## Verdict

**THROUGHPUT: FAIL — drive runs at USB 2.0 (480 Mbps), not SuperSpeed.**
**DATA INTEGRITY: PASS — 256 MB, sha256 match, zero corruption.**

The signal chain transfers data **reliably and without corruption**, but the downstream
SSD links at **USB 2.0 High-Speed (480 Mbps)**, capping real throughput at **~34 MB/s
write / ~39 MB/s read** — roughly **10× below** the 200–400 MB/s expected of this drive at
SuperSpeed 5 Gbps.

> The failure is localized to the **last hop only** (USBHub3p port 0 → SSD). The hub's
> own SuperSpeed uplink negotiates 5 Gbps to the host through the full 6.1 m
> U420-010 + Ramsey chain (`USBHub3p-3[A]` enumerated at 5 Gbps). **This result does
> not implicate the U420-010 cables or the Ramsey connector** — it points at the short
> local connection between the hub port and the SSD.

---

## Results

| Run | Write | Read |
|---|---|---|
| 1 | 34.0 MB/s | 39.1 MB/s |
| 2 | 33.4 MB/s | 38.5 MB/s |
| 3 | 33.2 MB/s | 38.5 MB/s |
| **Mean** | **33.5 MB/s** | **38.7 MB/s** |

- Run-to-run variance < 3% (pass criterion ±10%) — the link is *stable*, just slow.
- Integrity: 256 MB random, write/read sha256 **identical** → no corruption.
- Source ruled out: `/dev/urandom` sustains 305 MB/s and `/dev/zero` writes measured
  37.9 MB/s, so the ~35 MB/s ceiling is the USB link, not the data source.

---

## Root-Cause Evidence

1. **`ioreg`** — `NetacPortableSSD` is parented under **`USBHub3p-2[0-3]`** (the 480 Mbps
   USB 2.0 companion), never under `USBHub3p-3` (the SuperSpeed 5 Gbps interface).
   The device-node `"USBSpeed" = 3` property is misleading — it reflects the node, not
   the parent bus the device is actually attached to.
2. **`system_profiler`** — reports the SSD under the `HS-480Mbps` hub interface.
3. **Hub API** — `usb.getDownstreamDataSpeed(0)` returns **`1` (High Speed / USB 2.0)**.
4. **Not an error/power condition** — `getPortError(0) = 0x0`, current ~105 mA.
   After `clearPortErrorStatus` + `setSuperSpeedDataEnable` + a clean port power-cycle,
   the downstream speed **stays USB 2.0**. The SuperSpeed link to the device simply
   never trains.
5. **Recovery note** — on connect the SSD did not enumerate on the host at all
   (powered, ~103 mA, no host node). It only appeared after an Acroname API port-0
   power-cycle — and then only on the USB 2.0 path.

---

## Most Likely Causes (in order)

1. **The short cable between USBHub3p port 0 and the Netac SSD is USB 2.0-only or
   faulty.** Most common cause — many USB-C/USB-A cables wire only the USB 2.0 pairs.
2. **Hub downstream port 0 SuperSpeed lanes** degraded or disabled at the hardware level.
3. **The Netac SSD itself** defaulting to / stuck at USB 2.0.

The U420-010 cables and the Ramsey STE4453M4 connector are **not** implicated: the hub's
own SuperSpeed uplink crosses the entire 6.1 m chain at 5 Gbps.

---

## Recommended Next Steps (decisive bench tests)

1. **Swap the SSD's short cable** for a known SuperSpeed (USB 3.x) cable, replug,
   re-check `getDownstreamDataSpeed(0)`. (Cheapest, most likely fix.)
2. **Try a different downstream port** (e.g., port 4) with the same drive.
3. **Plug the SSD directly into the hub with the hub directly on the Mac** (bypass both
   U420-010 cables and the Ramsey connector): if it comes up SuperSpeed, the chain’s
   last hop hardware is fine and the issue is local; if it stays USB 2.0, it is the
   SSD or its cable.
4. Re-run this throughput test once the drive enumerates on `USBHub3p-3` (SuperSpeed).
   The expected pass band is 200–400 MB/s.

---

## Relation to Prior Findings

The prior report (`U420-010-x2-STE4453M4-USB-C.md`, 71/71 PASS at 5/10 Gbps) measured
the **hub uplink link negotiation**, which remains valid — the chain carries SuperSpeed
to the hub. This is the first test to push real data to a **downstream device**, and it
adds an important caveat: a SuperSpeed *link negotiation* on the hub does not by itself
guarantee a SuperSpeed *downstream device path*. The two must be validated separately.
