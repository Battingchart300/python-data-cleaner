"""python-data-cleaner: clean messy CSV and Excel files in one command.

Usage:
    python main.py input.csv
    python main.py input.csv -o clean.csv
    python main.py input.xlsx -o clean.xlsx

What it does:
    - drops fully empty rows
    - trims whitespace from text cells
    - drops duplicate rows (after cleaning, so "1 200,50" and "1200.50" count as one)
    - parses date columns to YYYY-MM-DD
    - fixes numbers written as "1 200,50" -> 1200.50
    - prints a short report of what changed
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


def clean_text(value):
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def _is_text(series: pd.Series) -> bool:
    """Text column? Works for both the old object dtype and pandas 3 str dtype."""
    return series.dtype == object or pd.api.types.is_string_dtype(series)


def clean_numbers(series: pd.Series) -> pd.Series:
    """Turn strings like '1 200,50' into numbers, if the column looks numeric."""
    if not _is_text(series):
        return series
    cleaned = (
        series.astype(str)
        .str.replace("\u00a0", " ", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    numeric = pd.to_numeric(cleaned, errors="coerce")
    # Only accept the conversion if at least half the non-empty values parse.
    non_empty = series.notna() & (series.astype(str).str.strip() != "")
    if non_empty.sum() and numeric[non_empty].notna().mean() >= 0.5:
        return numeric
    return series


def clean_dates(series: pd.Series) -> pd.Series:
    """Parse a date-like column to YYYY-MM-DD, if most values parse."""
    if not _is_text(series):
        return series
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True, format="mixed")
    non_empty = series.notna() & (series.astype(str).str.strip() != "")
    if non_empty.sum() and parsed[non_empty].notna().mean() >= 0.5:
        return parsed.dt.strftime("%Y-%m-%d")
    return series


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    report = {"rows_in": len(df)}
    df = df.dropna(how="all")
    report["empty_rows_removed"] = report["rows_in"] - len(df)

    df = df.apply(lambda col: col.map(clean_text))

    for col in df.columns:
        name = str(col).lower()
        if "date" in name or "datum" in name:
            df[col] = clean_dates(df[col])
        else:
            df[col] = clean_numbers(df[col])

    before = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = before - len(df)

    report["rows_out"] = len(df)
    report["empty_cells_left"] = int(df.isna().sum().sum())
    return df, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean a messy CSV or Excel file.")
    parser.add_argument("input", help="input .csv or .xlsx file")
    parser.add_argument("-o", "--output", help="output file (default: <input>_clean.<ext>)")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"File not found: {in_path}")
        return 1

    if in_path.suffix.lower() == ".csv":
        df = pd.read_csv(in_path, dtype=str, keep_default_na=False)
    elif in_path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(in_path, dtype=str, keep_default_na=False)
    else:
        print("Only .csv and .xlsx files are supported.")
        return 1

    # Empty strings become NaN so the report counts them honestly.
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    cleaned, report = clean(df)

    out_path = Path(args.output) if args.output else in_path.with_name(f"{in_path.stem}_clean{in_path.suffix}")
    if out_path.suffix.lower() == ".csv":
        cleaned.to_csv(out_path, index=False)
    else:
        cleaned.to_excel(out_path, index=False)

    print(f"Input:  {in_path} ({report['rows_in']} rows)")
    print(f"Output: {out_path} ({report['rows_out']} rows)")
    print(f"- empty rows removed: {report['empty_rows_removed']}")
    print(f"- duplicates removed: {report['duplicates_removed']}")
    print(f"- empty cells left:   {report['empty_cells_left']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
