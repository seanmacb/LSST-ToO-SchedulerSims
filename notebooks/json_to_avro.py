#!/usr/bin/env python3

import json
import fastavro
import sys
from pathlib import Path

def json_to_avro(json_path, avro_path, avro_schema):
    """Convert a JSON file to AVRO using a provided schema."""
    # Load JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Handle both single-record and multi-record files
    if isinstance(data, dict):
        records = [data]
    elif isinstance(data, list):
        records = data
    else:
        raise ValueError("Unsupported JSON structure")

    # Write to AVRO
    with open(avro_path, 'wb') as out:
        fastavro.writer(out, avro_schema, records)
    print(f"AVRO file written to {avro_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python json_to_avro.py input.json output.avro schema.avsc")
        sys.exit(1)

    json_file = Path(sys.argv[1])
    avro_file = Path(sys.argv[2])
    schema_file = Path(sys.argv[3])

    with open(schema_file, 'r') as f:
        schema = json.load(f)

    json_to_avro(json_file, avro_file, schema)