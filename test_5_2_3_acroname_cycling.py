#!/usr/bin/env python3
"""Test 5.2.3 — Acroname Hub API Control Cycling

Uses the BrainStem API to disable/re-enable a hub port, then
verifies re-enumeration at SuperSpeed or better each time.

Default: 50 cycles. Override with --cycles N.

Pass: All cycles enumerate at SuperSpeed+, no API timeouts
Fail: Any cycle fails to enumerate, reports wrong speed, or times out
"""

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brainstem
from brainstem.result import Result
from usb_utils import get_usb_speed, check_hub_enumerated, log_result, print_summary

TEST_ID = "5_2_3_acroname_cycling"
TEST_NAME = "Test 5.2.3 — Acroname Hub API Control Cycling"
DISABLE_WAIT = 5
RECONNECT_WAIT = 10
REPORT_EVERY = 10


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
    parser.add_argument("--cycles", type=int, default=50)
    parser.add_argument("--port", type=int, default=0,
                        help="Hub port to cycle (default: 0)")
    parser.add_argument("--device", choices=["control", "data"], default="control",
                        help="Which hub interface to check speed on")
    args = parser.parse_args()

    total_cycles = args.cycles
    sample_label = args.sample

    print(f"{TEST_NAME}")
    print(f"Cable sample: {sample_label}")
    print(f"Cycles: {total_cycles}")
    print(f"Hub port: {args.port} | Device: {args.device}")
    print(f"{'─'*60}")

    speed_code, speed_label, _ = get_usb_speed(device=args.device)
    if speed_code is None or speed_code < 3:
        print(f"  ABORT: Device not at SuperSpeed before test start (got: {speed_label})")
        return 1
    print(f"  Baseline confirmed: {speed_label}")
    print(f"  Starting {total_cycles}-cycle test...\n")

    passed = 0
    failed = 0
    api_errors = 0
    start_time = time.time()

    for cycle in range(1, total_cycles + 1):
        hub = connect_hub()
        if hub is None:
            api_errors += 1
            failed += 1
            log_result(TEST_ID, f"{sample_label}_cycle_{cycle}", "FAIL", None, "no API",
                       f"port={args.port},device={args.device}")
            if cycle % REPORT_EVERY == 0 or cycle == 1:
                print(f"  [{cycle:>4}/{total_cycles}] FAIL — API connection failed")
            time.sleep(RECONNECT_WAIT)
            continue

        hub.usb.setPortDisable(args.port)
        time.sleep(DISABLE_WAIT)
        hub.usb.setPortEnable(args.port)
        hub.disconnect()

        # Poll for re-enumeration (up to 30s)
        enum_start = time.time()
        speed_code = None
        speed_label = "not found"
        while time.time() - enum_start < 30:
            if check_hub_enumerated(device=args.device):
                time.sleep(2)
                speed_code, speed_label, _ = get_usb_speed(device=args.device)
                if speed_code is not None:
                    break
            time.sleep(1)

        if speed_code is not None and speed_code >= 3:
            passed += 1
            status = "PASS"
        elif speed_code is None:
            failed += 1
            status = "FAIL"
            speed_label = "not found"
        else:
            failed += 1
            status = "FAIL"

        log_result(TEST_ID, f"{sample_label}_cycle_{cycle}", status, speed_code, speed_label,
                   f"port={args.port},device={args.device}")

        if cycle % REPORT_EVERY == 0 or cycle == 1 or status == "FAIL":
            elapsed = time.time() - start_time
            rate = cycle / elapsed * 60
            print(f"  [{cycle:>4}/{total_cycles}] {status} — {speed_label}  "
                  f"(pass:{passed} fail:{failed} api_err:{api_errors} "
                  f"rate:{rate:.0f} cycles/min)")

    elapsed = time.time() - start_time

    print(f"\n  Total time: {elapsed/60:.1f} minutes ({elapsed/total_cycles:.1f}s per cycle)")
    print(f"  API errors: {api_errors}")
    print_summary(TEST_ID, TEST_NAME, total_cycles, passed, failed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
