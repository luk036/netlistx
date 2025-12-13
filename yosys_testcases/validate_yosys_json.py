import json
from jsonschema import validate

# Load schema and data
with open("yosys_schema.json") as f:
    schema = json.load(f)
with open("sphere_netlist.json") as f:
    data = json.load(f)

# Validate
validate(instance=data, schema=schema)
