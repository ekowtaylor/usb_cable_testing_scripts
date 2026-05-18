# Resume Notes — USB Cable Validation Testing

**Last session:** May 17, 2026
**Next machine:** Continue on a machine with USB write access (sudo/diskutil)

---

## What's Been Completed

### Link Negotiation Tests (all passed)

| Report | Cable | Signal Chain | Hub | Speed | Result |
|---|---|---|---|---|---|
| `reports/U420-010.md` | U420-010 (3m) | Direct to hub | USBHub3c | 5/20 Gbps | 71/71 PASS |
| `reports/U420-006.md` | U420-006 (1.83m) | Direct to hub | USBHub3c | 5/20 Gbps | 71/71 PASS |
| `reports/U420-010-x2-STE4453M4-USB-C.md` | 2x U420-010 (6.1m) | Through Ramsey STE4453M4 USB-C connector | USBHub3p | 10 Gbps | 71/71 PASS |

### Documentation

| File | Contents |
|---|---|
| `OBSERVATIONS.md` | 8 observations from testing |
| `AHEAD_COMPARISON.md` | Point-by-point comparison with AHEAD proposal v1.1 |
| `ARCHITECTURE.md` | Plan A.2 signal chain diagrams (ASCII) |
| `plan_a2_architecture.png` | Plan A.2 visual diagram (PNG) |
| `TESTING_LOG.md` | Detailed session log with all findings and issues |
| `THROUGHPUT_TEST_GUIDE.md` | Step-by-step instructions for the disk throughput test |

---

## What's Next — Disk Throughput Test

### Goal
Confirm that link negotiation speeds (5/10 Gbps) translate to actual sustained
data transfer throughput through the hub.

### Setup Required
```
MacBook (with sudo/diskutil access)
  → U420-010 #1 (3.05m)
    → Ramsey STE4453M4 USB-C I/O connector
      → U420-010 #2 (3.05m)
        → Acroname USBHub3p
          → Netac Portable SSD (1TB) on downstream port
```

Stem/API control: separate cable to USBHub3p-Stem port.

### Steps to Resume

1. **Clone the repo** (if on a new machine):
   ```bash
   git clone https://github.com/ekowtaylor/usb_cable_testing_scripts.git
   cd usb_cable_testing_scripts
   pip3 install brainstem
   ```

2. **Connect the hardware** as described above

3. **Verify the hub and drive are visible:**
   ```bash
   python3 test_5_1_1_link_speed.py throughput_test --device data
   ioreg -p IOUSB | grep -i netac
   ```

4. **Format the Netac SSD** (requires sudo):
   ```bash
   diskutil list external
   sudo diskutil eraseDisk ExFAT NETAC_SSD /dev/diskN  # replace N
   ```

5. **Run the throughput tests** (see `THROUGHPUT_TEST_GUIDE.md` for full details):
   ```bash
   # Sequential write (1GB)
   dd if=/dev/urandom of=/Volumes/NETAC_SSD/testfile bs=1M count=1024

   # Sequential read
   sudo purge
   dd if=/Volumes/NETAC_SSD/testfile of=/dev/null bs=1M

   # Integrity check
   dd if=/dev/urandom of=/Volumes/NETAC_SSD/testfile bs=1M count=256
   WRITE_HASH=$(shasum -a 256 /Volumes/NETAC_SSD/testfile | awk '{print $1}')
   sync && sudo purge
   READ_HASH=$(shasum -a 256 /Volumes/NETAC_SSD/testfile | awk '{print $1}')
   echo "Write: $WRITE_HASH"
   echo "Read:  $READ_HASH"
   ```

6. **Save results** to `reports/U420-010-x2-STE4453M4-USB-C-throughput/`

### Drive Details
| Property | Value |
|---|---|
| Device | Netac Portable SSD |
| Capacity | 1 TB |
| Serial | AA202308191T22163896 |
| Original filesystem | Linux (ext4) — needs reformatting to ExFAT |
| Downstream speed | USBSpeed=3 (SuperSpeed, 5 Gbps) |

---

## Other Pending Tests

| Test | Status | Notes |
|---|---|---|
| 5.1.4 Sleep/Wake cycling | Not run | Requires sudo, will sleep the Mac |
| 5.2.2 72-hour soak | Not run | Requires formatted drive + 72 hours |
| 5.3.x EMI resilience | Not run | Requires production rack environment |
| Single U420-010 through Ramsey | Not run | Production-representative config (vs 2x cable tested) |
| Mac Mini M4 (Z1JX0007R) testing | Not run | USBHub3p had enumeration issues on MacBook Pro — verify on Mac Mini |
| Additional cable samples | Not run | Different manufacturing lots recommended |
