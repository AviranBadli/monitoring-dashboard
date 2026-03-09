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
    python3 generate-gpu-type-mapping.py [--csv CSV_FILE] [--json JSON_FILE]

Arguments:
    --csv     Path to input CSV file (default: GPU-types-by-cloud-provider-costs.csv)
    --json    Path to output JSON file (default: apptio-business-mappings-gpu-type.json)

Examples:
    # Use default file paths
    python3 generate-gpu-type-mapping.py

    # Specify custom paths
    python3 generate-gpu-type-mapping.py --csv /path/to/data.csv --json /path/to/output.json

    # Specify only CSV input
    python3 generate-gpu-type-mapping.py --csv my-gpu-data.csv
"""

import csv
import json
import os
import argparse


def generate_gpu_type_mapping(csv_file, json_file):
    """
    Generate Apptio GPU type mapping JSON from CSV file.

    Args:
        csv_file: Path to input CSV file
        json_file: Path to output JSON file
    """
    # Validate input file exists
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        return False

    # Initialize JSON structure
    json_data = {"name": "GPU_Type", "defaultValue": "No GPU", "statements": []}

    # Read the CSV and create statements
    statements = []
    rows_processed = 0
    rows_with_gpu = 0

    print(f"Reading CSV file: {csv_file}")

    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
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
                        parts.append(" x ")
                        gpu_value += f" x {gpu_count.strip()}"

                    statement = {
                        "matchExpression": f"DIMENSION['instance_type'] == '{instance_type}'",
                        "valueExpression": f"'{gpu_value}'",
                    }
                    statements.append(statement)
                    rows_with_gpu += 1
    except KeyError as e:
        print(f"Error: Required column not found in CSV: {e}")
        return False
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False

    # Update the JSON data with all statements
    json_data["statements"] = statements

    # Write the updated JSON to file
    print(f"Writing JSON file: {json_file}")
    try:
        with open(json_file, "w") as f:
            json.dump(json_data, f, indent=2)
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        return False

    # Print summary
    print(f"\n{'='*60}")
    print(f"Conversion Complete!")
    print(f"{'='*60}")
    print(f"Total rows processed:      {rows_processed}")
    print(f"Rows with GPU types:       {rows_with_gpu}")
    print(f"JSON statements created:   {len(statements)}")
    print(f"Output file:               {json_file}")
    print(f"{'='*60}")

    # Show sample statements
    if statements:
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
  # Use default file paths
  %(prog)s
  
  # Specify custom paths
  %(prog)s --csv /path/to/data.csv --json /path/to/output.json
  
  # Specify only CSV input
  %(prog)s --csv my-gpu-data.csv
        """,
    )

    parser.add_argument(
        "--csv",
        default=os.path.join(script_dir, "GPU-types-by-cloud-provider-costs.csv"),
        help="Path to input CSV file (default: GPU-types-by-cloud-provider-costs.csv in script directory)",
    )

    parser.add_argument(
        "--json",
        default=os.path.join(script_dir, "apptio-business-mappings-gpu-type.json"),
        help="Path to output JSON file (default: apptio-business-mappings-gpu-type.json in script directory)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Run the conversion
    success = generate_gpu_type_mapping(args.csv, args.json)

    # Exit with appropriate status code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
