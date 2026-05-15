#!/usr/bin/env python3
"""Shared utilities for USB cable validation tests.

Model-agnostic: works with any Acroname BrainStem hub (USBHub3p, USBHub3c,
USBHub2x4, ...). The hub model and ioreg device-node names are auto-detected
at runtime rather than hardcoded, so the same suite runs unchanged across
different hub hardware on the bench.
"""

import subprocess
import csv
import os
import re
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

ACRONAME_VENDOR = "Acroname Inc."

# Known BrainStem model codes -> hub class name + downstream port count.
# Unknown models still work via the class-name fallback in connect_hub().
HUB_MODELS = {
    19: {"class": "USBHub3p", "ports": 8},
    # USBHub3c / USBHub2x4 model codes are resolved by the fallback probe
    # below when not listed here.
}

# Ordered class-name fallbacks tried when the model code is not in HUB_MODELS.
HUB_CLASS_FALLBACKS = ["USBHub3p", "USBHub3c", "USBHub2x4", "USBCSwitch"]

# Default downstream port count when the model is unknown (used only for a
# soft out-of-range warning, never to block a run).
DEFAULT_PORT_COUNT = 4


def _ioreg_acroname_nodes():
    """Parse `ioreg -p IOUSB -l` and return Acroname device nodes.

    Every `+-o <Name>@<addr>` line starts a new node block; the USBSpeed and
    vendor properties that follow (before the next `+-o`) belong to that node.
    Returns a list of dicts: {"name": str, "usb_speed": int|None}.
    Only nodes whose vendor is Acroname are returned.
    """
    result = subprocess.run(
        ["ioreg", "-p", "IOUSB", "-l"],
        capture_output=True, text=True, timeout=10,
    )
    nodes = []
    cur = None
    node_re = re.compile(r"\+-o (\S+?)@")

    def flush():
        if cur is not None and cur["acroname"]:
            nodes.append({"name": cur["name"], "usb_speed": cur["usb_speed"]})

    for line in result.stdout.splitlines():
        if "+-o " in line:
            flush()
            m = node_re.search(line)
            name = m.group(1) if m else line.split("+-o ", 1)[1].split()[0]
            cur = {"name": name, "usb_speed": None, "acroname": False}
            continue
        if cur is None:
            continue
        if '"USBSpeed"' in line:
            try:
                cur["usb_speed"] = int(line.split("=")[1].strip())
            except (ValueError, IndexError):
                pass
        elif ACRONAME_VENDOR in line:
            cur["acroname"] = True
    flush()
    return nodes


def _split_stem_data(nodes):
    """Split Acroname nodes into (stem/control, data) by name.

    The control interface always carries 'Stem' in its node name
    (e.g. USBHub3p-Stem, USBHub3c-Stem); the data path does not
    (e.g. USBHub3c-3-Up0, and its USB-2 companion USBHub3c-2-Up0).
    """
    stem = [n for n in nodes if "Stem" in n["name"]]
    data = [n for n in nodes if "Stem" not in n["name"]]
    return stem, data


def get_usb_speed(device="control"):
    """Query ioreg for the Acroname hub's negotiated USB speed.

    Args:
        device: "control" for the Stem port, "data" for the data path.

    For the data path, the highest-speed Acroname node is reported. This
    means a USB-2 fallback (only the USB-2 companion present, no SuperSpeed
    node) is detected as High Speed rather than misreported as "not found".

    Returns: (speed_code, speed_label, node_name)
    """
    try:
        nodes = _ioreg_acroname_nodes()
    except Exception as e:
        return None, f"Error: {e}", ""

    stem, data = _split_stem_data(nodes)
    if device == "data":
        candidates = [n for n in data if n["usb_speed"] is not None]
        node = max(candidates, key=lambda n: n["usb_speed"]) if candidates else None
    else:
        candidates = [n for n in stem if n["usb_speed"] is not None]
        node = candidates[0] if candidates else None

    if node is None:
        return None, "Device not found", ""

    code = node["usb_speed"]
    label, rate = USB_SPEED_MAP.get(code, ("Unknown", "Unknown"))
    return code, f"{label} ({rate})", node["name"]


def check_hub_enumerated(device="control"):
    """Return True if the Acroname hub's requested interface is enumerated.

    For the data path this returns True if *any* Acroname data node is
    present (including a USB-2-only companion), so a speed fallback is
    distinguishable from a true enumeration timeout by the caller.
    """
    try:
        nodes = _ioreg_acroname_nodes()
    except Exception:
        return False
    stem, data = _split_stem_data(nodes)
    return bool(data) if device == "data" else bool(stem)


def connect_hub():
    """Discover and connect to the first Acroname BrainStem hub over USB.

    The hub class is chosen from the discovered model code, falling back to
    probing known classes. brainstem is imported lazily so tests that only
    need ioreg (e.g. 5.1.1) run without the SDK installed.

    Returns: (hub, info) where info = {class, model, serial, ports}, or
             (None, None) if no hub could be connected.
    """
    import brainstem
    from brainstem.result import Result

    specs = brainstem.discover.findAllModules(brainstem.link.Spec.USB)
    if not specs:
        return None, None
    spec = specs[0]
    model = getattr(spec, "model", None)

    order = []
    if model in HUB_MODELS:
        order.append(HUB_MODELS[model]["class"])
    order += [c for c in HUB_CLASS_FALLBACKS if c not in order]

    for cls_name in order:
        cls = getattr(brainstem.stem, cls_name, None)
        if cls is None:
            continue
        hub = cls()
        if hub.connectFromSpec(spec) == Result.NO_ERROR:
            info = {
                "class": cls_name,
                "model": model,
                "serial": getattr(spec, "serial_number", None),
                "ports": HUB_MODELS.get(model, {}).get("ports", DEFAULT_PORT_COUNT),
            }
            return hub, info
    return None, None


def describe_hub(info):
    """Human-readable one-liner for a connect_hub() info dict."""
    if not info:
        return "unknown hub"
    serial = info.get("serial")
    serial_str = f"{serial:#010x}" if isinstance(serial, int) else str(serial)
    return (f"{info['class']} (model {info['model']}, serial {serial_str}, "
            f"{info['ports']} ports)")


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
