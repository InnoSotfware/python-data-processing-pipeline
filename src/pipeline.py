
import csv
import json
import logging
import re
import sys
from pathlib import Path
from datetime import date, datetime
from urllib.request import Request, urlopen


# -------------------------------------------------
# PROJECT LOCATION
# -------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent


# -------------------------------------------------
# LOAD CONFIGURATION
# -------------------------------------------------

def load_config():
    config_path = ROOT / "config.json"

    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


# -------------------------------------------------
# SET UP LOGGING
# -------------------------------------------------

def setup_logging(config):
    log_path = ROOT / config["logging"]["file"]
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(
            logging,
            config["logging"]["level"].upper(),
            logging.INFO
        ),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )


# -------------------------------------------------
# READ CSV DATA
# -------------------------------------------------

def read_csv_file(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV file has no column headings.")

        return list(reader)


# -------------------------------------------------
# READ JSON DATA
# -------------------------------------------------

def read_json_file(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        data = data.get("data", data.get("results", [data]))

    if not isinstance(data, list):
        raise ValueError("JSON data must contain a list of records.")

    return data


# -------------------------------------------------
# READ API DATA
# -------------------------------------------------

def read_api_data(source):
    request = Request(
        source["url"],
        headers={"User-Agent": "PythonDataPipeline/1.0"}
    )

    with urlopen(
        request,
        timeout=source.get("timeout", 20)
    ) as response:

        data = json.loads(response.read().decode("utf-8"))

    if isinstance(data, dict):
        data = data.get(
            source.get("records_key", "data"),
            data.get("results", [data])
        )

    if not isinstance(data, list):
        raise ValueError("API response must contain a list of records.")

    return data


# -------------------------------------------------
# SELECT DATA SOURCE
# -------------------------------------------------

def read_source(config):
    source = config["source"]
    source_type = source["type"].lower()

    if source_type == "csv":
        path = ROOT / source["path"]
        records = read_csv_file(path)

    elif source_type == "json":
        path = ROOT / source["path"]
        records = read_json_file(path)

    elif source_type == "api":
        records = read_api_data(source)

    else:
        raise ValueError("Unsupported data source: " + source_type)

    logging.info("Successfully read %s records.", len(records))

    return records


# -------------------------------------------------
# STANDARDISE COLUMN NAMES
# -------------------------------------------------

def standardise_column(name):
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)

    return name.strip("_")


# -------------------------------------------------
# CONVERT DATA TYPES
# -------------------------------------------------

def convert_type(value, data_type):

    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()

        if value == "":
            return None

    if data_type == "string":
        return str(value)

    if data_type == "int":
        return int(float(value))

    if data_type == "float":
        return float(value)

    if data_type == "bool":

        if isinstance(value, bool):
            return value

        value = str(value).strip().lower()

        if value in ("yes", "true", "1", "y"):
            return True

        if value in ("no", "false", "0", "n"):
            return False

        raise ValueError("Invalid boolean value: " + str(value))

    if data_type == "date":
        return date.fromisoformat(str(value)).isoformat()

    if data_type == "datetime":
        return datetime.fromisoformat(str(value)).isoformat()

    raise ValueError("Unsupported data type: " + data_type)


# -------------------------------------------------
# CLEAN AND TRANSFORM DATA
# -------------------------------------------------

def clean_data(records, config):

    cleaning = config["cleaning"]

    missing_values = {
        str(value).strip().lower()
        for value in cleaning["missing_values"]
    }

    defaults = cleaning.get("defaults", {})
    rename = config.get("rename_columns", {})
    types = config.get("types", {})
    required = config.get("required_columns", [])
    duplicate_fields = config.get("deduplicate_by", [])

    # Standardise rename rules as well as incoming headings.
    # This prevents column-name mismatches.
    rename_rules = {
        standardise_column(old_name):
        standardise_column(new_name)
        for old_name, new_name in rename.items()
    }

    cleaned_records = []
    seen_records = set()

    invalid_rows = 0
    duplicates_removed = 0
    missing_values_filled = 0

    for row_number, original in enumerate(records, start=1):

        if not isinstance(original, dict):
            invalid_rows += 1
            logging.warning(
                "Row %s skipped. Record is not a dictionary.",
                row_number
            )
            continue

        row = {}

        # Standardise and rename columns
        for key, value in original.items():

            original_name = standardise_column(key)
            new_name = rename_rules.get(
                original_name,
                original_name
            )

            if isinstance(value, str):
                value = value.strip()

                if value.lower() in missing_values:
                    value = None

            row[new_name] = value

        # Fill missing values with configured defaults
        for key, default_value in defaults.items():

            key = standardise_column(key)

            if row.get(key) is None:
                row[key] = default_value
                missing_values_filled += 1

        # Convert configured data types
        for field, data_type in types.items():

            field = standardise_column(field)

            if field not in row:
                continue

            try:
                row[field] = convert_type(
                    row[field],
                    data_type
                )

            except (ValueError, TypeError, OverflowError):
                logging.warning(
                    "Row %s: Invalid %s value '%s'. Set to missing.",
                    row_number,
                    field,
                    row[field]
                )
                row[field] = None

        # Check required fields
        missing_required = [
            standardise_column(field)
            for field in required
            if row.get(standardise_column(field)) is None
        ]

        if missing_required:
            invalid_rows += 1

            logging.warning(
                "Row %s skipped. Missing required fields: %s",
                row_number,
                missing_required
            )
            continue

        # Remove duplicate records
        if duplicate_fields:

            duplicate_key = tuple(
                row.get(standardise_column(field))
                for field in duplicate_fields
            )

            if duplicate_key in seen_records:
                duplicates_removed += 1

                logging.info(
                    "Duplicate record removed at row %s.",
                    row_number
                )
                continue

            seen_records.add(duplicate_key)

        cleaned_records.append(row)

    logging.info(
        "Cleaning completed. Valid records: %s",
        len(cleaned_records)
    )

    return (
        cleaned_records,
        invalid_rows,
        duplicates_removed,
        missing_values_filled
    )


# -------------------------------------------------
# SAVE CSV OUTPUT
# -------------------------------------------------

def save_csv(records, output_path):

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not records:
        logging.warning("No records available for CSV output.")
        return

    # Include all fields found in the cleaned records.
    fieldnames = list(
        dict.fromkeys(
            key
            for record in records
            for key in record.keys()
        )
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(records)

    logging.info("CSV output saved: %s", output_path)


# -------------------------------------------------
# SAVE JSON OUTPUT
# -------------------------------------------------

def save_json(records, output_path):

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:

        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False
        )

    logging.info("JSON output saved: %s", output_path)


# -------------------------------------------------
# SAVE PROCESSING SUMMARY
# -------------------------------------------------

def save_summary(
    input_count,
    output_count,
    invalid_rows,
    duplicates_removed,
    missing_values_filled,
    output_path
):

    summary = {
        "input_rows": input_count,
        "output_rows": output_count,
        "invalid_rows_skipped": invalid_rows,
        "duplicates_removed": duplicates_removed,
        "missing_values_filled": missing_values_filled,
        "processing_status": "Completed"
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:

        json.dump(
            summary,
            file,
            indent=4
        )

    logging.info("Processing summary saved: %s", output_path)

    return summary


# -------------------------------------------------
# MAIN PIPELINE
# -------------------------------------------------

def main():

    try:
        config = load_config()

        setup_logging(config)

        logging.info("Starting data processing pipeline.")

        # Read raw data
        records = read_source(config)

        # Clean and transform records
        (
            cleaned_records,
            invalid_rows,
            duplicates_removed,
            missing_values_filled
        ) = clean_data(records, config)

        output = config["output"]

        # Save requested output formats
        formats = output.get("formats", [])

        if "csv" in formats:
            csv_path = ROOT / output["csv"]
            save_csv(cleaned_records, csv_path)

        if "json" in formats:
            json_path = ROOT / output["json"]
            save_json(cleaned_records, json_path)

        # Save processing summary
        summary_path = ROOT / output["summary"]

        summary = save_summary(
            len(records),
            len(cleaned_records),
            invalid_rows,
            duplicates_removed,
            missing_values_filled,
            summary_path
        )

        logging.info("Pipeline completed successfully.")

        print("\nPROCESSING SUMMARY")
        print("------------------")
        print("Input Rows:", summary["input_rows"])
        print("Output Rows:", summary["output_rows"])
        print("Invalid Rows Skipped:", summary["invalid_rows_skipped"])
        print("Duplicates Removed:", summary["duplicates_removed"])
        print("Missing Values Filled:", summary["missing_values_filled"])

    except Exception as error:
        logging.exception("Pipeline failed: %s", error)
        print("\nERROR:", error)


# -------------------------------------------------
# PROGRAM ENTRY POINT
# -------------------------------------------------

if __name__ == "__main__":
    main()
