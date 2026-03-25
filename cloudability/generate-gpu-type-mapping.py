#!/usr/bin/env python3
"""
Generate Apptio business mapping JSON from GPU types CSV

This script reads the GPU-types-by-cloud-provider-costs.csv file and generates
a JSON mapping file (apptio-business-mappings-gpu-type.json) that can be used
for Apptio business logic rules.

Each row in the CSV becomes a statement object with:
- matchExpression: checks if instance_type matches the Instance Type column (A)
- valueExpression: concatenates GPU Type (E) + GPU Memory (F) + GPU Variant (G) + GPU Count (D)

Usage:
    python3 generate-gpu-type-mapping.py --csv CSV_FILE [-o OUTPUT_FILE]

Arguments:
    --csv     Path to input CSV file (required)
    -o        Path to output JSON file (default: output to stdout)

Examples:
    # Output to stdout
    python3 generate-gpu-type-mapping.py --csv data.csv

    # Output to file
    python3 generate-gpu-type-mapping.py --csv data.csv -o output.json

    # Specify full paths
    python3 generate-gpu-type-mapping.py --csv /path/to/data.csv -o /path/to/output.json
"""

import csv
import json
import os
import sys
import argparse


def generate_gpu_type_mapping(csv_file, json_file=None):
    """
    Generate Apptio GPU type mapping JSON from CSV file.

    Args:
        csv_file: Path to input CSV file
        json_file: Path to output JSON file (None = stdout)
    """
    # Validate input file exists
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        return False

    # Initialize JSON structure
    json_data = {"name": "GPU_Type", "defaultValue": "No GPU", "statements": []}

    # Read the CSV and create statements
    # Group by valueExpression so each unique GPU config appears only once
    from collections import OrderedDict

    value_to_instances = OrderedDict()
    rows_processed = 0
    rows_with_gpu = 0

    # Print to stderr if outputting JSON to stdout, otherwise to stdout
    output = sys.stderr if not json_file else sys.stdout
    print(f"Reading CSV file: {csv_file}", file=output)

    # Required CSV columns
    required_columns = [
        "Instance Type",
        "Instance Family",
        "Cloud Provider",
        "GPU Count",
        "GPU Type",
        "GPU Memory (GB)",
        "GPU Variant",
    ]

    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)

            # Validate that all required columns are present
            if reader.fieldnames is None:
                print(
                    f"Error: CSV file appears to be empty or invalid", file=sys.stderr
                )
                return False

            missing_columns = [
                col for col in required_columns if col not in reader.fieldnames
            ]
            if missing_columns:
                print(f"Error: CSV file is missing required columns:", file=sys.stderr)
                for col in missing_columns:
                    print(f"  - {col}", file=sys.stderr)
                print(
                    f"\nFound columns: {', '.join(reader.fieldnames)}", file=sys.stderr
                )
                return False

            for row in reader:
                rows_processed += 1
                instance_type = row["Instance Type"]  # Column A
                gpu_type = row["GPU Type"]  # Column E
                gpu_memory = row["GPU Memory (GB)"]  # Column F
                gpu_variant = row["GPU Variant"]  # Column G
                gpu_count = row["GPU Count"]  # Column D

                # Only add if GPU Type has a value
                if gpu_type and gpu_type.strip():
                    # Build the value expression from columns E, F, G, and D
                    # Format: "GPU Type GPU_Memory GPU_Variant x GPU_Count"
                    parts = []

                    # Add GPU Type
                    parts.append(gpu_type.strip())

                    # Add GPU Memory if present
                    if gpu_memory and gpu_memory.strip():
                        parts.append(gpu_memory.strip())

                    # Add GPU Variant if present
                    if gpu_variant and gpu_variant.strip():
                        parts.append(gpu_variant.strip())

                    # Join parts and add GPU count
                    gpu_value = " ".join(parts)

                    # Add count if present
                    if gpu_count and gpu_count.strip():
                        gpu_value += f" x {gpu_count.strip()}"

                    value_expr = f"'{gpu_value}'"
                    match_expr = f"DIMENSION['instance_type'] == '{instance_type}'"

                    if value_expr not in value_to_instances:
                        value_to_instances[value_expr] = []
                    value_to_instances[value_expr].append(match_expr)
                    rows_with_gpu += 1

        # Build statements with combined match expressions
        statements = []
        for value_expr, match_exprs in value_to_instances.items():
            statement = {
                "matchExpression": " || ".join(match_exprs),
                "valueExpression": value_expr,
            }
            statements.append(statement)
    except KeyError as e:
        print(f"Error: Required column not found in CSV: {e}")
        return False
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False

    # Update the JSON data with all statements
    json_data["statements"] = statements

    # Write the JSON to file or stdout
    try:
        if json_file:
            print(f"Writing JSON file: {json_file}")
            with open(json_file, "w") as f:
                json.dump(json_data, f, indent=2)
        else:
            # Output to stdout
            json.dump(json_data, sys.stdout, indent=2)
            sys.stdout.write("\n")
            return True  # Skip summary output when writing to stdout
    except Exception as e:
        print(f"Error writing JSON: {e}", file=sys.stderr if not json_file else None)
        return False

    # Print summary (only when writing to file)
    if json_file:
        print(f"\n{'='*60}")
        print(f"Conversion Complete!")
        print(f"{'='*60}")
        print(f"Total rows processed:      {rows_processed}")
        print(f"Rows with GPU types:       {rows_with_gpu}")
        print(f"JSON statements created:   {len(statements)}")
        print(f"Output file:               {json_file}")
        print(f"{'='*60}")

    # Show sample statements (only when writing to file)
    if json_file and statements:
        print(f"\nSample statements (first 3):")
        for i, stmt in enumerate(statements[:3], 1):
            print(f"\n{i}. Match: {stmt['matchExpression']}")
            print(f"   Value: {stmt['valueExpression']}")

        print(f"\nSample statements (last 3):")
        for i, stmt in enumerate(statements[-3:], len(statements) - 2):
            print(f"\n{i}. Match: {stmt['matchExpression']}")
            print(f"   Value: {stmt['valueExpression']}")

    return True


def main():
    """Parse command-line arguments and run the conversion."""
    # Get script directory for default paths
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Generate Apptio business mapping JSON from GPU types CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Output to stdout
  %(prog)s --csv data.csv

  # Output to file
  %(prog)s --csv data.csv -o output.json

  # Specify full paths
  %(prog)s --csv /path/to/data.csv -o /path/to/output.json
        """,
    )

    parser.add_argument(
        "--csv",
        required=True,
        help="Path to input CSV file (required)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to output JSON file (default: output to stdout)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Run the conversion
    success = generate_gpu_type_mapping(args.csv, args.output)

    # Exit with appropriate status code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
