
# Python Data Processing Pipeline

## 1. Project Overview

The Python Data Processing Pipeline reads raw data, cleans and transforms it, and produces structured output files.

It handles missing values, incorrect data types, duplicate records, and invalid entries.

## 2. Project Objectives

- Read data from CSV, JSON, and API sources.
- Clean and standardise incoming data.
- Handle missing values.
- Convert values into correct data types.
- Identify and skip invalid records.
- Remove duplicate records.
- Save processed data in structured formats.
- Record activities using logging.
- Manage settings through a configuration file.

## 3. Technologies Used

- Python 3.9
- CSV and JSON
- Python standard library modules
- Logging
- JSON configuration management

## 4. Project Structure

python_data_processing_pipeline/
- config.json
- requirements.txt
- README.md
- src/pipeline.py
- data/input/raw_customers.csv
- data/input/raw_customers.json
- data/output/
- logs/

## 5. Installation and Setup

Requirements:
- Python 3.9 or later.
- Terminal or command-line application.

Open Terminal and navigate to the project folder:

    cd ~/Documents/python_data_processing_pipeline

Check your Python version:

    python3 --version

No additional packages are required because the project uses Python standard library modules.

## 6. Running the Pipeline

From the main project directory, run:

    python3 src/pipeline.py

The pipeline reads the configured source, cleans and transforms the records, removes duplicates, and saves the results.

## 7. Configuration Management

The config.json file controls:
- Input source type and file path.
- Missing-value rules.
- Default values.
- Column-renaming rules.
- Data type conversions.
- Required columns.
- Duplicate detection.
- Output file locations and formats.
- Logging settings.

The pipeline supports CSV, JSON, and API input sources.

## 8. Data Cleaning and Transformation

The pipeline:
- Identifies missing values and applies configured defaults.
- Converts values into integer, float, Boolean, date, and datetime types.
- Skips records missing required information.
- Removes duplicate records.

## 9. Output Files

The pipeline generates:
- cleaned_customers.csv
- cleaned_customers.json
- summary.json

Processing logs are stored in logs/pipeline.log.

## 10. Sample Test Results

## 10. Testing and Results

The pipeline was tested using three different input sources: CSV, JSON, and a public API.

### CSV Test

- Input Rows: 7
- Output Rows: 5
- Invalid Rows Skipped: 1
- Duplicates Removed: 1
- Missing Values Filled: 1

### JSON Test

- Input Rows: 2
- Output Rows: 2
- Invalid Rows Skipped: 0
- Duplicates Removed: 0
- Missing Values Filled: 2

### API Test

- Input Rows: 10
- Output Rows: 10
- Invalid Rows Skipped: 0
- Duplicates Removed: 0
- Missing Values Filled: 10

All three tests completed successfully.

## 11. Logging

The application uses Python logging to record processing activities and errors.

The log file is stored at:

`logs/pipeline.log`

## 12. Conclusion

The Python Data Processing Pipeline demonstrates how raw data can be read, cleaned, transformed, and saved in structured formats. It handles missing values, type conversions, invalid records, and duplicates while providing logging and configuration management.