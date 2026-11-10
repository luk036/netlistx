# Working with Synopsys Liberty (.lib) Format: A Practical Tutorial

## Table of Contents
1. [Introduction to Liberty Format](#introduction-to-liberty-format)
2. [Understanding .lib File Structure](#understanding-lib-file-structure)
3. [Working with Liberty Files](#working-with-liberty-files)
4. [Converting to JSON](#converting-to-json)
5. [JSON Schema Validation](#json-schema-validation)
6. [Generating Liberty from Verilog](#generating-liberty-from-verilog)
7. [Best Practices and Tools](#best-practices-and-tools)
8. [End-to-End Example: Verilog → Liberty → JSON → Validation](#end-to-end-example)

---

## Introduction to Liberty Format

The **Synopsys Liberty (.lib) format** is the industry-standard ASCII format for modeling semiconductor cell characteristics in Electronic Design Automation (EDA) tools. It provides timing, power, and signal integrity data for standard cells, macros, and I/O pads.

### Key Characteristics
- **Human-readable** text-based format
- Used by all major EDA vendors (Synopsys, Cadence, Siemens)
- Models cell behavior across PVT (Process, Voltage, Temperature) corners
- Compiled to binary `.db` format for tool use

### What Liberty Files Provide
- **Timing**: Cell delays and output transition times (using lookup tables)
- **Power**: Internal, leakage, and switching power consumption
- **Signal Integrity**: Noise and crosstalk immunity
- **Test**: Design-for-test (DFT) information

---

## Understanding .lib File Structure

### Basic Syntax Rules

```liberty
/* Comments use C-style syntax */
group_name (optional_name) {
    attribute_name : attribute_value ;

    subgroup_name (subgroup_params) {
        /* nested content */
        attribute_name : attribute_value ;
    }
}
```

### Complete Minimal Example

Here's a feature-rich example showing most critical Liberty elements:

```liberty
library(example_minimal) {
    /* Library Header */
    technology ("cmos") ;
    time_unit : "1ns" ;
    voltage_unit : "1V" ;
    current_unit : "1mA" ;
    capacitive_load_unit (1, "pf") ;
    leakage_power_unit : "1nW" ;
    default_fanout_load : 1.0 ;
    default_input_pin_cap : 0.5 ;
    delay_model : "table_lookup" ;

    /* Operating Conditions (PVT) */
    nom_process : 1.0 ;
    nom_temperature : 25.0 ;
    nom_voltage : 1.2 ;

    operating_conditions (typical) {
        process : 1.0 ;
        temperature : 25.0 ;
        voltage : 1.2 ;
        tree_type : "balanced_tree" ;
    }

    /* Lookup Table Templates */
    lu_table_template (delay_template_2x2) {
        variable_1 : "input_net_transition" ;
        variable_2 : "total_output_net_capacitance" ;
        index_1 ("0.1, 1.0") ;
        index_2 ("0.05, 0.5") ;
    }

    lu_table_template (power_template_1x1) {
        variable_1 : "input_net_transition" ;
        variable_2 : "total_output_net_capacitance" ;
        index_1 ("0.1") ;
        index_2 ("0.05") ;
    }

    lu_table_template (constraint_template_2x1) {
        variable_1 : "related_constraint" ;
        variable_2 : "related_pin_transition" ;
        index_1 ("0.1, 1.0") ;
        index_2 ("0.05") ;
    }

    /* Combinational Cell: 2-input AND gate */
    cell (AND2_X1) {
        area : 5.0 ;
        is_macro : false ;

        pin (A) {
            direction : input ;
            capacitance : 0.8 ;
            fanout_load : 1.0 ;
        }

        pin (B) {
            direction : input ;
            capacitance : 0.8 ;
            fanout_load : 1.0 ;
        }

        pin (Z) {
            direction : output ;
            function : "(A & B)" ;
            max_capacitance : 1.5 ;

            timing () {
                related_pin : "A" ;
                timing_sense : positive_unate ;

                cell_rise (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.12, 0.24", "0.38, 0.52") ;
                }

                rise_transition (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.09, 0.18", "0.70, 0.95") ;
                }

                cell_fall (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.10, 0.20", "0.32, 0.45") ;
                }

                fall_transition (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.08, 0.16", "0.65, 0.88") ;
                }
            }

            timing () {
                related_pin : "B" ;
                timing_sense : positive_unate ;

                cell_rise (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.14, 0.26", "0.40, 0.55") ;
                }

                rise_transition (delay_template_2x2) {
                    index_1 ("0.1, 1.0") ;
                    index_2 ("0.05, 0.5") ;
                    values ("0.10, 0.20", "0.72, 0.98") ;
                }
            }
        }

        /* Power Modeling */
        internal_power () {
            related_pin : "A" ;
            rise_power (power_template_1x1) { values ("0.05") ; }
            fall_power (power_template_1x1) { values ("0.04") ; }
        }

        leakage_power () {
            value : 0.002 ;
        }
    }

    /* Sequential Cell: D Flip-Flop */
    cell (DFF_X1) {
        area : 15.0 ;
        ff : "IQ" ;

        pin (CK) {
            direction : input ;
            clock : true ;
            capacitance : 0.7 ;
        }

        pin (D) {
            direction : input ;
            capacitance : 0.6 ;
        }

        pin (Q) {
            direction : output ;
            function : "IQ" ;

            timing () {
                related_pin : "CK" ;
                timing_type : "rising_edge" ;
                cell_rise (delay_template_2x2) {
                    values ("0.35, 0.62", "0.51, 0.78") ;
                }
                rise_transition (delay_template_2x2) {
                    values ("0.25, 0.45", "0.55, 0.82") ;
                }
            }
        }

        pin (QN) {
            direction : output ;
            function : "!IQ" ;

            timing () {
                related_pin : "CK" ;
                timing_type : "rising_edge" ;
                cell_fall (delay_template_2x2) {
                    values ("0.30, 0.55", "0.48, 0.72") ;
                }
                fall_transition (delay_template_2x2) {
                    values ("0.22, 0.40", "0.50, 0.76") ;
                }
            }
        }

        /* Timing Constraints */
        timing () {
            related_pin : "CK" ;
            timing_type : "setup_rising" ;
            rise_constraint (constraint_template_2x1) {
                values ("0.15, 0.22") ;
            }
        }

        timing () {
            related_pin : "CK" ;
            timing_type : "hold_rising" ;
            rise_constraint (constraint_template_2x1) {
                values ("0.05, 0.10") ;
            }
        }

        leakage_power () { value : 0.01 ; }
    }

    /* Combinational Cell: Inverter */
    cell (INV_X1) {
        area : 3.0 ;
        is_macro : false ;

        pin (A) {
            direction : input ;
            capacitance : 0.5 ;
        }

        pin (ZN) {
            direction : output ;
            function : "(!A)" ;
            max_capacitance : 2.0 ;

            timing () {
                related_pin : "A" ;
                timing_sense : negative_unate ;
                cell_rise (delay_template_2x2) {
                    values ("0.08, 0.18", "0.30, 0.42") ;
                }
                rise_transition (delay_template_2x2) {
                    values ("0.06, 0.14", "0.55, 0.78") ;
                }
                cell_fall (delay_template_2x2) {
                    values ("0.07, 0.16", "0.28, 0.38") ;
                }
                fall_transition (delay_template_2x2) {
                    values ("0.05, 0.12", "0.50, 0.72") ;
                }
            }
        }

        leakage_power () { value : 0.001 ; }
    }
}
```

Features demonstrated:
- **3 cell types**: combinational (AND2_X1, INV_X1) and sequential (DFF_X1)
- **Timing arcs**: multiple `timing()` groups per pin, multiple table types (cell_rise, rise_transition, cell_fall, fall_transition)
- **Power modeling**: internal_power with rise_power/fall_power, static leakage_power
- **Sequential**: `ff : "IQ"`, `clock : true`, timing constraints (setup/hold)
- **Lookup tables**: 2×2 (1D and 2D templates), multi-template references
- **Library header**: technology, units, nominal PVT operating conditions

---

## Working with Liberty Files

### Open Source Tools

Several open-source tools can parse and manipulate Liberty files:

| Tool | Language | Read | Write | Best For |
|------|----------|------|-------|----------|
| `liberty-parser` | Python | ✅ | ⚠️* | Scripting, analysis |
| `liberty-io` | Rust | ✅ | ✅ | Production, huge files |
| `libertyparse` | Rust | ✅ | ❌ | Memory-efficient parsing |
| `OpenSTA` | C++ | ✅ | ❌ | Static timing analysis |
| `convert-lib-to-json` (skill) | Python | ✅ | ✅† | Liberty ↔ JSON with schema validation |
| `lib-for-verilog` (skill) | Python | ❌ | ✅ | Verilog → Liberty generation via Yosys |

*Can format back to string but no dedicated writer API.
†Converts to JSON file; round-trip requires JSON-to-Liberty reconstruction.

### Python: Using liberty-parser

**Installation:**
```bash
pip install liberty-parser
```

**Basic Usage:**

```python
from liberty.parser import parse_liberty

# Parse a Liberty file
with open("your_library.lib", "r") as f:
    library = parse_liberty(f.read())

# Iterate through cells
for cell_group in library.get_groups('cell'):
    cell_name = cell_group.args[0]
    print(f"Cell: {cell_name}")

    # Examine pins
    for pin_group in cell_group.get_groups('pin'):
        pin_name = pin_group.args[0]

        if 'direction' in pin_group:
            print(f"  Pin {pin_name}: {pin_group['direction']}")

        # Extract timing tables as NumPy arrays
        timing = pin_group.get_groups('timing')
        if timing:
            # cell_rise is a SUBGROUP, not an attribute
            cr_groups = timing[0].get_groups('cell_rise')
            if cr_groups:
                # Values are inside the subgroup as an array
                delay_table = cr_groups[0].get_array('values')
                print(f"  Delay table shape: {delay_table.shape}")

# Modify attributes
library['time_unit'] = '1ps'  # Change time unit

# Write back to string
modified_lib = str(library)
with open("modified.lib", "w") as f:
    f.write(modified_lib)
```

> **API Note**: In `liberty-parser` v0.0.29, the `Group` class uses `group_name` (not `.name`), `attributes` is a **list** of `Attribute` objects (not a dict — each has `.name` and `.value`), and timing tables like `cell_rise` are **subgroups**, not direct attributes of the timing group. Access their values via `get_groups(name)[0].get_array('values')`.

### Rust: Using liberty-io

**Cargo.toml:**
```toml
[dependencies]
liberty-io = "0.1"
```

**Basic Usage:**
```rust
use liberty_io;
use std::fs::File;
use std::io::BufReader;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let f = File::open("library.lib")?;
    let mut buf = BufReader::new(f);

    // Parse library
    let library = liberty_io::read_liberty_bytes(&mut buf)?;

    // Access cells
    for group in &library.groups {
        if group.name == "cell" {
            println!("Cell: {}", group.arguments[0]);

            // Find pins
            for pin in &group.groups {
                if pin.name == "pin" {
                    println!("  Pin: {}", pin.arguments[0]);
                }
            }
        }
    }

    // Modify and write back
    library.groups.push(
        liberty_io::liberty::Group::new("comment", vec!["Modified by script"])
    );

    let output = File::create("modified.lib")?;
    liberty_io::write_liberty(&library, output)?;

    Ok(())
}
```

### C++: Using OpenSTA

OpenSTA provides a production-quality Liberty parser in C++:

```cpp
#include "liberty/LibertyReader.hh"
#include "liberty/LibertyVisitor.hh"

// Custom visitor to extract information
class MyLibertyVisitor : public Liberty::Visitor {
public:
    void visit(const Liberty::Group* group) override {
        if (group->name() == "cell") {
            std::cout << "Cell: " << group->argument(0) << std::endl;
        }
    }
};

int main() {
    // Parse Liberty file
    Liberty::Library* lib = Liberty::readLibertyFile("library.lib");

    if (lib) {
        // Traverse the parsed data
        MyLibertyVisitor visitor;
        lib->accept(&visitor);

        // Access attributes
        const auto& cells = lib->cells();
        for (auto* cell : cells) {
            std::cout << "Cell area: " << cell->area() << std::endl;
        }
    }

    return 0;
}
```

---

## Converting to JSON

### Method 1: Using libertymetric (Dedicated Tool)

```bash
pip install libertymetric
```

```python
from libertymetric.classLiberty import liberty as lutil

# Convert Liberty to JSON
lnode = lutil.read_lib('your_library.lib')
lutil.dump_json(lnode, out='output.json')

# Convert JSON back to Liberty
lnode = lutil.load_json('output.json')
lutil.write_lib('reconstructed.lib', lnode)
```

### Method 2: Custom JSON Serialization with liberty-parser

This method recursively converts the Liberty group tree into a JSON structure. Every group becomes a JSON object with `type`, `args`, `attributes`, and optional `groups`.

```python
import json
from liberty.parser import parse_liberty
from liberty.types import EscapedString

def _json_safe(value):
    """Convert liberty-parser types (EscapedString, NumPy arrays) to JSON-safe types."""
    if isinstance(value, EscapedString):
        return value.value.strip('"')
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "tolist"):  # NumPy array
        return value.tolist()
    return value

def liberty_to_dict(group):
    """Recursively convert a Liberty Group to a dictionary."""
    result = {
        "type": group.group_name,  # NOT group.name
        "args": list(group.args),
    }
    # attributes is a LIST of Attribute objects (not a dict)
    attrs = {}
    for a in group.attributes:
        attrs[a.name] = _json_safe(a.value)
    if attrs:
        result["attributes"] = attrs

    if group.groups:
        result["groups"] = [liberty_to_dict(g) for g in group.groups]

    return result

# Parse and convert
with open("library.lib", "r") as f:
    library = parse_liberty(f.read())

json_data = liberty_to_dict(library)

with open("library.json", "w") as f:
    json.dump(json_data, f, indent=2)
```

The output JSON follows this recursive structure:
```json
{
  "type": "library",
  "args": ["library_name"],
  "attributes": { "time_unit": "1ns", ... },
  "groups": [
    {
      "type": "cell",
      "args": ["AND2_X1"],
      "attributes": { "area": 5.0, ... },
      "groups": [
        {
          "type": "pin",
          "args": ["Z"],
          "attributes": { "direction": "output", "function": "(A & B)" },
          "groups": [
            {
              "type": "timing",
              "args": [],
              "attributes": { "related_pin": "A", "timing_sense": "positive_unate" },
              "groups": [
                {
                  "type": "cell_rise",
                  "args": ["delay_template_2x2"],
                  "attributes": { "values": ["0.12, 0.24", "0.38, 0.52"] }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Method 3: Selective JSON Extraction

Extract specific data for analysis instead of dumping the entire recursive structure:

```python
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

def extract_timing_data(lib_file):
    with open(lib_file, "r") as f:
        library = parse_liberty(f.read())

    timing_data = {}

    for cell in library.get_groups('cell'):
        cell_name = cell.args[0]
        timing_data[cell_name] = {
            "area": float(cell.get_attribute('area', 0)),
            "is_sequential": 'ff' in cell,
            "pins": {}
        }

        for pin in cell.get_groups('pin'):
            pin_name = pin.args[0]
            pin_info = {
                "direction": _json_safe(pin.get_attribute('direction', 'unknown')),
                "capacitance": float(pin.get_attribute('capacitance', 0))
            }

            # Extract timing arcs
            arcs = []
            for timing in pin.get_groups('timing'):
                arc = {
                    "related_pin": _json_safe(timing.get_attribute('related_pin', 'unknown')),
                    "timing_sense": _json_safe(timing.get_attribute('timing_sense', 'unknown')),
                    "timing_type": _json_safe(timing.get_attribute('timing_type', 'unknown')),
                }
                # Extract delay values from subgroups
                for table_name in ["cell_rise", "cell_fall", "rise_transition", "fall_transition"]:
                    tbl_grp = timing.get_groups(table_name)  # subgroup check
                    if tbl_grp:
                        table = tbl_grp[0].get_array('values')  # 'values' attribute inside
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
        leakage = cell.get_groups('leakage_power')
        if leakage:
            timing_data[cell_name]["leakage_power"] = float(
                leakage[0].get_attribute('value', 0)
            )

    return timing_data

data = extract_timing_data("library.lib")
with open("timing_analysis.json", "w") as f:
    json.dump(data, f, indent=2)
```

### Method 4: Using the convert-lib-to-json Agent Skill

The `convert-lib-to-json` agent skill wraps Methods 2 and 3 into a single command-line tool with automatic schema validation:

```bash
# Convert and validate in one step
python /path/to/convert-lib-to-json/convert_lib_to_json.py library.lib output.json

# Or using the skill from task context
# task(load_skills=["convert-lib-to-json"], prompt="Convert my lib file")
```

The skill:
- Parses the .lib with `liberty-parser`
- Converts to Method 2 JSON format
- Prints a human-readable cell summary
- Validates against the bundled JSON schema
- Returns exit code 0 on success, 2 on validation failure

---

## JSON Schema Validation

A comprehensive **JSON Schema (Draft-07)** for the Method 2 conversion format is available at `liberty_json_schema.json`. The schema covers:

| Group Type | Coverage |
|---|---|
| `library` (root) | technology, time_unit, voltage_unit, delay_model, nominal PVT |
| `cell` | area, is_macro, ff, dont_use, dont_touch + arbitrary params |
| `pin` | direction, capacitance, clock, function, max_capacitance, fanout_load |
| `timing` | related_pin, timing_sense, timing_type |
| `cell_rise` / `cell_fall` / `rise_transition` / `fall_transition` | index_1, index_2, values |
| `rise_constraint` / `fall_constraint` | values |
| `internal_power` | related_pin → rise_power / fall_power tables |
| `leakage_power` | value |
| `lu_table_template` | variable_1, variable_2, variable_3, index_1/2/3 |
| `operating_conditions` | process, temperature, voltage, tree_type |

### Schema Design

- **Recursive**: `any_group` base type with `anyOf` dispatching to specific group types
- **Permissive**: unknown group types and attributes fall through to a generic `any_group` catch-all via `additionalProperties`
- **Typed attributes**: `attribute_value` covers strings, numbers, booleans, and arrays thereof
- **Specific constraints**: known Liberty group types have validated `required` fields and `enum` values where appropriate

### Validation Usage

```python
import json
import jsonschema

with open("library.json") as f:
    data = json.load(f)
with open("liberty_json_schema.json") as f:
    schema = json.load(f)

try:
    jsonschema.validate(instance=data, schema=schema)
    print("VALID")
except jsonschema.ValidationError as e:
    print(f"INVALID: {e.message}")
```

---

## Generating Liberty from Verilog

The `lib-for-verilog` agent skill generates an artificial Liberty .lib file from a Verilog RTL source by synthesizing it with **Yosys** and extracting all technology primitive cell types.

### Workflow

```
Verilog (.v)
    │
    ▼  Yosys synthesis (proc → opt → techmap → clean)
    │
    ▼  Temporary Yosys JSON netlist
    │
    ▼  Cell type extraction (100+ known cell types mapped)
    │
    ▼  Liberty .lib generation
         ├── Library header (technology, units, PVT)
         ├── Operating conditions
         ├── Lookup table template (delay_template_2x2)
         └── Cells per primitive type
              ├── area, ff, parameters
              ├── pins (direction, clock flag, function)
              ├── timing stubs (cell_rise/fall, rise/fall_transition)
              └── leakage power
```

### Usage

```bash
python /path/to/lib-for-verilog/lib_for_verilog.py my_design.v \
    --top top_module \
    --output cells.lib \
    --json --validate
```

This produces:
- `cells.lib` — Liberty library with mapped primitive cells
- `cells.json` — JSON conversion (via `convert-lib-to-json` internals)
- Schema validation of the JSON output

### Extracted Cell Types

The script knows port directions for **100+ Yosys cell types** across two categories:

**Pre-techmap** (before `techmap`): `$add`, `$mul`, `$sub`, `$mux`, `$pmux`, `$eq`, `$lt`, `$shr`, `$dff`, `$adff`, etc.

**Post-techmap technology primitives** (after `techmap`): `$_AND_`, `$_OR_`, `$_XOR_`, `$_NOT_`, `$_MUX_`, `$_DFF_P_` (posedge DFF), `$_DFF_N_` (negedge DFF), `$_DFF_PN0_` (posedge with async reset), `$_DLATCH_P_`, etc.

### Cell Name Sanitization

Liberty identifiers cannot contain `$`. The script converts:
- `$` → `_dollar_` (e.g., `$_AND_` → `_dollar__AND_`)
- Leading `\` stripped (Yosys escape character for `\$memrd`, etc.)

### Practical Example: 32-Tap FIR Filter

```bash
# A 32-tap FIR filter after Yosys synthesis produces:
python lib_for_verilog.py fir_filter.v --top fir_filter --json --validate
```
Yields 7 primitive cell types:
| Liberty Cell | Yosys Primitive | Function | Pins |
|---|---|---|---|
| `_dollar__AND_` | `$_AND_` | AND | A, B → Y |
| `_dollar__DFF_PN0_` | `$_DFF_PN0_` | posedge DFF, async neg reset | C, D, R → Q |
| `_dollar__DFF_P_` | `$_DFF_P_` | posedge DFF | C, D → Q |
| `_dollar__MUX_` | `$_MUX_` | 2:1 mux | A, B, S → Y |
| `_dollar__NOT_` | `$_NOT_` | inverter | A → Y |
| `_dollar__OR_` | `$_OR_` | OR | A, B → Y |
| `_dollar__XOR_` | `$_XOR_` | XOR | A, B → Y |

---

## Best Practices and Tools

### Compiling .lib to .db (Synopsys)

For production use, compile Liberty files to binary `.db` format:

```bash
# Using Library Compiler
lc_shell
lc_shell> read_lib my_library.lib
lc_shell> write_lib -format db my_library -output my_library.db
lc_shell> exit

# Use in Design Compiler
# dc_shell> set target_library "my_library.db"
```

### Validation Approaches

Since no official schema exists for Liberty, validation happens through tools:

1. **Synopsys Library Compiler** - Authoritative validator (commercial)
2. **Open source parsers** - Will error on invalid syntax
3. **JSON Schema** (`liberty_json_schema.json`) - Validates the JSON conversion against a structured Draft-07 schema covering all known Liberty group types
4. **Liberty Reference Manual** - Official specification document

### Common Pitfalls

| Issue | Solution |
|-------|----------|
| Missing lookup table templates | Define `lu_table_template` before use |
| Inconsistent units | Check `time_unit`, `capacitive_load_unit` settings |
| Incorrect function syntax | Use Liberty expression syntax: `"(A & B)"`, `"(!A)"` |
| PVT corner mismatches | Ensure operating conditions match library data |
| `AttributeError: 'Group' object has no attribute 'name'` | Use `.group_name` instead of `.name` (liberty-parser v0.0.29 API) |
| `dict(group.attributes)` fails | `attributes` is a **list** of `Attribute` objects — iterate and access `.name` / `.value` |
| Timing tables return empty | `cell_rise` etc. are **subgroups**, not attributes — use `get_groups("cell_rise")` then `.get_array("values")` |
| `EscapedString` not JSON serializable | Convert via `.value.strip('"')` (see `_json_safe` helper above) |
| `$` in cell names (Liberty syntax error) | Replace with `_dollar_` prefix — `$` is not a valid Liberty identifier character |
| Yosys `dfflibmap` cannot map cells | Post-techmap liberty cells need specific naming conventions in Yosys 0.9; use `read_liberty -lib` for library registration instead |
| `opt` pass after techmap zeroes design | For cell type extraction, use `techmap; clean` instead of `techmap; opt` — the aggression of `opt` can remove all cells in complex designs |
| Yosys rejects procedural `for` loops with `integer` indices | Pre-unroll the loop or declare the loop variable with `genvar` for generate loops |

### Resources

- **Liberty Reference Manual** - Available from Synopsys (hundreds of pages)
- **Liberty Technical Advisory Board (LTAB)** - Industry governance body
- **Open-source tools** - See table in "Working with Liberty Files" section
- **liberty-parser** - https://pypi.org/project/liberty-parser/
- **liberty-io** - https://crates.io/crates/liberty-io
- **OpenSTA** - https://github.com/The-OpenROAD-Project/OpenSTA

### When to Use Each Tool

| Use Case | Recommended Tool |
|----------|------------------|
| Quick scripting and analysis | `liberty-parser` (Python) |
| Converting to/from JSON | `convert-lib-to-json` agent skill (Python, schema-validated) |
| Processing huge libraries (GB+) | `liberty-io` (Rust) |
| Production static timing analysis | OpenSTA (C++) |
| Writing/modifying Liberty files | `liberty-io` (Rust) |
| Generating Liberty from RTL/Verilog | `lib-for-verilog` agent skill (Python + Yosys) |
| Schema validation of Liberty JSON | `liberty_json_schema.json` + `jsonschema` |
| Liberty ↔ JSON round-trip | `libertymetric` (Python) |

---

## End-to-End Example

The complete pipeline from Verilog source to validated Liberty JSON:

```bash
# Step 1: Generate Liberty from Verilog
python lib_for_verilog.py my_design.v --top my_top --output my_design.lib

# Step 2: Convert to JSON and validate
python convert_lib_to_json.py my_design.lib my_design_converted.json

# Step 3 (programmatic): Use in Python
from liberty.parser import parse_liberty
with open("my_design.lib") as f:
    lib = parse_liberty(f.read())

for cell in lib.get_groups("cell"):
    print(f"{cell.args[0]}: {len(cell.get_groups('pin'))} pins")
```

This tutorial project includes the following working example files:

| File | Description |
|---|---|
| `example_minimal.lib` | Hand-crafted Liberty library with 3 cells |
| `tutorial_parse_lib.py` | Basic parsing: iterate cells, pins, extract timing tables as NumPy arrays |
| `tutorial_convert_json.py` | JSON conversion (Methods 1–3) |
| `tutorial_extract_timing.py` | Detailed timing/power extraction with statistics |
| `liberty_json_schema.json` | JSON Schema for Liberty conversion (Draft-07) |
| `yosys_to_liberty.py` | Yosys JSON → Liberty .lib converter |
| `yosys_sphere.lib` | Generated Liberty from a Yosys netlist (20 cells) |
| `yosys_sphere_tech.lib` | Generated Liberty from post-techmap primitives (8 cells) |
| `fir_filter.lib` | Generated Liberty from a 32-tap FIR filter (7 cells) |

---

## Summary

The Synopsys Liberty format is a powerful, human-readable standard for semiconductor library characterization. While it lacks formal machine-readable schema validation, the ecosystem of open-source tools has matured significantly:

- **Python** users have excellent options with `liberty-parser` and `libertymetric`
- **Rust** provides high-performance parsing with `liberty-io` and writer support
- **C++** production applications can leverage OpenSTA's parser
- **JSON conversion** with schema validation is provided by the `convert-lib-to-json` skill and `liberty_json_schema.json`
- **Verilog → Liberty generation** is possible via Yosys synthesis and the `lib-for-verilog` skill
- **JSON Schema (Draft-07)** provides the first structured validation for Liberty-derived JSON, covering all known group types

Understanding this format is essential for anyone working with ASIC design flows, static timing analysis, or power estimation tools.
