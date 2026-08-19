#!/usr/bin/env python3
"""
Validate a JSON file produced by an agent against its schema.

Usage:
    python3 scripts/validate_schema.py <schema_file> <json_file>

Exit codes:
    0 -> valid   (prints "SCHEMA_OK")
    1 -> invalid (prints "SCHEMA_INVALID: <reason>")
    2 -> usage / file error
"""
import json
import sys

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("SCHEMA_ERROR: the 'jsonschema' package is required (pip install jsonschema)")
    sys.exit(2)


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: validate_schema.py <schema_file> <json_file>")
        sys.exit(2)

    schema_path, data_path = sys.argv[1], sys.argv[2]

    try:
        with open(schema_path) as f:
            schema = json.load(f)
        with open(data_path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"SCHEMA_ERROR: could not read/parse input: {e}")
        sys.exit(2)

    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        print(f"SCHEMA_INVALID: {e.message}")
        sys.exit(1)

    print("SCHEMA_OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
