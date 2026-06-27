# Medicaid Provider Data Cleaning

## Project Overview

This project focuses on cleaning and standardizing Medicaid Provider Exclusion datasets collected from multiple U.S. states.

The objective is to prepare the datasets for PostgreSQL integration by applying a unified ETL pipeline.

## Current Progress

Completed States

- South Carolina
- Tennessee
- Texas
- Vermont
- Washington
- West Virginia
- Wyoming


## Data Cleaning Tasks

- Remove duplicate records
- Handle missing values
- Standardize provider names
- Validate National Provider Identifier (NPI)
- Preserve provider identifiers
- Standardize date formats (YYYY-MM-DD)
- Normalize exclusion status
- Generate PostgreSQL-ready datasets


## Project Structure

```
raw_data/         # Original datasets
cleaned_data/     # Cleaned datasets
scripts/          # Python data cleaning scripts
```

## Technologies

- Python
- Pandas
- PostgreSQL

## Author
Yiming Yan
