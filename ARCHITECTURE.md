# Plan A.2 Architecture — USB Signal Chain

**Reference:** AHEAD Proposal v1.1 (May 3, 2026), Plan A.2
**Scope:** Mac Mini M4 rack deployments with Ramsey STE4453M4 enclosures

---

## Overview

Plan A.2 eliminates the Apple USB-C to USB-A adapter from the Mac mini signal chain
and runs a USB-C to USB-C cable directly from the Mac mini's Thunderbolt 4 port to
the STE4453M4's USB-C I/O interface. The speed target is 5Gbps (USB 3.1 Gen 1).

---

## Signal Chain Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        RACK ASSEMBLY                                    │
│                                                                         │
│  ┌───────────────────────┐                                              │
│  │   SLIDING SERVICE     │                                              │
│  │   SHELF               │                                              │
│  │                       │                                              │
│  │  ┌─────────────────┐  │         USB-C to USB-C Cable                 │
│  │  │  Apple Mac Mini  │  │        (Tripp Lite U420-010)                 │
│  │  │  M4 (Z1JX0007R) │  │         3m / 5Gbps Passive                  │
│  │  │                  │  │                                              │
│  │  │  [TB4/USB-C]─────│──│────────────────┐                            │
│  │  │                  │  │                │                             │
│  │  └─────────────────┘  │                │                             │
│  │                       │                │                             │
│  │  ◄── shelf extends ──►│                │                             │
│  └───────────────────────┘                │                             │
│                                           │                             │
│                                           ▼                             │
│                              ┌────────────────────────┐                 │
│                              │  Ramsey STE4453M4       │                │
│                              │  RF Shielded Enclosure  │                │
│                              │                         │                │
│                              │  [USB-C I/O Interface]  │                │
│                              │   (rated 20Gbps)        │                │
│                              │         │               │                │
│                              │         ▼               │                │
│                              │  ┌─────────────────┐   │                │
│                              │  │ Acroname         │   │                │
│                              │  │ S79-USBHUB-3P   │   │                │
│                              │  │ (USB Hub)        │   │                │
│                              │  │                  │   │                │
│                              │  │  [Port 0]──►DUT  │   │                │
│                              │  │  [Port 1]──►DUT  │   │                │
│                              │  │  [Port 2]──►DUT  │   │                │
│                              │  │  [Port 3]──►...  │   │                │
│                              │  └─────────────────┘   │                │
│                              │                         │                │
│                              └────────────────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Speed Budget — What Limits What

```
Mac Mini M4          Cable              STE4453M4 I/O       Acroname Hub        DUT
Thunderbolt 4        U420-010           USB-C Interface      S79-USBHUB-3P
                     (passive)

 ┌──────────┐     ┌──────────┐       ┌──────────┐        ┌──────────┐     ┌──────────┐
 │          │     │          │       │          │        │          │     │          │
 │  40Gbps  │────►│  5Gbps   │──────►│  20Gbps  │───────►│  5Gbps*  │────►│  varies  │
 │ capable  │     │  rated   │       │  rated   │        │  rated   │     │          │
 │          │     │          │       │          │        │          │     │          │
 └──────────┘     └──────────┘       └──────────┘        └──────────┘     └──────────┘

                                                          * See Observation 1:
                                                            Hub data ports observed
                                                            negotiating 10-20Gbps
                                                            in testing

 Speed-governing component (per AHEAD proposal): Acroname Hub at 5Gbps
 Speed-governing component (observed):           Cable at 5Gbps rated
                                                 (though it negotiated 20Gbps
                                                  on the data port in testing)
```

---

## Cable Options by Position

```
                    ┌──────────────────────────────────────────────┐
                    │              MAC MINI RACK                    │
                    │                                              │
  SERVICE SHELF     │   ┌──────────┐                               │
  (extended)        │   │ Mac Mini │                               │
        ◄───3m────► │   │          │                               │
                    │   └────┬─────┘                               │
                    │        │                                     │
                    │        │ U420-010 (3.05m) ──── 3m position   │
                    │        │   or                                │
                    │        │ U420-006 (1.83m) ──── 2m position   │
                    │        │   or                                │
                    │        │ USB315CCV2M (2.0m) ── 2m position   │
                    │        │                       (preferred)    │
                    │        ▼                                     │
                    │   ┌──────────┐                               │
                    │   │STE4453M4 │                               │
                    │   │Enclosure │                               │
                    │   └──────────┘                               │
                    │                                              │
                    └──────────────────────────────────────────────┘

  Cable Selection:
  ┌────────────────────┬──────────────┬────────┬────────┬─────────────────┐
  │ Position           │ Cable        │ Length │ Speed  │ Notes           │
  ├────────────────────┼──────────────┼────────┼────────┼─────────────────┤
  │ 3m service shelf   │ U420-010     │ 3.05m  │ 5Gbps  │ Required        │
  │ 2m fixed (option 1)│ USB315CCV2M  │ 2.00m  │ 5Gbps  │ Preferred       │
  │ 2m fixed (option 2)│ U420-006     │ 1.83m  │ 5Gbps  │ Fit test needed │
  └────────────────────┴──────────────┴────────┴────────┴─────────────────┘
```

---

## What Changed from Current Setup

```
  CURRENT (STE4453M3)                    PLAN A.2 (STE4453M4)
  ────────────────────                   ───────────────────────

  Mac Mini M4                            Mac Mini M4
       │                                      │
  [USB-C port]                           [USB-C port]
       │                                      │
       ▼                                      │
  ┌──────────────┐                            │
  │ Apple USB-C  │  ◄── ELIMINATED            │
  │ to USB-A     │                            │
  │ Adapter      │                            │
  └──────┬───────┘                            │
         │                                    │
    [USB-A cable]                         [USB-C to USB-C cable]
    C2G 54171/54172                       U420-010 / U420-006
    (USB-A to USB-A)                      (USB-C to USB-C)
         │                                    │
         ▼                                    ▼
  ┌──────────────┐                     ┌──────────────┐
  │  STE4453M3   │                     │  STE4453M4   │
  │  USB-A I/O   │                     │  USB-C I/O   │
  │  (5Gbps)     │                     │  (20Gbps)    │
  └──────┬───────┘                     └──────┬───────┘
         │                                    │
         ▼                                    ▼
  ┌──────────────┐                     ┌──────────────┐
  │  Acroname    │                     │  Acroname    │
  │  S79-HUB-3P │  ◄── UNCHANGED ──►  │  S79-HUB-3P │
  │  (5Gbps)     │                     │  (5Gbps)     │
  └──────┬───────┘                     └──────┬───────┘
         │                                    │
         ▼                                    ▼
       DUT                                  DUT


  Changes:
    ✗ Apple USB-C to USB-A adapter — removed
    ✗ USB-A to USB-A cable — replaced
    ✗ STE4453M3 (USB-A, 5Gbps) — replaced
    ✓ Mac Mini M4 — unchanged
    ✓ Acroname hub — unchanged
    ✓ Operating speed — unchanged (5Gbps)

  Benefits:
    • One fewer component (adapter eliminated)
    • One fewer failure point during servicing
    • Direct USB-C to USB-C connection
    • STE4453M4 provides upgrade path to 10/20Gbps
```

---

## Rack View — Multiple Enclosures

```
  ┌─────────────────────────────────────────────────────────┐
  │                    RACK FRONT                            │
  │                                                         │
  │  ┌───────────────────────────────────────────────────┐  │
  │  │  Mac Mini Service Shelf (slides out for access)   │  │
  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
  │  │  │ Mac Mini │  │ Mac Mini │  │ Mac Mini │  ...   │  │
  │  │  │    #1    │  │    #2    │  │    #3    │        │  │
  │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘        │  │
  │  └───────│─────────────│─────────────│───────────────┘  │
  │          │             │             │                   │
  │     U420-010      U420-010      U420-006                │
  │     (3.05m)       (3.05m)       (1.83m)                 │
  │          │             │             │                   │
  │  ┌───────▼─────────────▼─────────────▼───────────────┐  │
  │  │                                                    │  │
  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
  │  │  │STE4453M4 │  │STE4453M4 │  │STE4453M4 │  ...  │  │
  │  │  │Enclosure │  │Enclosure │  │Enclosure │        │  │
  │  │  │  #1      │  │  #2      │  │  #3      │        │  │
  │  │  │ [Hub]    │  │ [Hub]    │  │ [Hub]    │        │  │
  │  │  │  └►DUT   │  │  └►DUT   │  │  └►DUT   │        │  │
  │  │  └──────────┘  └──────────┘  └──────────┘        │  │
  │  │                                                    │  │
  │  │  Adjacent equipment (switches, PDUs, other         │  │
  │  │  enclosures) generates EMI — cable shielding       │  │
  │  │  and routing are critical at 3m                    │  │
  │  └────────────────────────────────────────────────────┘  │
  │                                                         │
  └─────────────────────────────────────────────────────────┘

  Cable length determined by Mac Mini position relative to enclosure:
    • Far enclosures / shelf extended:  U420-010 (3.05m)
    • Near enclosures / shelf closed:   U420-006 (1.83m) or USB315CCV2M (2.0m)
```

---

## Test Validation Coverage

The following shows which parts of the Plan A.2 signal chain have been validated
by this test suite and which remain to be tested:

```
  Mac Mini M4       Cable           STE4453M4        Acroname Hub       DUT
  ───────────       ─────           ─────────        ────────────       ───

  [TB4/USB-C] ───► [U420-010] ───► [USB-C I/O] ───► [S79-HUB-3P] ───► [DUT]

                    ▲                                 ▲
                    │                                 │
               ✅ VALIDATED                      ✅ VALIDATED
               • 5Gbps: 70/70                    • API control works
               • 20Gbps capable                  • Port cycling stable
               • Signal margin                   • Data ports 10-20Gbps
                 confirmed                         capable


  ┌──────────────────────────────────────────────────────────────────────┐
  │ VALIDATED                                                           │
  │  ✅ 5.1.1 — Link speed (5Gbps on control, 20Gbps on data port)     │
  │  ✅ 5.1.2 — Connect/disconnect cycling (20/20 at 5Gbps)            │
  │  ✅ 5.2.3 — Stress cycling (50/50 at 5Gbps)                        │
  │                                                                     │
  │ NOT YET VALIDATED                                                   │
  │  ⬜ 5.1.3 — Cold boot negotiation                                  │
  │  ⬜ 5.1.4 — Sleep/wake cycling (script ready, requires sudo)       │
  │  ⬜ 5.2.1 — Baseline throughput measurement                        │
  │  ⬜ 5.2.2 — 72-hour soak test                                      │
  │  ⬜ 5.3.x — EMI resilience (requires production rack)              │
  │  ⬜ U420-006 cable validation                                       │
  │  ⬜ Full signal chain with STE4453M4 enclosure                      │
  │  ⬜ Mac mini M4 (Z1JX0007R) as host instead of MacBook Pro          │
  └──────────────────────────────────────────────────────────────────────┘
```
