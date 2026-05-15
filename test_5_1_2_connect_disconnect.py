#!/usr/bin/env python3
"""Test 5.1.2 — Connect/Disconnect Cycling (via Acroname port control)

Disables and re-enables a USB port on the Acroname hub to simulate
cable disconnect/reconnect, then verifies speed re-negotiation.

Pass: All cycles negotiate SuperSpeed or better
Fail: Any cycle results in USB 2.0 fallback or no enumeration
"""

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brainstem
from brainstem.result import Result
from usb_utils import get_usb_speed, check_hub_enumerated, log_result, print_summary

TEST_ID = "5_1_2_connect_disconnect"
TEST_NAME = "Test 5.1.2 — Connect/Disconnect Cycling"
TOTAL_CYCLES = 20
DISCONNECT_WAIT = 5
RECONNECT_WAIT = 10


def connect_hub():
    specs = brainstem.discover.findAllModules(brainstem.link.Spec.USB)
    if not specs:
        return None
    hub = brainstem.stem.USBHub3c()
    err = hub.connectFromSpec(specs[0])
    if err == Result.NO_ERROR:
        return hub
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", nargs="?", default="sample_1")
    parser.add_argument("--port", type=int, default=0,
                        help="Hub port to cycle (default: 0)")
    parser.add_argument("--device", choices=["control", "data"], default="control",
                        help="Which hub interface to check speed on")
    args = parser.parse_args()

    print(f"{TEST_NAME}")
    print(f"Cable sample: {args.sample}")
    print(f"Cycles: {TOTAL_CYCLES}")
    print(f"Hub port: {args.port} | Device: {args.device}")
    print(f"{'─'*60}")

    passed = 0
    failed = 0

    for cycle in range(1, TOTAL_CYCLES + 1):
        print(f"\n  Cycle {cycle}/{TOTAL_CYCLES}")

        hub = connect_hub()
        if hub is None:
            print(f"    Cannot connect to hub API")
            failed += 1
            log_result(TEST_ID, f"{args.sample}_cycle_{cycle}", "FAIL", None, "no API")
            time.sleep(RECONNECT_WAIT)
            continue

        print(f"    Disabling port {args.port}...")
        hub.usb.setPortDisable(args.port)
        time.sleep(DISCONNECT_WAIT)

        print(f"    Re-enabling port {args.port}...")
        hub.usb.setPortEnable(args.port)
        hub.disconnect()

        print(f"    Waiting for re-enumeration...")
        enum_start = time.time()
        speed_code = None
        speed_label = "not found"
        while time.time() - enum_start < 60:
            if check_hub_enumerated(device=args.device):
                time.sleep(2)
                speed_code, speed_label, _ = get_usb_speed(device=args.device)
                if speed_code is not None:
                    break
            time.sleep(1)

        if speed_code is not None and speed_code >= 3:
            passed += 1
            status = "PASS"
            print(f"    Speed: {speed_label} — PASS")
        elif speed_code is None:
            failed += 1
            status = "FAIL"
            speed_label = "not found"
            print(f"    Device not enumerated — FAIL")
        else:
            failed += 1
            status = "FAIL"
            print(f"    Speed: {speed_label} — FAIL (fallback)")

        log_result(TEST_ID, f"{args.sample}_cycle_{cycle}", status, speed_code, speed_label,
                   f"port={args.port},device={args.device}")

    print_summary(TEST_ID, TEST_NAME, TOTAL_CYCLES, passed, failed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
