# GPU Type Mapping Generator

## Overview

The `generate-gpu-type-mapping.py` script converts GPU instance data from CSV format into an Apptio business mapping JSON file.

## Usage

### Basic Usage (Default Paths)

```bash
python3 generate-gpu-type-mapping.py --csv <input file in CSV> [-o <output file name>]
```

This uses the default file paths:
- Input: `GPU-types-by-cloud-provider-costs.csv`
- Output: `apptio-business-mappings-gpu-type.json`

### Custom File Paths

```bash
# Specify both input and output
python3 generate-gpu-type-mapping.py --csv /path/to/input.csv -o /path/to/output.json



## Input CSV Format

See [GPU-types-by-cloud-provider](./GPU-types-by-cloud-provider.csv) for an example.


---

Generated: March 2026
