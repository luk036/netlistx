#!/usr/bin/env python3
"""
Tutorial: Selective Timing & Power Data Extraction from Liberty Files

This script performs focused extraction of timing and power data from
a Liberty library file. It demonstrates how to:
  - Extract detailed timing arcs for each cell/pin
  - Compute statistical summaries of delay tables
  - Extract power data (internal, leakage)
  - Generate a compact analysis-friendly JSON report

Based on the tutorial section: "Method 3: Selective JSON Extraction"
"""

import json

import numpy as np
from liberty.parser import parse_liberty
from liberty.types import EscapedString


def _json_safe(value):
    if isinstance(value, EscapedString):
        return value.value.strip('"')
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _get_attr(group, key, default=None):
    return _json_safe(group.get_attribute(key, default))


def extract_detailed_timing(lib_file):
    with open(lib_file, "r") as f:
        library = parse_liberty(f.read())

    report = {
        "library": {
            "name": library.group_name,
            "technology": _get_attr(library, "technology", "unknown"),
            "time_unit": _get_attr(library, "time_unit", "unknown"),
            "voltage_unit": _get_attr(library, "voltage_unit", "unknown"),
        },
        "operating_conditions": {},
        "cells": {},
    }

    for oc in library.get_groups("operating_conditions"):
        name = oc.args[0] if oc.args else "default"
        report["operating_conditions"][name] = {
            "process": float(oc.get_attribute("process", 1.0)),
            "temperature": float(oc.get_attribute("temperature", 25.0)),
            "voltage": float(oc.get_attribute("voltage", 1.0)),
        }

    for cell in library.get_groups("cell"):
        cell_name = cell.args[0]
        cell_info = {
            "area": float(cell.get_attribute("area", 0)),
            "is_sequential": "ff" in cell,
            "pins": {},
            "leakage_power": None,
            "internal_power": [],
        }

        lp = cell.get_groups("leakage_power")
        if lp:
            cell_info["leakage_power"] = float(lp[0].get_attribute("value", 0))

        for ip in cell.get_groups("internal_power"):
            related = _get_attr(ip, "related_pin", "unknown")
            power_entry = {"related_pin": related}
            for pwr_type in ["rise_power", "fall_power"]:
                pwr_grp = ip.get_groups(pwr_type)
                if pwr_grp:
                    tbl = pwr_grp[0].get_array("values")
                    power_entry[pwr_type] = {
                        "mean": float(tbl.mean()),
                        "values": tbl.tolist(),
                    }
            cell_info["internal_power"].append(power_entry)

        for pin in cell.get_groups("pin"):
            pin_name = pin.args[0]
            pin_info = {
                "direction": _get_attr(pin, "direction", "unknown"),
                "capacitance": float(pin.get_attribute("capacitance", 0)),
                "clock": pin.get_attribute("clock", False),
                "max_capacitance": _get_attr(pin, "max_capacitance", None),
                "function": _get_attr(pin, "function", None),
                "timing_arcs": [],
            }

            for timing in pin.get_groups("timing"):
                arc = {
                    "related_pin": _get_attr(timing, "related_pin", ""),
                    "timing_sense": _get_attr(timing, "timing_sense", ""),
                    "timing_type": _get_attr(timing, "timing_type", ""),
                }

                for table_key in [
                    "cell_rise",
                    "cell_fall",
                    "rise_transition",
                    "fall_transition",
                    "rise_constraint",
                    "fall_constraint",
                ]:
                    tbl_grp = timing.get_groups(table_key)
                    if tbl_grp:
                        table = tbl_grp[0].get_array("values")
                        arc[table_key] = {
                            "shape": list(table.shape),
                            "min": float(np.min(table)),
                            "max": float(np.max(table)),
                            "mean": float(np.mean(table)),
                            "std": float(np.std(table)),
                            "values": table.tolist(),
                        }

                pin_info["timing_arcs"].append(arc)

            cell_info["pins"][pin_name] = pin_info

        report["cells"][cell_name] = cell_info

    return report


def print_timing_summary(report):
    """Print a human-readable summary of the timing report."""
    lib = report["library"]
    print(f"Library: {lib['name']} ({lib['technology']})")
    print(f"Units: time={lib['time_unit']}, voltage={lib['voltage_unit']}")

    for oc_name, oc in report["operating_conditions"].items():
        print(
            f"Operating Conditions ({oc_name}): "
            f"{oc['process']}p, {oc['temperature']}°C, {oc['voltage']}V"
        )

    print()
    for cell_name, info in report["cells"].items():
        seq_marker = " [FF]" if info["is_sequential"] else ""
        lp = info["leakage_power"] or 0
        print(f"Cell: {cell_name}{seq_marker}  " f"area={info['area']}, leakage={lp}")

        for pin_name, pin in info["pins"].items():
            func = f" fn={pin['function']}" if pin["function"] else ""
            clock = " [CLK]" if pin["clock"] else ""
            maxcap = (
                f" maxcap={pin['max_capacitance']}" if pin["max_capacitance"] else ""
            )
            print(
                f"  Pin: {pin_name}  "
                f"dir={pin['direction']}, cap={pin['capacitance']}"
                f"{func}{clock}{maxcap}"
            )

            for arc in pin["timing_arcs"]:
                related = arc["related_pin"]
                sense = arc["timing_sense"]
                ttype = arc["timing_type"]

                # Collect delay info
                delays = []
                for dk in ["cell_rise", "cell_fall"]:
                    if dk in arc:
                        delays.append(f"{dk}={arc[dk]['mean']:.4f}")
                delay_str = ", ".join(delays) if delays else ""

                # Collect transition info
                trans = []
                for tk in ["rise_transition", "fall_transition"]:
                    if tk in arc:
                        trans.append(f"{tk}={arc[tk]['mean']:.4f}")
                trans_str = ", ".join(trans) if trans else ""

                parts = [f"    → {related}"]
                if ttype and ttype != "unknown":
                    parts.append(f"[{ttype}]")
                if sense and sense != "unknown":
                    parts.append(f"({sense})")
                if delay_str:
                    parts.append(f" delay: {delay_str}")
                if trans_str:
                    parts.append(f" trans: {trans_str}")

                print(" ".join(parts))

        if info["internal_power"]:
            for ip in info["internal_power"]:
                pwrs = []
                for pt in ["rise_power", "fall_power"]:
                    if pt in ip:
                        pwrs.append(f"{pt}={ip[pt]['mean']:.4f}")
                if pwrs:
                    print(
                        f"  InternalPower({ip['related_pin']}): " f"{', '.join(pwrs)}"
                    )

        print()


def main():
    lib_file = "example_minimal.lib"
    output_json = "timing_analysis_detailed.json"

    print("=" * 60)
    print("TIMING & POWER EXTRACTION TUTORIAL")
    print("=" * 60)

    # Extract
    print(f"\nExtracting timing data from: {lib_file}")
    report = extract_detailed_timing(lib_file)

    # Print summary
    print("\n--- Summary ---")
    print_timing_summary(report)

    # Save to JSON
    print(f"\nSaving detailed report to: {output_json}")
    with open(output_json, "w") as f:
        json.dump(report, f, indent=2)
    print(f"File size: {len(json.dumps(report)):,} bytes")

    # Sanity checks
    cell_count = len(report["cells"])
    pin_count = sum(len(c["pins"]) for c in report["cells"].values())
    arc_count = sum(
        len(p["timing_arcs"])
        for c in report["cells"].values()
        for p in c["pins"].values()
    )
    print(
        f"\nStatistics: {cell_count} cells, {pin_count} pins, {arc_count} timing arcs"
    )


if __name__ == "__main__":
    main()
