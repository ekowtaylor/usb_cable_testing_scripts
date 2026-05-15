#!/usr/bin/env python3
"""Test 5.1.4 — Sleep/Wake Cycling

Puts the MacBook to sleep via pmset, wakes it, and verifies
the USB link re-establishes at 5Gbps.

IMPORTANT: This script must be run with sudo (pmset requires root).
It uses caffeinate to schedule the wake before sleeping.

Pass: All wake cycles restore 5Gbps within 60 seconds
Fail: Any wake results in fallback, no enumeration, or recovery > 60s
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from usb_utils import get_usb_speed, check_hub_enumerated, log_result, print_summary

TEST_ID = "5_1_4_sleep_wake"
TEST_NAME = "Test 5.1.4 — Sleep/Wake Cycling"
TOTAL_CYCLES = 10
SLEEP_DURATION = 30
MAX_RECOVERY_WAIT = 60
SAMPLE_LABEL = sys.argv[1] if len(sys.argv) > 1 else "sample_1"


def schedule_wake_and_sleep():
    """Schedule a wake in SLEEP_DURATION seconds, then put the Mac to sleep."""
    wake_time = int(time.time()) + SLEEP_DURATION
    # Schedule a wake using pmset schedule
    # Format: MM/DD/YYYY HH:MM:SS
    from datetime import datetime, timedelta
    wake_dt = datetime.now() + timedelta(seconds=SLEEP_DURATION)
    wake_str = wake_dt.strftime("%m/%d/%Y %H:%M:%S")

    print(f"    Scheduling wake at {wake_str}")
    subprocess.run(
        ["sudo", "pmset", "schedule", "wake", wake_str],
        capture_output=True, text=True
    )

    print(f"    Putting Mac to sleep...")
    subprocess.run(["pmset", "sleepnow"], capture_output=True, text=True)


def wait_for_hub(timeout):
    """Poll for hub enumeration up to timeout seconds. Returns time taken or -1."""
    start = time.time()
    while time.time() - start < timeout:
        if check_hub_enumerated():
            return time.time() - start
        time.sleep(2)
    return -1


def main():
    # Check for root privileges
    if os.geteuid() != 0:
        print("ERROR: This test requires sudo. Run with:")
        print(f"  sudo python3 {os.path.basename(__file__)} [{SAMPLE_LABEL}]")
        return 1

    print(f"{TEST_NAME}")
    print(f"Cable sample: {SAMPLE_LABEL}")
    print(f"Cycles: {TOTAL_CYCLES}")
    print(f"Sleep duration: {SLEEP_DURATION}s")
    print(f"{'─'*60}")

    # Verify baseline before starting
    speed_code, speed_label, _ = get_usb_speed()
    if speed_code is None or speed_code < 3:
        print(f"  ABORT: Hub not at 5Gbps before test start (got: {speed_label})")
        return 1
    print(f"  Baseline confirmed: {speed_label}")

    passed = 0
    failed = 0

    for cycle in range(1, TOTAL_CYCLES + 1):
        print(f"\n  Cycle {cycle}/{TOTAL_CYCLES}")

        # Sleep and wake
        schedule_wake_and_sleep()

        # After wake, we should be running again
        # Wait a few seconds for the system to stabilize
        time.sleep(5)

        # Wait for hub to appear
        print(f"    Waiting for hub re-enumeration (max {MAX_RECOVERY_WAIT}s)...")
        recovery_time = wait_for_hub(MAX_RECOVERY_WAIT)

        if recovery_time < 0:
            failed += 1
            print(f"    Hub not found after {MAX_RECOVERY_WAIT}s — FAIL")
            log_result(TEST_ID, f"{SAMPLE_LABEL}_cycle_{cycle}", "FAIL", None, "not found",
                       f"No enumeration within {MAX_RECOVERY_WAIT}s")
            continue

        # Check speed
        speed_code, speed_label, _ = get_usb_speed()

        if speed_code is not None and speed_code >= 3:
            passed += 1
            print(f"    Speed: {speed_label} (recovered in {recovery_time:.1f}s) — PASS")
            log_result(TEST_ID, f"{SAMPLE_LABEL}_cycle_{cycle}", "PASS", speed_code, speed_label,
                       f"recovery={recovery_time:.1f}s")
        else:
            failed += 1
            print(f"    Speed: {speed_label} (recovered in {recovery_time:.1f}s) — FAIL")
            log_result(TEST_ID, f"{SAMPLE_LABEL}_cycle_{cycle}", "FAIL", speed_code, speed_label,
                       f"recovery={recovery_time:.1f}s, fallback")

    print_summary(TEST_ID, TEST_NAME, TOTAL_CYCLES, passed, failed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
