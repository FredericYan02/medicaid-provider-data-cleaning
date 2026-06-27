"""
clean_wyoming.py

Purpose:
Clean and standardize the Wyoming Medicaid Provider Exclusion dataset.

Input:
    raw_data/Wyoming.xlsx

Output:
    cleaned_data/Wyoming_Cleaned.xlsx
    cleaned_data/Wyoming_Cleaned.csv
"""

from pathlib import Path
import re
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "raw_data" / "Wyoming.xlsx"
OUTPUT_DIR = BASE_DIR / "cleaned_data"
OUTPUT_EXCEL = OUTPUT_DIR / "Wyoming_Cleaned.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "Wyoming_Cleaned.csv"


def clean_text(value):
    """Trim spaces and normalize internal whitespace."""
    if pd.isna(value):
        return None

    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    if value == "" or value.lower() in {"nan", "none", "null", "n/a", "na"}:
        return None

    return value


def normalize_column_name(column_name):
    """Convert raw column names into snake_case."""
    column_name = str(column_name).strip().lower()
    column_name = re.sub(r"[^a-z0-9]+", "_", column_name)
    column_name = column_name.strip("_")
    return column_name


def find_column(df, possible_names):
    """Find a column from a list of possible source column names."""
    for name in possible_names:
        if name in df.columns:
            return name
    return None


def clean_date(value):
    """Convert date values to YYYY-MM-DD format."""
    if pd.isna(value):
        return None

    parsed_date = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed_date):
        return None

    return parsed_date.strftime("%Y-%m-%d")


def clean_npi_and_identifier(value):
    """
    Extract valid 10-digit NPI values from provider number.

    If one 10-digit NPI exists:
        npi_valid = Yes

    If multiple 10-digit NPIs exist:
        keep all in npi and mark npi_valid = No

    Other license/provider numbers are retained in provider_identifier.
    """
    value = clean_text(value)

    if value is None:
        return None, "No", None

    if value.upper() in {"N/A", "NA"}:
        return None, "No", None

    npi_matches = re.findall(r"\b\d{10}\b", value)

    if len(npi_matches) == 1:
        npi = npi_matches[0]
        npi_valid = "Yes"
    elif len(npi_matches) > 1:
        npi = "; ".join(npi_matches)
        npi_valid = "No"
    else:
        npi = None
        npi_valid = "No"

    identifier_text = value

    # Remove NPI labels and extracted NPI values from provider_identifier.
    identifier_text = re.sub(r"\bNPI\b\s*:?\s*", "", identifier_text, flags=re.IGNORECASE)

    for npi_value in npi_matches:
        identifier_text = identifier_text.replace(npi_value, "")

    identifier_parts = [
        clean_text(part)
        for part in re.split(r"[/,;\n]+", identifier_text)
    ]

    identifier_parts = [
        part
        for part in identifier_parts
        if part and part.upper() not in {"N/A", "NA", "NONE", "NULL"}
    ]

    provider_identifier = "; ".join(identifier_parts) if identifier_parts else None

    return npi, npi_valid, provider_identifier


def build_provider_name(last_name, first_name, business_name):
    """
    Build provider_name from last name, first name, and business name.
    """
    last_name = clean_text(last_name)
    first_name = clean_text(first_name)
    business_name = clean_text(business_name)

    person_name = " ".join(part for part in [first_name, last_name] if part)

    if person_name and business_name:
        return f"{person_name} / {business_name}"

    return person_name or business_name


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(RAW_FILE)
    df.columns = [normalize_column_name(col) for col in df.columns]

    last_name_col = find_column(df, ["last_name", "lastname"])
    first_name_col = find_column(df, ["first_name", "firstname"])
    business_name_col = find_column(df, ["business_name", "business", "organization_name", "entity_name"])
    provider_name_col = find_column(df, ["provider_name", "name"])

    provider_type_col = find_column(df, ["provider_type", "type", "provider_category", "specialty"])
    provider_number_col = find_column(df, ["provider_number", "provider_no", "provider_id", "license_number", "license_no", "npi"])
    city_col = find_column(df, ["city"])
    state_col = find_column(df, ["state", "provider_state"])
    date_col = find_column(df, ["exclusion_date", "date_of_exclusion", "action_date", "effective_date", "date"])
    reason_col = find_column(df, ["exclusion_reason", "reason", "action", "comments", "basis"])

    cleaned_rows = []

    for _, row in df.iterrows():
        if provider_name_col:
            provider_name = clean_text(row[provider_name_col])
        else:
            provider_name = build_provider_name(
                row[last_name_col] if last_name_col else None,
                row[first_name_col] if first_name_col else None,
                row[business_name_col] if business_name_col else None,
            )

        if provider_name is None:
            continue

        npi, npi_valid, provider_identifier = clean_npi_and_identifier(
            row[provider_number_col] if provider_number_col else None
        )

        provider_state = clean_text(row[state_col]) if state_col else None
        if provider_state is None:
            provider_state = "WY"

        cleaned_rows.append({
            "provider_name": provider_name,
            "npi": npi,
            "npi_valid": npi_valid,
            "provider_identifier": provider_identifier,
            "city": clean_text(row[city_col]) if city_col else None,
            "provider_state": provider_state,
            "zip_code": None,
            "provider_type": clean_text(row[provider_type_col]) if provider_type_col else None,
            "exclusion_status": "Excluded",
            "action_date": clean_date(row[date_col]) if date_col else None,
            "source_state": "Wyoming",
            "exclusion_reason": clean_text(row[reason_col]) if reason_col else None,
        })

    cleaned_df = pd.DataFrame(cleaned_rows)

    standard_columns = [
        "provider_name",
        "npi",
        "npi_valid",
        "provider_identifier",
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

    print("Wyoming data cleaning completed.")
    print(f"Raw rows: {before_dedup}")
    print(f"Cleaned rows: {after_dedup}")
    print(f"Duplicates removed: {before_dedup - after_dedup}")
    print(f"Excel output: {OUTPUT_EXCEL}")
    print(f"CSV output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
