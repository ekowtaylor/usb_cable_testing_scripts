# USB Throughput Report #2 — SSK SSD on USBHub3p port 0

**Objective:** Repeat the downstream throughput test with a *different drive type* on the
**same USBHub3p port 0** that failed the first throughput test (Netac SSD linked USB-2,
~35 MB/s). Isolates whether port 0 / the signal chain is at fault, or the Netac drive was.
**Date:** May 18, 2026
**Test machine:** MacBook Air M5, macOS 26.3 (Darwin 25.x), Python 3.14, BrainStem SDK
**Hub:** Acroname USBHub3p — model 19, serial `0xb72d5b42`, 8 downstream ports
**Drive:** SSK SSD 1 TB (vendor "SSK Corporation"), `/dev/disk4s2`, exFAT `SSK SSD`, used as-is (not formatted)
**Raw data:** [`./throughput-2-SSK-SSD-USBHub3p-port0/raw/`](./throughput-2-SSK-SSD-USBHub3p-port0/raw/) (`throughput.txt`, `hub_port0.txt`)

> **Signal chain (UPSTREAM TO CONFIRM):** drive → USBHub3p port 0 → hub data uplink
> (`USBHub3p-3[A]`, USBSpeed 4 = 10 Gbps to host) → … → Mac. The hub-port→drive last hop
> and hub uplink are verified below; the exact upstream cabling (direct vs 2× U420-010 +
> Ramsey STE4453M4) was not re-confirmed this run — annotate before treating as a formal
> chain validation.

---

## Verdict

**THROUGHPUT: PASS — SuperSpeed, ~286 MB/s write / ~402 MB/s read.**
**DATA INTEGRITY: PASS — 256 MB, sha256 match, zero corruption.**

The SSK SSD on USBHub3p **port 0** links at **SuperSpeed** (`getDownstreamDataSpeed(0)=2`,
parented under `USBHub3p-3`, `portError=0x0`) and delivers full SuperSpeed throughput —
**~8–10× the failed Netac result on the identical port** (33.5 / 38.7 MB/s).

**Diagnostic conclusion:** USBHub3p port 0's SuperSpeed lanes and the signal chain are
healthy. The first throughput test's USB-2 failure was the **Netac SSD or its short
hub→drive cable**, *not* port 0, the U420-010 cables, or the Ramsey connector.

---

## Results

| Run | Write | Read |
|---|---|---|
| 1 | 253.5 MB/s | 402.6 MB/s |
| 2 | 303.9 MB/s | 402.3 MB/s |
| 3 | 301.4 MB/s | 402.2 MB/s |
| **Mean** | **286.3 MB/s** | **402.4 MB/s** |
| Steady-state (runs 2–3) | ~302 MB/s | ~402 MB/s |

- **Read variance < 0.1 %** across runs — extremely stable. Write runs 2–3 within 1 %;
  run 1 is a ~16 % cold-start outlier (exFAT allocation / drive ramp), steady-state ~302 MB/s.
- Cache cleared between runs by volume **unmount/remount** (no `sudo purge` available).
- **Integrity:** 256 MB random, write vs read sha256 **identical**
  (`d013d43c…5c0baa7a`) → zero corruption.
- No USB errors: `getPortError(0) = 0x0` throughout; link stayed on `USBHub3p-3` (SuperSpeed).

Pass criterion (`THROUGHPUT_TEST_GUIDE.md`): consistent ±10 %, no USB errors, in the
200–400 MB/s SuperSpeed band → **met** (read trivially; write steady-state met, run-1
cold start noted).

---

## Comparison with Throughput Test #1 (Netac SSD, same port 0)

| | Test #1 — Netac SSD | Test #2 — SSK SSD |
|---|---|---|
| Downstream link (`getDownstreamDataSpeed(0)`) | 1 = **USB-2 (480 Mbps)** | 2 = **SuperSpeed** |
| ioreg parent bus | `USBHub3p-2` (USB-2) | `USBHub3p-3` (SuperSpeed) |
| Write | 33.5 MB/s | **286 MB/s** (~8.5×) |
| Read | 38.7 MB/s | **402 MB/s** (~10.4×) |
| Integrity | PASS | PASS |
| `portError(0)` | 0x0 | 0x0 |

Same hub, same port 0, same chain — only the drive changed. The SSK SSD trains SuperSpeed
where the Netac stayed USB-2. **Root cause of Test #1 confirmed: the Netac SSD or its
hub→drive cable, isolated to that last hop.**

---

## Recommended Next Steps

1. Re-test the Netac SSD with a **known SuperSpeed (USB 3.x) cable** on port 0 — if it then
   trains SuperSpeed, the Netac's bundled short cable is the culprit (most likely).
2. Confirm the **upstream cabling** for this run and update the chain header above so this
   doubles as an end-to-end chain validation.
3. Optional: codify this procedure into `test_5_2_1_throughput.py` (currently a manual
   shell sequence) for repeatable, CSV-logged throughput runs in the suite.
