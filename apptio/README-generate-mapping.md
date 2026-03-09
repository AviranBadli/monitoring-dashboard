# GPU Type Mapping Generator

## Overview

The `generate-gpu-type-mapping.py` script converts GPU instance data from CSV format into an Apptio business mapping JSON file.

## Usage

### Basic Usage (Default Paths)

```bash
python3 generate-gpu-type-mapping.py
```

This uses the default file paths:
- Input: `GPU-types-by-cloud-provider-costs.csv`
- Output: `apptio-business-mappings-gpu-type.json`

### Custom File Paths

```bash
# Specify both input and output
python3 generate-gpu-type-mapping.py --csv /path/to/input.csv --json /path/to/output.json

# Specify only input CSV
python3 generate-gpu-type-mapping.py --csv my-data.csv

# Specify only output JSON
python3 generate-gpu-type-mapping.py --json custom-output.json
```

### Get Help

```bash
python3 generate-gpu-type-mapping.py --help
```

## Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--csv` | Path to input CSV file | `GPU-types-by-cloud-provider-costs.csv` |
| `--json` | Path to output JSON file | `apptio-business-mappings-gpu-type.json` |

## Input CSV Format

The script expects a CSV file with these columns:
- **Instance Type** (Column A): The cloud provider instance type name
- **GPU_Type** (Column H): The formatted GPU specification string

Example row:
```
Instance Type: p5e.48xlarge
GPU_Type: NVIDIA H200 141 SXM5 x 8
```

## Output JSON Format

The script generates a JSON file with this structure:

```json
{
  "name": "GPU_Type",
  "defaultValue": "No GPU",
  "statements": [
    {
      "matchExpression": "DIMENSION['instance_type'] == 'p5e.48xlarge'",
      "valueExpression": "'NVIDIA H200 141 SXM5 x 8'"
    }
  ]
}
```

## Examples

### Example 1: Default Usage
```bash
python3 generate-gpu-type-mapping.py
```
Output:
```
Reading CSV file: GPU-types-by-cloud-provider-costs.csv
Writing JSON file: apptio-business-mappings-gpu-type.json
============================================================
Conversion Complete!
============================================================
Total rows processed:      156
Rows with GPU types:       156
JSON statements created:   156
```

### Example 2: Custom Paths
```bash
python3 generate-gpu-type-mapping.py \
  --csv data/gpu-instances.csv \
  --json output/mappings.json
```

### Example 3: Absolute Paths
```bash
python3 generate-gpu-type-mapping.py \
  --csv /home/user/data/gpu-types.csv \
  --json /home/user/output/apptio-mapping.json
```

## Exit Codes

- `0`: Success
- `1`: Error (file not found, missing columns, etc.)

## Error Handling

The script validates:
- Input CSV file exists
- Required columns are present in CSV
- File permissions for reading/writing

Common errors:
```
Error: CSV file not found: /path/to/file.csv
Error: Required column not found in CSV: 'GPU_Type'
Error: Permission denied: /path/to/output.json
```

## Notes

- The script only includes rows that have a non-empty `GPU_Type` value
- Paths can be relative or absolute
- The script creates the output file (and overwrites if it exists)
- All 156 GPU instance types from AWS, Azure, GCP, and IBM are supported

## Maintenance

To update the mapping:
1. Update the CSV file with new instance types
2. Run the script to regenerate the JSON
3. Verify the output with sample statements shown in the console

---

Generated: March 2026
