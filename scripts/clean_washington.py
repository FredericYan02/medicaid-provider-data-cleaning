"""
clean_washington.py

Purpose:
Clean and standardize the Washington Medicaid Provider Exclusion dataset.

Input:
    raw_data/Washington.xlsx

Output:
    cleaned_data/Washington_Cleaned.xlsx
    cleaned_data/Washington_Cleaned.csv
"""

from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "raw_data" / "Washington.xlsx"
OUTPUT_DIR = BASE_DIR / "cleaned_data"
OUTPUT_EXCEL = OUTPUT_DIR / "Washington_Cleaned.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "Washington_Cleaned.csv"


def clean_text(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    if value == "" or value.lower() in {"nan", "none", "null", "n/a", "na"}:
        return None
    return value


def normalize_column_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def clean_npi(value):
    value = clean_text(value)
    if value is None:
        return None, "No"

    npi_matches = re.findall(r"\b\d{10}\b", value)

    if len(npi_matches) == 1:
        return npi_matches[0], "Yes"

    return None, "No"


def clean_zip(value):
    value = clean_text(value)
    if value is None:
        return None
    digits = re.sub(r"\D", "", value)
    return digits[:5] if len(digits) >= 5 else None


def clean_date(value):
    if pd.isna(value):
        return None
    parsed_date = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed_date):
        return None
    return parsed_date.strftime("%Y-%m-%d")


def find_column(df, names):
    for name in names:
        if name in df.columns:
            return name
    return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(RAW_FILE)
    df.columns = [normalize_column_name(col) for col in df.columns]

    provider_name_col = find_column(df, [
        "provider_name",
        "name",
        "provider",
        "individual_name",
        "entity_name",
        "individual_entity_name",
    ])

    npi_col = find_column(df, [
        "npi",
        "npi_number",
        "provider_npi",
        "npi_or_p1",
    ])

    city_col = find_column(df, [
        "city",
        "provider_city",
    ])

    state_col = find_column(df, [
        "state",
        "provider_state",
    ])

    zip_col = find_column(df, [
        "zip",
        "zip_code",
        "zipcode",
        "provider_zip",
    ])

    provider_type_col = find_column(df, [
        "provider_type",
        "type",
        "provider_category",
        "specialty",
        "license_type",
        "license",
        "license_number",
        "license_no",
    ])

    date_col = find_column(df, [
        "action_date",
        "effective_date",
        "exclusion_date",
        "date_of_exclusion",
        "termination_date",
        "date",
    ])

    reason_col = find_column(df, [
        "exclusion_reason",
        "reason",
        "action",
        "comments",
        "basis",
        "description",
    ])

    rows = []

    for _, row in df.iterrows():
        npi, npi_valid = clean_npi(row[npi_col] if npi_col else None)

        state = clean_text(row[state_col]) if state_col else None
        if state is None:
            state = "WA"

        rows.append({
            "provider_name": clean_text(row[provider_name_col]) if provider_name_col else None,
            "npi": npi,
            "npi_valid": npi_valid,
            "city": clean_text(row[city_col]) if city_col else None,
            "provider_state": state,
            "zip_code": clean_zip(row[zip_col]) if zip_col else None,
            "provider_type": clean_text(row[provider_type_col]) if provider_type_col else None,
            "exclusion_status": "Excluded",
            "action_date": clean_date(row[date_col]) if date_col else None,
            "source_state": "Washington",
            "exclusion_reason": clean_text(row[reason_col]) if reason_col else None,
        })

    out = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)
    out.insert(0, "record_id", range(1, len(out) + 1))

    out.to_excel(OUTPUT_EXCEL, index=False)
    out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("Washington data cleaning completed.")
    print(f"Rows: {len(out)}")
    print(f"Excel output: {OUTPUT_EXCEL}")
    print(f"CSV output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
