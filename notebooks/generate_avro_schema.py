#!/usr/bin/env python3

import json
import sys
from pathlib import Path

# Mapping from Python types to Avro types
TYPE_MAP = {
    str: "string",
    int: "int",
    float: "float",
    bool: "boolean",
    type(None): "null"
}

def infer_avro_type(value):
    """Infer Avro type from a Python value."""
    py_type = type(value)
    if py_type in TYPE_MAP:
        return TYPE_MAP[py_type]
    elif isinstance(value, list):
        if len(value) == 0:
            return {"type": "array", "items": "string"}  # default for empty
        item_type = infer_avro_type(value[0])
        return {"type": "array", "items": item_type}
    elif isinstance(value, dict):
        return {"type": "record",
                "name": "NestedRecord",
                "fields": infer_fields(value)}
    else:
        return "string"  # fallback

def infer_fields(record):
    """Generate field definitions for a single JSON object."""
    fields = []
    for key, val in record.items():
        avro_type = infer_avro_type(val)

        # Handle nulls as unions (e.g., ["null", "int"])
        if isinstance(val, list) and val == []:
            avro_type = {"type": "array", "items": "string"}
        elif val is None:
            avro_type = ["null", "string"]  # default to nullable string

        elif isinstance(avro_type, str):
            if val is None:
                avro_type = ["null", avro_type]
        elif isinstance(avro_type, dict):
            if val is None:
                avro_type = ["null", avro_type]

        fields.append({
            "name": key,
            "type": avro_type
        })
    return fields

def generate_avro_schema(json_file, output_file, record_name="AutoRecord"):
    with open(json_file, 'r') as f:
        data = json.load(f)

    if isinstance(data, list):
        example = data[0]
    elif isinstance(data, dict):
        example = data
    else:
        raise ValueError("Unsupported JSON structure")

    schema = {
        "type": "record",
        "name": record_name,
        "fields": infer_fields(example)
    }

    with open(output_file, 'w') as f:
        json.dump(schema, f, indent=4)
    print(f"Avro schema written to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_avro_schema.py input.json output.avsc")
        sys.exit(1)

    input_json = Path(sys.argv[1])
    output_avsc = Path(sys.argv[2])
    generate_avro_schema(input_json, output_avsc)