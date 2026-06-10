#!/usr/bin/env python3
"""
Convert a Yosys JSON netlist to a Liberty (.lib) cell library description.

Extracts all unique cell types from the Yosys netlist and generates a
Liberty .lib file with each type represented as a Liberty cell with
its ports mapped to pins.
"""

import json
from collections import OrderedDict
from liberty.parser import parse_liberty


def lib_str(value):
    """Format a value for Liberty output."""
    if isinstance(value, str):
        # Escape inner quotes if present
        return f'"{value}"'
    return str(value)


def indent(level):
    return "    " * level


def format_attr(key, value, level):
    """Format a Liberty attribute assignment."""
    if isinstance(value, list):
        items = ", ".join(lib_str(v) for v in value)
        return f'{indent(level)}{key} ({items}) ;'
    return f'{indent(level)}{key} : {lib_str(value)} ;'


def format_group(group_name, args, attrs, subgroups, level):
    """Format a Liberty group block."""
    args_str = "(" + ", ".join(lib_str(a) for a in args) + ")" if args else "()"
    lines = [f'{indent(level)}{group_name}{args_str} {{']
    for k, v in attrs.items():
        lines.append(format_attr(k, v, level + 1))
    for sg_name, sg_args, sg_attrs, sg_subs in subgroups:
        lines.append(format_group(sg_name, sg_args, sg_attrs, sg_subs, level + 1))
    lines.append(f"{indent(level)}}}")
    return "\n".join(lines)


def generate_liberty(cell_types, lib_name="yosys_derived"):
    """Generate a Liberty .lib file from collected cell types.

    cell_types: dict of type_name -> {ports: {port_name: direction}}
    """
    lines = [f"library({lib_name}) {{"]

    # Header
    lines.append('  technology ("cmos") ;')
    lines.append('  time_unit : "1ns" ;')
    lines.append('  voltage_unit : "1V" ;')
    lines.append('  current_unit : "1mA" ;')
    lines.append('  capacitive_load_unit (1, "pf") ;')
    lines.append('  leakage_power_unit : "1nW" ;')
    lines.append('  delay_model : "table_lookup" ;')
    lines.append("")

    # Operating conditions
    lines.append("  operating_conditions (typical) {")
    lines.append("    process : 1.0 ;")
    lines.append("    temperature : 25.0 ;")
    lines.append("    voltage : 1.2 ;")
    lines.append("    tree_type : \"balanced_tree\" ;")
    lines.append("  }")
    lines.append("")
    lines.append("  lu_table_template (delay_template_2x2) {")
    lines.append('    variable_1 : "input_net_transition" ;')
    lines.append('    variable_2 : "total_output_net_capacitance" ;')
    lines.append('    index_1 ("0.1, 1.0") ;')
    lines.append('    index_2 ("0.05, 0.5") ;')
    lines.append("  }")
    lines.append("")

    # Cells in alphabetical order
    for cell_name in sorted(cell_types.keys()):
        # Sanitize: strip leading \, replace $ with _dollar_
        lib_cell_name = cell_name.lstrip("\\").replace("$", "_dollar_")
        cell_info = cell_types[cell_name]
        ports = cell_info["ports"]
        params = cell_info.get("parameters", {})
        is_seq = "Q" in ports

        lines.append(f"  cell ({lib_cell_name}) {{")
        lines.append("    area : 1.0 ;")
        if is_seq:
            lines.append('    ff : "IQ" ;')

        # Add key parameters as attributes
        for pk, pv in params.items():
            lines.append(f'    {pk} : {lib_str(pv)} ;')

        # Pins
        for pin_name in sorted(ports.keys()):
            direction = ports[pin_name]
            lines.append("")
            lines.append(f"    pin ({pin_name}) {{")
            lines.append(f"      direction : {lib_str(direction)} ;")
            if direction == "input" and pin_name.upper() in ("CLK", "CK", "C"):
                lines.append("      clock : true ;")
            lines.append("      capacitance : 0.5 ;")

            if direction == "output":
                func = f"{pin_name}"
                in_pins = [p for p in ports if ports[p] == "input"]
                if in_pins:
                    func = f"({' & '.join(in_pins)})"
                if pin_name in ("Q", "QN"):
                    func = "IQ" if pin_name == "Q" else "!IQ"
                lines.append(f'      function : {lib_str(func)} ;')

            if direction == "output":
                lines.append("      max_capacitance : 2.0 ;")
                lines.append("")
                # Pick the first input pin as the related_pin for timing
                in_pins = sorted(p for p, d in ports.items() if d == "input")
                related = "CK" if "CK" in ports else (in_pins[0] if in_pins else "unknown")
                lines.append("      timing () {")
                lines.append(f'        related_pin : "{related}" ;')
                lines.append('        timing_sense : positive_unate ;')
                lines.append("        cell_rise (delay_template_2x2) {")
                lines.append('          values ("0.1, 0.2", "0.3, 0.4") ;')
                lines.append("        }")
                lines.append("        rise_transition (delay_template_2x2) {")
                lines.append('          values ("0.05, 0.1", "0.2, 0.3") ;')
                lines.append("        }")
                lines.append("        cell_fall (delay_template_2x2) {")
                lines.append('          values ("0.08, 0.18", "0.25, 0.35") ;')
                lines.append("        }")
                lines.append("        fall_transition (delay_template_2x2) {")
                lines.append('          values ("0.04, 0.09", "0.18, 0.28") ;')
                lines.append("        }")
                lines.append("      }")

            lines.append("    }")

        # Leakage power
        lines.append("")
        lines.append("    leakage_power () {")
        lines.append("      value : 0.001 ;")
        lines.append("    }")

        lines.append("  }")
        lines.append("")

    lines.append("}")
    return "\n".join(lines)


def extract_cell_types(yosys_json_path):
    """Extract unique cell types and their port directions from a Yosys JSON netlist.

    Returns dict: type_name -> {ports: {name: direction}, parameters: {k: v}}
    """
    with open(yosys_json_path) as f:
        data = json.load(f)

    modules = data.get("modules", {})
    cell_types = OrderedDict()

    # Standard Yosys cell types with known port directions
    # These include both pre-techmap ($-prefix) and post-techmap ($_-prefix) cells
    STD_CELL_PORTS = {
        "$mul": {"A": "input", "B": "input", "Y": "output"},
        "$add": {"A": "input", "B": "input", "Y": "output"},
        "$sub": {"A": "input", "B": "input", "Y": "output"},
        "$div": {"A": "input", "B": "input", "Y": "output"},
        "$mod": {"A": "input", "B": "input", "Y": "output"},
        "$pow": {"A": "input", "B": "input", "Y": "output"},
        "$and": {"A": "input", "B": "input", "Y": "output"},
        "$or":  {"A": "input", "B": "input", "Y": "output"},
        "$xor": {"A": "input", "B": "input", "Y": "output"},
        "$eq":  {"A": "input", "B": "input", "Y": "output"},
        "$ne":  {"A": "input", "B": "input", "Y": "output"},
        "$ge":  {"A": "input", "B": "input", "Y": "output"},
        "$le":  {"A": "input", "B": "input", "Y": "output"},
        "$lt":  {"A": "input", "B": "input", "Y": "output"},
        "$gt":  {"A": "input", "B": "input", "Y": "output"},
        "$shl": {"A": "input", "B": "input", "Y": "output"},
        "$shr": {"A": "input", "B": "input", "Y": "output"},
        "$sshl": {"A": "input", "B": "input", "Y": "output"},
        "$sshr": {"A": "input", "B": "input", "Y": "output"},
        "$mux": {"A": "input", "B": "input", "S": "input", "Y": "output"},
        "$pmux": {"A": "input", "B": "input", "S": "input", "Y": "output"},
        "$dff": {"CLK": "input", "D": "input", "Q": "output"},
        "$adff": {"CLK": "input", "D": "input", "ARST": "input", "Q": "output"},
        "$aldff": {"CLK": "input", "D": "input", "ALOAD": "input", "Q": "output"},
        "$sdff": {"CLK": "input", "D": "input", "Q": "output"},
        "$sr": {"SET": "input", "CLR": "input", "Q": "output"},
        "$ff": {"D": "input", "Q": "output"},
        "$dlatch": {"EN": "input", "D": "input", "Q": "output"},
        "$dlatchsr": {"EN": "input", "D": "input", "SET": "input", "CLR": "input", "Q": "output"},
        "$not": {"A": "input", "Y": "output"},
        "$pos": {"A": "input", "Y": "output"},
        "$neg": {"A": "input", "Y": "output"},
        "$reduce_and": {"A": "input", "Y": "output"},
        "$reduce_or": {"A": "input", "Y": "output"},
        "$reduce_xor": {"A": "input", "Y": "output"},
        "$logic_not": {"A": "input", "Y": "output"},
        "$logic_and": {"A": "input", "B": "input", "Y": "output"},
        "$logic_or": {"A": "input", "B": "input", "Y": "output"},
        "$concat": {"A": "input", "B": "input", "Y": "output"},
        "$slice": {"A": "input", "Y": "output"},
        "$buf": {"A": "input", "Y": "output"},
        # Post-techmap technology primitives
        "$_DFF_P_": {"C": "input", "D": "input", "Q": "output"},
        "$_DFF_N_": {"C": "input", "D": "input", "Q": "output"},
        "$_DFF_PP0_": {"C": "input", "D": "input", "Q": "output"},
        "$_DFF_PP1_": {"C": "input", "D": "input", "Q": "output"},
        "$_DFF_NP0_": {"C": "input", "D": "input", "Q": "output"},
        "$_DFF_NP1_": {"C": "input", "D": "input", "Q": "output"},
        "$_DFF_PN0_": {"C": "input", "D": "input", "R": "input", "Q": "output"},
        "$_DFF_PN1_": {"C": "input", "D": "input", "R": "input", "Q": "output"},
        "$_DFF_NN0_": {"C": "input", "D": "input", "R": "input", "Q": "output"},
        "$_DFF_NN1_": {"C": "input", "D": "input", "R": "input", "Q": "output"},
        "$_DFF_PP0P_": {"C": "input", "D": "input", "R": "input", "S": "input", "Q": "output"},
        "$_DFF_PP1P_": {"C": "input", "D": "input", "R": "input", "S": "input", "Q": "output"},
        "$_MUX_": {"A": "input", "B": "input", "S": "input", "Y": "output"},
        "$_AND_": {"A": "input", "B": "input", "Y": "output"},
        "$_OR_": {"A": "input", "B": "input", "Y": "output"},
        "$_XOR_": {"A": "input", "B": "input", "Y": "output"},
        "$_NAND_": {"A": "input", "B": "input", "Y": "output"},
        "$_NOR_": {"A": "input", "B": "input", "Y": "output"},
        "$_XNOR_": {"A": "input", "B": "input", "Y": "output"},
        "$_NOT_": {"A": "input", "Y": "output"},
        "$_DLATCH_P_": {"E": "input", "D": "input", "Q": "output"},
        "$_DLATCH_N_": {"E": "input", "D": "input", "Q": "output"},
        "$_MUX16_": {"A": "input", "B": "input", "S": "input", "Y": "output"},
        "$_TBUF_": {"A": "input", "E": "input", "Y": "output"},
        "$_SDFF_P_": {"C": "input", "D": "input", "Q": "output"},
        "$_SDFF_N_": {"C": "input", "D": "input", "Q": "output"},
        "$_ALDFF_P_": {"C": "input", "D": "input", "L": "input", "Q": "output"},
    }

    for mod_name, module in modules.items():
        # Extract module ports as well (these become top-level pins too)
        module.get("ports", {})
        cells = module.get("cells", {})

        for cell_inst_name, cell_data in cells.items():
            cell_type = cell_data.get("type", "unknown")

            if cell_type not in cell_types:
                # Get port directions
                port_dirs = cell_data.get("port_directions", {})
                if not port_dirs and cell_type in STD_CELL_PORTS:
                    port_dirs = STD_CELL_PORTS[cell_type]

                # Get parameters
                params = cell_data.get("parameters", {})

                # Collect ports (ordered from port_directions)
                ports = {}
                for pname in sorted(port_dirs.keys()):
                    ports[pname] = port_dirs[pname]

                if not ports:
                    continue
                # Skip hierarchical module references (not technology primitives)
                if not cell_type.startswith("$"):
                    continue
                cell_types[cell_type] = {
                    "ports": ports,
                    "parameters": {k: v for k, v in params.items()
                                   if isinstance(v, (str, int, float, bool))},
                }

    return cell_types


def main():
    yosys_json = "yosys_syn_output.json"
    lib_output = "yosys_sphere_tech.lib"
    json_output = "yosys_sphere_tech_converted.json"

    print(f"Reading Yosys netlist: {yosys_json}")
    cell_types = extract_cell_types(yosys_json)

    print(f"\nFound {len(cell_types)} unique cell types:")
    for ct in sorted(cell_types.keys()):
        info = cell_types[ct]
        ports_desc = ", ".join(f"{p}({d[:3]})" for p, d in info["ports"].items())
        print(f"  {ct:40s}  {ports_desc}")

    print(f"\nGenerating Liberty file: {lib_output}")
    lib_content = generate_liberty(cell_types)
    with open(lib_output, "w") as f:
        f.write(lib_content)
    print(f"Written: {len(lib_content)} bytes")

    print("\nParsing .lib with liberty-parser...")
    with open(lib_output) as f:
        library = parse_liberty(f.read())

    cell_count = len(library.get_groups("cell"))
    print(f"Parsed {cell_count} cells")

    print(f"\nConverting to JSON: {json_output}")
    # Reuse the Method 2 conversion logic
    from liberty.types import EscapedString

    def _json_safe(value):
        if isinstance(value, EscapedString):
            return value.value.strip('"')
        if isinstance(value, list):
            return [_json_safe(v) for v in value]
        if hasattr(value, "tolist"):
            return value.tolist()
        return value

    def liberty_group_to_dict(group):
        result = {"type": group.group_name, "args": list(group.args)}
        attrs = {}
        for a in group.attributes:
            attrs[a.name] = _json_safe(a.value)
        if attrs:
            result["attributes"] = attrs
        if group.groups:
            result["groups"] = [liberty_group_to_dict(g) for g in group.groups]
        return result

    json_data = liberty_group_to_dict(library)
    with open(json_output, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"Written: {json_output}")

    # Verify against schema
    try:
        import jsonschema
        with open("liberty_json_schema.json") as f:
            schema = json.load(f)
        jsonschema.validate(instance=json_data, schema=schema)
        print("JSON validation against schema: VALID")
    except ImportError:
        print("jsonschema not available: skip validation")
    except jsonschema.ValidationError as e:
        print("JSON validation against schema: INVALID")
        print(f"  {e.message}")


if __name__ == "__main__":
    main()
