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

from usb_utils import (get_usb_speed, check_hub_enumerated, connect_hub,
                       describe_hub, hub_ident, log_result, print_summary)

TEST_ID = "5_1_2_connect_disconnect"
TEST_NAME = "Test 5.1.2 — Connect/Disconnect Cycling"
TOTAL_CYCLES = 20
DISCONNECT_WAIT = 5
RECONNECT_WAIT = 10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", nargs="?", default="sample_1")
    parser.add_argument("--port", default="0",
                        help="Hub port to cycle: 0-7 for downstream, 'upstream' for uplink")
    parser.add_argument("--device", choices=["control", "data"], default="control",
                        help="Which hub interface to check speed on")
    args = parser.parse_args()

    print(f"{TEST_NAME}")
    print(f"Cable sample: {args.sample}")
    print(f"Cycles: {TOTAL_CYCLES}")
    print(f"Hub port: {args.port} | Device: {args.device}")

    probe, info = connect_hub()
    if probe is None:
        print("  ABORT: no Acroname hub found via BrainStem API")
        return 1
    probe.disconnect()
    print(f"Hub: {describe_hub(info)}")
    hub_model, hub_serial = hub_ident(info)
    is_upstream = args.port.lower() == "upstream"
    port_num = None if is_upstream else int(args.port)
    port_label = "upstream" if is_upstream else str(port_num)
    if not is_upstream and port_num >= info["ports"]:
        print(f"  WARNING: port {port_num} is out of range for this hub "
              f"(0–{info['ports'] - 1})")
    print(f"{'─'*60}")

    passed = 0
    failed = 0

    for cycle in range(1, TOTAL_CYCLES + 1):
        print(f"\n  Cycle {cycle}/{TOTAL_CYCLES}")

        hub, _ = connect_hub()
        if hub is None:
            print(f"    Cannot connect to hub API")
            failed += 1
            log_result(TEST_ID, args.sample, "FAIL", None, "no API",
                       cycle=cycle, device=args.device, port=port_label,
                       hub_model=hub_model, hub_serial=hub_serial,
                       notes="API connection failed")
            time.sleep(RECONNECT_WAIT)
            continue

        if is_upstream:
            print(f"    Disabling upstream...")
            hub.usb.setUpstreamMode(255)  # UPSTREAM_MODE_NONE
            time.sleep(DISCONNECT_WAIT)
            print(f"    Re-enabling upstream...")
            hub.usb.setUpstreamMode(2)  # UPSTREAM_MODE_AUTO
        else:
            print(f"    Disabling port {port_num}...")
            hub.usb.setPortDisable(port_num)
            time.sleep(DISCONNECT_WAIT)
            print(f"    Re-enabling port {port_num}...")
            hub.usb.setPortEnable(port_num)
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

        log_result(TEST_ID, args.sample, status, speed_code, speed_label,
                   cycle=cycle, device=args.device, port=port_label,
                   hub_model=hub_model, hub_serial=hub_serial)

    print_summary(TEST_ID, TEST_NAME, TOTAL_CYCLES, passed, failed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
