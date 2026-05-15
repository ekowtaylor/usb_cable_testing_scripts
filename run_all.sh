#!/bin/bash
# USB Cable Validation — Test Runner
# Usage: ./run_all.sh [sample_label] [device] [port]
#
#   sample_label  Cable identifier (default: sample_1)
#   device        "control" or "data" (default: control)
#   port          Hub port number to cycle (default: 0)
#
# Tests 5.1.1, 5.1.2, and 5.2.3 run without sudo.
# Test 5.1.4 (sleep/wake) requires sudo and runs separately.

SAMPLE="${1:-sample_1}"
DEVICE="${2:-control}"
PORT="${3:-0}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================================"
echo "  USB Cable Validation Test Suite"
echo "  Sample: ${SAMPLE}"
echo "  Device: ${DEVICE} | Port: ${PORT}"
echo "  Date: $(date)"
echo "============================================================"
echo ""

echo ">>> Test 5.1.1 — Initial Link Speed Verification"
python3 "${DIR}/test_5_1_1_link_speed.py" "${SAMPLE}" --device "${DEVICE}"
echo ""

echo ">>> Test 5.1.2 — Connect/Disconnect Cycling (20 cycles)"
python3 "${DIR}/test_5_1_2_connect_disconnect.py" "${SAMPLE}" --port "${PORT}" --device "${DEVICE}"
echo ""

echo ">>> Test 5.2.3 — Acroname Hub API Cycling (50 cycles)"
python3 "${DIR}/test_5_2_3_acroname_cycling.py" "${SAMPLE}" --port "${PORT}" --device "${DEVICE}" --cycles 50
echo ""

echo "============================================================"
echo "  NOTE: Test 5.1.4 (Sleep/Wake) requires sudo."
echo "  Run separately:"
echo "    sudo python3 ${DIR}/test_5_1_4_sleep_wake.py ${SAMPLE} --device ${DEVICE}"
echo "============================================================"
echo ""
echo "Results saved to: ${DIR}/results/"
