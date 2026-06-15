#!/usr/bin/env python3
"""
Tutorial: Converting Liberty (.lib) Files to JSON

This script implements three methods from the tutorial:
  Method 1: Using libertymetric (dedicated tool) — if available
  Method 2: Custom JSON serialization with liberty-parser (full conversion)
  Method 3: Selective JSON extraction for timing analysis

Based on the tutorial section: "Converting to JSON"
"""

import json

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


# ======================================================================
# METHOD 2: Custom JSON Serialization with liberty-parser
# ======================================================================


def liberty_group_to_dict(group):
    result = {
        "type": group.group_name,
        "args": list(group.args),
    }

    attrs = {}
    for a in group.attributes:
        attrs[a.name] = _json_safe(a.value)
    if attrs:
        result["attributes"] = attrs

    # Recursively convert subgroups
    if group.groups:
        result["groups"] = [liberty_group_to_dict(g) for g in group.groups]

    return result


def method2_custom_serialization(lib_file, output_json):
    """Method 2: Full Liberty → JSON conversion using custom serialization."""
    print(f"  Reading: {lib_file}")
    with open(lib_file, "r") as f:
        library = parse_liberty(f.read())

    print("  Converting to dictionary...")
    json_data = liberty_group_to_dict(library)

    print(f"  Writing: {output_json}")
    with open(output_json, "w") as f:
        json.dump(json_data, f, indent=2)

    # Summary
    cell_count = sum(1 for g in library.get_groups("cell"))
    print(f"  Converted {cell_count} cells")
    print(f"  Output size: {len(json.dumps(json_data)):,} bytes")
    return json_data


# ======================================================================
# METHOD 3: Selective JSON Extraction (timing analysis)
# ======================================================================


def extract_timing_data(lib_file):
    with open(lib_file, "r") as f:
        library = parse_liberty(f.read())

    timing_data = {}

    for cell in library.get_groups("cell"):
        cell_name = cell.args[0]
        timing_data[cell_name] = {
            "area": float(cell.get_attribute("area", 0)),
            "is_sequential": "ff" in cell,
            "pins": {},
        }

        for pin in cell.get_groups("pin"):
            pin_name = pin.args[0]
            pin_info = {
                "direction": _json_safe(pin.get_attribute("direction", "unknown")),
                "capacitance": float(pin.get_attribute("capacitance", 0)),
            }

            arcs = []
            for timing in pin.get_groups("timing"):
                arc = {
                    "related_pin": _json_safe(
                        timing.get_attribute("related_pin", "unknown")
                    ),
                    "timing_sense": _json_safe(
                        timing.get_attribute("timing_sense", "unknown")
                    ),
                    "timing_type": _json_safe(
                        timing.get_attribute("timing_type", "unknown")
                    ),
                }
                for table_name in [
                    "cell_rise",
                    "cell_fall",
                    "rise_transition",
                    "fall_transition",
                    "rise_constraint",
                    "fall_constraint",
                ]:
                    tbl_grp = timing.get_groups(table_name)
                    if tbl_grp:
                        table = tbl_grp[0].get_array("values")
                        arc[table_name] = {
                            "shape": list(table.shape),
                            "min": float(table.min()),
                            "max": float(table.max()),
                            "mean": float(table.mean()),
                            "values": table.tolist(),
                        }
                arcs.append(arc)

            if arcs:
                pin_info["timing_arcs"] = arcs

            timing_data[cell_name]["pins"][pin_name] = pin_info

        # Extract leakage power
        leakage = cell.get_groups("leakage_power")
        if leakage:
            timing_data[cell_name]["leakage_power"] = float(
                leakage[0].get_attribute("value", 0)
            )

    return timing_data


def method3_selective_extraction(lib_file, output_json):
    """Method 3: Selective timing data → JSON."""
    print(f"  Reading: {lib_file}")
    data = extract_timing_data(lib_file)

    print(f"  Writing: {output_json}")
    with open(output_json, "w") as f:
        json.dump(data, f, indent=2)

    # Summary
    for cell_name, info in data.items():
        pin_count = len(info["pins"])
        arc_count = sum(len(p.get("timing_arcs", [])) for p in info["pins"].values())
        print(
            f"  {cell_name}: {pin_count} pins, {arc_count} timing arcs, "
            f"area={info['area']}"
        )
    return data


# ======================================================================
# METHOD 1: libertymetric (if available)
# ======================================================================


def method1_libertymetric(lib_file, output_json):
    """Method 1: Using libertymetric (if installed)."""
    try:
        from libertymetric.classLiberty import liberty as lutil
    except ImportError:
        print("  libertymetric not installed — skipping Method 1")
        print("  Install with: pip install libertymetric")
        return None

    print(f"  Reading: {lib_file}")
    lnode = lutil.read_lib(lib_file)
    print("  Converting to JSON...")
    lutil.dump_json(lnode, out=output_json)
    print(f"  Written: {output_json}")
    return lnode


# ======================================================================
# MAIN
# ======================================================================


def main():
    lib_file = "example_minimal.lib"

    print("=" * 60)
    print("LIBERTY → JSON CONVERSION TUTORIAL")
    print("=" * 60)

    # --- Method 1: libertymetric ---
    print("\n--- Method 1: libertymetric ---")
    method1_libertymetric(lib_file, "example_minimal_method1.json")

    # --- Method 2: Custom Serialization ---
    print("\n--- Method 2: Custom JSON Serialization ---")
    method2_custom_serialization(lib_file, "example_minimal_method2.json")

    # --- Method 3: Selective Timing Extraction ---
    print("\n--- Method 3: Selective Timing Extraction ---")
    method3_selective_extraction(lib_file, "example_timing_analysis.json")

    # --- Verify round-trip for Method 2 ---
    print("\n--- Verification: Method 2 Round-Trip ---")
    with open("example_minimal_method2.json", "r") as f:
        loaded_data = json.load(f)
    print(f"  Loaded JSON root type: {loaded_data['type']}")
    print(f"  Loaded JSON root args: {loaded_data['args']}")
    cell_count = sum(1 for g in loaded_data.get("groups", []) if g["type"] == "cell")
    print(f"  Cells in JSON: {cell_count}")

    print("\nAll conversions completed successfully.")


if __name__ == "__main__":
    main()
