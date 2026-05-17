# USB Throughput Test Guide

**Purpose:** Measure sustained data transfer rates through the USB signal chain to confirm
that link negotiation speeds (5/10/20 Gbps) translate to actual throughput.

**Prerequisite:** Complete the link negotiation tests (5.1.1, 5.1.2, 5.2.3) first.

---

## Equipment

- USB 3.0+ SSD or flash drive (the Netac Portable SSD 1TB was identified for this purpose)
- The same signal chain used for link testing:
  ```
  MacBook → U420-010 #1 → Ramsey STE4453M4 USB-C I/O → U420-010 #2 → Acroname USBHub3p → SSD on downstream port
  ```

---

## Step 1 — Format the Drive

The Netac SSD ships with a Linux filesystem. Reformat to ExFAT for macOS compatibility:

```bash
# Identify the drive
diskutil list external

# Reformat (replace disk4 with your actual disk identifier)
diskutil eraseDisk ExFAT NETAC_SSD /dev/disk4

# If permission denied:
sudo diskutil eraseDisk ExFAT NETAC_SSD /dev/disk4
```

Verify it mounted:
```bash
ls /Volumes/NETAC_SSD
```

---

## Step 2 — Confirm Drive Connection Speed

```bash
python3 test_5_1_1_link_speed.py netac_ssd_throughput --device data
```

Or manually:
```bash
ioreg -p IOUSB -l | grep -A5 "NetacPortableSSD" | grep USBSpeed
```

Expected: `USBSpeed = 3` (5 Gbps) or higher on the downstream port.

---

## Step 3 — Baseline Throughput (Test 5.2.1)

### Sequential Write
```bash
dd if=/dev/urandom of=/Volumes/NETAC_SSD/testfile bs=1M count=1024 2>&1 | tail -1
```
Records: write throughput in MB/s for 1 GB of random data.

### Sequential Read
```bash
# Purge disk cache first
sudo purge 2>/dev/null
dd if=/Volumes/NETAC_SSD/testfile of=/dev/null bs=1M 2>&1 | tail -1
```
Records: read throughput in MB/s.

### Repeat 3 Times
Run both read and write 3 times each, average the results.

**Expected range at 5 Gbps:** 200–400 MB/s (depending on SSD capability)
**Pass:** Throughput consistent across runs (±10%), no USB errors
**Fail:** Throughput significantly below device capability, or any USB bus reset

---

## Step 4 — Throughput with Integrity Check

Write random data, hash it, read it back, compare:

```bash
DEVICE_PATH="/Volumes/NETAC_SSD"

# Write 256MB random data
dd if=/dev/urandom of=${DEVICE_PATH}/testfile bs=1M count=256

# Hash after write
WRITE_HASH=$(shasum -a 256 ${DEVICE_PATH}/testfile | awk '{print $1}')

# Sync and purge cache
sync
sudo purge 2>/dev/null

# Read back and hash
READ_HASH=$(shasum -a 256 ${DEVICE_PATH}/testfile | awk '{print $1}')

# Compare
if [ "$WRITE_HASH" = "$READ_HASH" ]; then
    echo "PASS — checksums match"
else
    echo "FAIL — checksum mismatch (data corruption)"
fi

echo "Write hash: $WRITE_HASH"
echo "Read hash:  $READ_HASH"

# Cleanup
rm -f ${DEVICE_PATH}/testfile
```

---

## Step 5 — Extended Soak (Test 5.2.2)

For a 72-hour sustained transfer test, use the soak script:

```bash
# Edit DEVICE_PATH in the script first
python3 test_5_2_2_soak.py --device-path /Volumes/NETAC_SSD --hours 72
```

Or use the shell script from the test plan:
```bash
# u420_010_soak_test.sh (from the original test plan)
# Edit DEVICE_PATH="/Volumes/NETAC_SSD" at the top
bash u420_010_soak_test.sh
```

Monitor during soak (check every 8 hours):
```bash
tail -5 /tmp/u420_soak_*.log
ioreg -p IOUSB | grep -A3 "NetacPortableSSD"
```

**Pass criteria:**
- Zero checksum mismatches
- Zero USB bus resets
- Zero speed fallbacks
- Link remains at rated speed for the full duration
- Throughput degradation < 15% over the test period

---

## Step 6 — Log Results

Record results in a report file following the existing format:

```bash
mkdir -p reports/U420-010-ramsey-throughput/raw
# Copy result CSVs and logs to reports/U420-010-ramsey-throughput/raw/
# Create reports/U420-010-ramsey-throughput.md with findings
```

---

## Drive Details (Identified May 17, 2026)

| Property | Value |
|---|---|
| Device | Netac Portable SSD |
| Capacity | 1 TB |
| Serial | AA202308191T22163896 |
| Vendor ID | 3544 |
| Product ID | 8992 |
| Downstream speed | USBSpeed=3 (SuperSpeed, 5 Gbps) |
| Hub port | USBHub3p downstream port group [0-3] |
| Filesystem (original) | Linux (ext4) — requires reformatting |
| Filesystem (target) | ExFAT |

---

## Signal Chain for Throughput Testing

```
MacBook Pro M4 Max
  --> U420-010 #1 (3.05m)              Stem cable (separate)
    --> Ramsey STE4453M4 USB-C I/O       --> USBHub3p-Stem
      --> U420-010 #2 (3.05m)                (API control)
        --> Acroname USBHub3p
          --> [Port 0-3] --> Netac SSD   <-- throughput measured here
```

The throughput test measures actual data rates through the complete signal chain,
including both U420-010 cables, the Ramsey RF-filtered connector, and the hub's
downstream port. This is the end-to-end validation that link negotiation speed
translates to real-world data transfer capability.
