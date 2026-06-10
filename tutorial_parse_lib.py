#!/usr/bin/env python3
"""
Tutorial: Basic Liberty File Parsing with liberty-parser

This script demonstrates the core usage of the liberty-parser library:
  - Parsing a .lib file
  - Iterating through cells, pins, and timing groups
  - Extracting timing tables as NumPy arrays
  - Modifying attributes
  - Writing back to a .lib file

Based on the tutorial section: "Python: Using liberty-parser → Basic Usage"
"""

import numpy as np
from liberty.parser import parse_liberty
from liberty.types import Group


def main():
    lib_file = "example_minimal.lib"

    # ---------------------------------------------------------------
    # 1. Parse the Liberty file
    # ---------------------------------------------------------------
    print("=" * 60)
    print("1. PARSING THE LIBERTY FILE")
    print("=" * 60)
    with open(lib_file, "r") as f:
        library = parse_liberty(f.read())
    print(f"Parsed: {lib_file}")
    print(f"Library name: {library.group_name}")

    # ---------------------------------------------------------------
    # 2. Iterate through cells and their pins
    # ---------------------------------------------------------------
    print("\n" + "=" * 60)
    print("2. ITERATING THROUGH CELLS AND PINS")
    print("=" * 60)

    for cell_group in library.get_groups("cell"):
        cell_name = cell_group.args[0]
        print(f"\nCell: {cell_name}")

        # Cell-level attributes
        for attr in ["area", "is_macro", "ff"]:
            if attr in cell_group:
                print(f"  {attr}: {cell_group[attr]}")

        # Examine pins
        for pin_group in cell_group.get_groups("pin"):
            pin_name = pin_group.args[0]
            direction = pin_group.get_attribute("direction", "unknown")
            cap = pin_group.get_attribute("capacitance", "N/A")
            print(f"  Pin {pin_name}: direction={direction}, capacitance={cap}")

            # Extract timing tables as NumPy arrays
            timing_groups = pin_group.get_groups("timing")
            for timing in timing_groups:
                related_pin = timing.get_attribute("related_pin", "N/A")
                for table_name in ["cell_rise", "cell_fall", "rise_transition",
                                   "fall_transition", "rise_constraint"]:
                    tbl_grp = timing.get_groups(table_name)
                    if tbl_grp:
                        delay_table = tbl_grp[0].get_array("values")
                        print(f"    {table_name}({related_pin}): "
                              f"shape={delay_table.shape}, "
                              f"min={delay_table.min():.4f}, "
                              f"max={delay_table.max():.4f}")

    # ---------------------------------------------------------------
    # 3. Extract a specific delay table as a NumPy array
    # ---------------------------------------------------------------
    print("\n" + "=" * 60)
    print("3. NUMPY ARRAY EXTRACTION (AND2_X1 pin Z → timing → cell_rise)")
    print("=" * 60)

    and2 = library.get_groups("cell", "AND2_X1")
    if and2:
        for pin in and2[0].get_groups("pin"):
            if pin.args[0] == "Z":
                for timing in pin.get_groups("timing"):
                    cr_grp = timing.get_groups("cell_rise")
                    if cr_grp:
                        delay_table = cr_grp[0].get_array("values")
                        print("cell_rise table (NumPy array):")
                        print(delay_table)
                        print(f"Shape: {delay_table.shape}")
                        print(f"Dtype: {delay_table.dtype}")

                        avg_delay = np.mean(delay_table)
                        print(f"Average delay: {avg_delay:.4f} (ns)")

    # ---------------------------------------------------------------
    # 4. Find all cells with sequential logic (flip-flops)
    # ---------------------------------------------------------------
    print("\n" + "=" * 60)
    print("4. SEQUENTIAL CELL DETECTION")
    print("=" * 60)

    for cell_group in library.get_groups("cell"):
        is_seq = "ff" in cell_group
        has_clock = any(
            pin.get_attribute("clock", False)
            for pin in cell_group.get_groups("pin")
        )
        if is_seq or has_clock:
            print(f"  {cell_group.args[0]}: "
                  f"sequential={is_seq}, has_clock_pin={has_clock}")

    # ---------------------------------------------------------------
    # 5. Extract library-level attributes
    # ---------------------------------------------------------------
    print("\n" + "=" * 60)
    print("5. LIBRARY-LEVEL ATTRIBUTES")
    print("=" * 60)

    lib_attrs = [
        "technology", "time_unit", "voltage_unit", "current_unit",
        "delay_model", "default_fanout_load", "default_input_pin_cap",
        "nom_process", "nom_temperature", "nom_voltage",
    ]
    for attr in lib_attrs:
        if attr in library:
            print(f"  {attr}: {library[attr]}")

    # ---------------------------------------------------------------
    # 6. Modify attributes and write back
    # ---------------------------------------------------------------
    print("\n" + "=" * 60)
    print("6. MODIFYING AND WRITING BACK")
    print("=" * 60)

    # Change time unit
    old_unit = library["time_unit"]
    library["time_unit"] = "1ps"
    print(f"  Changed time_unit from {old_unit} to {library['time_unit']}")

    # Add a comment group
    comment = Group("comment", ["Modified by tutorial_parse_lib.py"])
    library.groups.append(comment)
    print("  Added comment group")

    # Write modified version
    modified_lib = str(library)
    output_file = "example_modified.lib"
    with open(output_file, "w") as f:
        f.write(modified_lib)
    print(f"  Wrote modified library to: {output_file}")

    library["time_unit"] = old_unit
    library.groups.remove(comment)


if __name__ == "__main__":
    main()
