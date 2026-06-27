"""
clean_tennessee.py

Purpose:
Clean and standardize the Tennessee Medicaid Provider Exclusion dataset.
"""

from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "raw_data" / "Tennessee.xlsx"
OUTPUT_DIR = BASE_DIR / "cleaned_data"
OUTPUT_EXCEL = OUTPUT_DIR / "Tennessee_Cleaned.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "Tennessee_Cleaned.csv"


def clean_text(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    if value == "" or value.lower() in {"nan", "none", "null", "n/a", "na"}:
        return None
    return value


def normalize_column_name(column_name):
    column_name = str(column_name).strip().lower()
    column_name = re.sub(r"[^a-z0-9]+", "_", column_name)
    return column_name.strip("_")


def clean_npi(value):
    value = clean_text(value)
    if value is None:
        return None, "No", None, "missing npi"

    npi_matches = re.findall(r"\b\d{10}\b", value)

    if len(npi_matches) == 1:
        return npi_matches[0], "Yes", None, None
    if len(npi_matches) > 1:
        return "; ".join(npi_matches), "No", None, "multiple NPI values retained from source"

    return None, "No", value, "non-NPI identifier retained from source"


def clean_zip(value):
    value = clean_text(value)
    if value is None:
        return None
    digits = re.sub(r"\D", "", value)
    return digits[:5] if len(digits) >= 5 else None


def clean_date(value):
    if pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")


def find_column(df, possible_names):
    for name in possible_names:
        if name in df.columns:
            return name
    return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(RAW_FILE)
    df.columns = [normalize_column_name(c) for c in df.columns]

    provider_name_col = find_column(df, ["provider_name","name","individual_name","entity_name","provider","business_name"])
    npi_col = find_column(df, ["npi","npi_number","provider_npi"])
    city_col = find_column(df, ["city","provider_city"])
    state_col = find_column(df, ["state","provider_state"])
    zip_col = find_column(df, ["zip","zip_code","zipcode","provider_zip"])
    provider_type_col = find_column(df, ["provider_type","type","provider_category","specialty"])
    date_col = find_column(df, ["action_date","exclusion_date","effective_date","termination_date","date"])
    reason_col = find_column(df, ["exclusion_reason","reason","action","comments","basis"])

    rows = []

    for _, row in df.iterrows():
        npi, npi_valid, provider_identifier, note = clean_npi(row[npi_col] if npi_col else None)
        state = clean_text(row[state_col]) if state_col else None
        if state is None:
            state = "TN"

        rows.append({
            "provider_name": clean_text(row[provider_name_col]) if provider_name_col else None,
            "npi": npi,
            "npi_valid": npi_valid,
            "provider_identifier": provider_identifier,
            "city": clean_text(row[city_col]) if city_col else None,
            "provider_state": state,
            "zip_code": clean_zip(row[zip_col]) if zip_col else None,
            "provider_type": clean_text(row[provider_type_col]) if provider_type_col else None,
            "exclusion_status": "Excluded",
            "action_date": clean_date(row[date_col]) if date_col else None,
            "source_state": "Tennessee",
            "exclusion_reason": clean_text(row[reason_col]) if reason_col else None,
        })

    df_out = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)
    df_out.insert(0, "record_id", range(1, len(df_out)+1))
    df_out.to_excel(OUTPUT_EXCEL, index=False)
    df_out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("Done")


if __name__ == "__main__":
    main()
