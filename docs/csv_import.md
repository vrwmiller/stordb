# CSV Import Script for stordb

## Overview
The CSV import script (`scripts/import_csv.py`) allows you to bulk import device secrets into the stordb database from a CSV file. This is useful for initial data migration or one-time imports.

## Usage
Run the script from the project root or the `scripts/` directory:

```bash
python scripts/import_csv.py scripts/example.csv
```

## CSV Format
The input CSV file should have the following columns (case-insensitive):

- `owner`: Device owner
- `device name`: Name of the device
- `mac address`: MAC address of the device
- `description`: Description or notes
- Additional columns are optional and ignored by default

Example (`scripts/example.csv`):
```csv
owner,device name,mac address,description,location
Alice,Router,AA:BB:CC:DD:EE:01,Main office router,Office
Bob,Switch,AA:BB:CC:DD:EE:02,Core switch,Data Center
Carol,Access Point,AA:BB:CC:DD:EE:03,Guest WiFi AP,Lobby
```

## How It Works
- The script reads the CSV file and maps columns to the required fields.
- For each row, it calls the `add_secret` function from `stordb.py` to insert the record into the database.
- Only the required columns are used; extra columns are ignored.
- The database is initialized automatically if needed.

## Error Handling & Validation
- If required columns are missing, the script will exit with an error.
- If the CSV or JSON file is malformed, an error will be logged and displayed; the application will not crash.
- All imported records are validated for required fields before insertion.
- See edge case tests in `tests/test_edge_cases.py` for coverage of malformed input scenarios.

## Customization
- You can modify the script to handle additional fields or custom logic as needed.

## See Also
- [`scripts/import_csv.py`](../scripts/import_csv.py): The import script
- [`scripts/example.csv`](../scripts/example.csv): Example input file
- [`stordb.py`](../stordb.py): Main database logic
