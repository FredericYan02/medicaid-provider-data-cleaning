"""
clean_west_virginia.py

Purpose:
Clean and standardize the West Virginia Medicaid Provider Exclusion dataset.

Input:
    raw_data/West Virginia.csv

Output:
    cleaned_data/West_Virginia_Cleaned.xlsx
    cleaned_data/West_Virginia_Cleaned.csv
"""

from pathlib import Path
import re
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "raw_data" / "West Virginia.csv"
OUTPUT_DIR = BASE_DIR / "cleaned_data"
OUTPUT_EXCEL = OUTPUT_DIR / "West_Virginia_Cleaned.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "West_Virginia_Cleaned.csv"


def clean_text(value):
    """Trim spaces and normalize internal whitespace."""
    if pd.isna(value):
        return None

    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    if value == "" or value.lower() in {"nan", "none", "null", "n/a", "na"}:
        return None

    return value


def clean_npi(value):
    """Extract NPI values from the identifiers field."""
    value = clean_text(value)

    if value is None:
        return None, "No"

    npi_matches = re.findall(r"\b\d{10}\b", value)

    if len(npi_matches) == 1:
        return npi_matches[0], "Yes"

    if len(npi_matches) > 1:
        return "; ".join(npi_matches), "No"

    return None, "No"


def parse_address(value):
    """
    Extract city, state, and ZIP from the OpenSanctions address field.

    Example:
        510 Washington Street West, Charleston, WV 25302
    """
    value = clean_text(value)

    if value is None:
        return None, "WV", None

    match = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})(?:-\d{4})?", value)

    if match:
        city = clean_text(match.group(1))
        state = clean_text(match.group(2))
        zip_code = match.group(3)
        return city, state, zip_code

    return None, "WV", None


def clean_date_from_text(value):
    """Extract YYYY-MM-DD date from the sanctions text."""
    value = clean_text(value)

    if value is None:
        return None

    matches = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", value)

    if not matches:
        return None

    parsed_date = pd.to_datetime(matches[-1], errors="coerce")

    if pd.isna(parsed_date):
        return None

    return parsed_date.strftime("%Y-%m-%d")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_FILE, dtype=str)

    cleaned_rows = []

    for _, row in df.iterrows():
        city, provider_state, zip_code = parse_address(row.get("addresses"))
        npi, npi_valid = clean_npi(row.get("identifiers"))

        cleaned_rows.append({
            "provider_name": clean_text(row.get("name")),
            "npi": npi,
            "npi_valid": npi_valid,
            "city": city,
            "provider_state": provider_state,
            "zip_code": zip_code,
            "provider_type": clean_text(row.get("schema")),
            "exclusion_status": "Excluded",
            "action_date": clean_date_from_text(row.get("sanctions")),
            "source_state": "West Virginia",
            "exclusion_reason": clean_text(row.get("sanctions")),
        })

    cleaned_df = pd.DataFrame(cleaned_rows)

    standard_columns = [
        "provider_name",
        "npi",
        "npi_valid",
        "city",
        "provider_state",
        "zip_code",
        "provider_type",
        "exclusion_status",
        "action_date",
        "source_state",
        "exclusion_reason",
    ]

    cleaned_df = cleaned_df[standard_columns]

    before_dedup = len(cleaned_df)
    cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
    after_dedup = len(cleaned_df)

    cleaned_df.insert(0, "record_id", range(1, len(cleaned_df) + 1))

    cleaned_df.to_excel(OUTPUT_EXCEL, index=False)
    cleaned_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("West Virginia data cleaning completed.")
    print(f"Raw rows: {before_dedup}")
    print(f"Cleaned rows: {after_dedup}")
    print(f"Duplicates removed: {before_dedup - after_dedup}")
    print(f"Excel output: {OUTPUT_EXCEL}")
    print(f"CSV output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
