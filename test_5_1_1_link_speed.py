#!/usr/bin/env python3
"""Test 5.1.1 — Initial Link Speed Verification

Verifies the Acroname USBHub3c negotiates USB 3.1 Gen 1 (5Gbps) or higher
through the cable under test.

Pass: USBSpeed >= 3 (SuperSpeed or better)
Fail: USBSpeed < 3 (fallback to USB 2.0) or device not enumerated
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from usb_utils import get_usb_speed, hub_label, log_result, print_summary

TEST_ID = "5_1_1_link_speed"
TEST_NAME = "Test 5.1.1 — Initial Link Speed Verification"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", nargs="?", default="sample_1")
    parser.add_argument("--device", choices=["control", "data"], default="control",
                        help="Which hub interface to check: control (Stem) or data (Up0)")
    args = parser.parse_args()

    hub_model, hub_serial = hub_label()

    print(f"{TEST_NAME}")
    print(f"Cable sample: {args.sample}")
    print(f"Hub: {hub_model or 'unknown'} {hub_serial}")
    print(f"Device: {args.device}")
    print(f"{'─'*60}")

    speed_code, speed_label, _ = get_usb_speed(device=args.device)

    common = dict(cycle="", device=args.device, port="",
                  hub_model=hub_model, hub_serial=hub_serial)

    if speed_code is None:
        status = "FAIL"
        print(f"  Result: FAIL — device not enumerated")
        log_result(TEST_ID, args.sample, "FAIL", None, "not found", **common)
    elif speed_code >= 3:
        status = "PASS"
        print(f"  Negotiated speed: {speed_label}")
        print(f"  Result: PASS")
        log_result(TEST_ID, args.sample, "PASS", speed_code, speed_label, **common)
    else:
        status = "FAIL"
        print(f"  Negotiated speed: {speed_label}")
        print(f"  Result: FAIL — fell back to {speed_label}")
        log_result(TEST_ID, args.sample, "FAIL", speed_code, speed_label, **common)

    print_summary(TEST_ID, TEST_NAME, 1, 1 if status == "PASS" else 0, 0 if status == "PASS" else 1)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
