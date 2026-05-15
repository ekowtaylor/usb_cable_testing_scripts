#!/usr/bin/env python3
"""Shared utilities for USB cable validation tests."""

import subprocess
import csv
import os
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

USB_SPEED_MAP = {
    0: ("Low Speed", "1.5 Mbps"),
    1: ("Full Speed", "12 Mbps"),
    2: ("High Speed", "480 Mbps"),
    3: ("SuperSpeed", "5 Gbps"),
    4: ("SuperSpeed+", "10 Gbps"),
    5: ("SuperSpeed+ 2x1", "20 Gbps"),
}

ACRONAME_SERIAL = "68D1A7BE"

# Device names by connection type
DEVICE_CONTROL = "USBHub3c_Stem"
DEVICE_DATA = "USBHub3c-3-Up0"
IOREG_NODE_CONTROL = "USBHub3c-Stem@"
IOREG_NODE_DATA = "USBHub3c-3-Up0@"


def get_usb_speed(device="control"):
    """Query ioreg for Acroname hub USB speed.

    Args:
        device: "control" for Stem port, "data" for data port (Up0)

    Returns: (speed_code, speed_label, raw_output)
    """
    if device == "data":
        product_name = DEVICE_DATA
        node_marker = IOREG_NODE_DATA
    else:
        product_name = DEVICE_CONTROL
        node_marker = IOREG_NODE_CONTROL

    try:
        result = subprocess.run(
            ["ioreg", "-p", "IOUSB", "-l"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        usb_speed = None
        in_block = False
        for line in output.splitlines():
            if node_marker in line:
                in_block = True
                continue
            if in_block and '"USBSpeed"' in line:
                parts = line.strip().split("=")
                if len(parts) == 2:
                    usb_speed = int(parts[1].strip())
                    break

        if usb_speed is not None:
            label, rate = USB_SPEED_MAP.get(usb_speed, ("Unknown", "Unknown"))
            return usb_speed, f"{label} ({rate})", output
        return None, "Device not found", output
    except Exception as e:
        return None, f"Error: {e}", ""


def check_hub_enumerated(device="control"):
    """Check if the Acroname hub is enumerated. Returns bool."""
    target = DEVICE_DATA if device == "data" else DEVICE_CONTROL
    try:
        result = subprocess.run(
            ["ioreg", "-p", "IOUSB"],
            capture_output=True, text=True, timeout=10
        )
        return target in result.stdout
    except Exception:
        return False


def log_result(test_id, cycle, status, speed_code, speed_label, notes=""):
    """Append a result row to the test CSV log."""
    log_file = os.path.join(RESULTS_DIR, f"{test_id}.csv")
    file_exists = os.path.exists(log_file)
    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "cycle", "status", "speed_code", "speed_label", "notes"])
        writer.writerow([
            datetime.now().isoformat(),
            cycle,
            status,
            speed_code,
            speed_label,
            notes,
        ])


def print_summary(test_id, test_name, total, passed, failed):
    """Print a formatted test summary."""
    result = "PASS" if failed == 0 else "FAIL"
    print(f"\n{'='*60}")
    print(f"  {test_name}")
    print(f"  Result: {result}")
    print(f"  Passed: {passed}/{total}  |  Failed: {failed}/{total}")
    log_file = os.path.join(RESULTS_DIR, f"{test_id}.csv")
    print(f"  Log: {log_file}")
    print(f"{'='*60}")
