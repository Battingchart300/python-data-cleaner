"""Data Cleaner — Hugging Face Space demo.

Upload a messy CSV or Excel file, get a cleaned one back.
No API key, no account: the file is cleaned inside this Space
and only you download the result.
"""

import tempfile
from pathlib import Path

import gradio as gr
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


def clean_file(upload):
    if upload is None:
        return None, "Upload a CSV or Excel file first."
    path = Path(upload.name)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    elif path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, dtype=str, keep_default_na=False)
    else:
        return None, "Only .csv and .xlsx files are supported."
    df = df.replace(r"^\s*$", pd.NA, regex=True)
    cleaned, report = clean(df)
    out = Path(tempfile.gettempdir()) / f"{path.stem}_clean{path.suffix}"
    if out.suffix.lower() == ".csv":
        cleaned.to_csv(out, index=False)
    else:
        cleaned.to_excel(out, index=False)
    text = (
        f"Rows: {report['rows_in']} -> {report['rows_out']}\n"
        f"Empty rows removed: {report['empty_rows_removed']}\n"
        f"Duplicates removed: {report['duplicates_removed']}\n"
        f"Empty cells left: {report['empty_cells_left']}"
    )
    return str(out), text


with gr.Blocks(title="Data Cleaner") as demo:
    gr.Markdown(
        "# Data Cleaner\n"
        "Upload a messy CSV or Excel file and download the cleaned version. "
        "Duplicates, empty rows, messy dates and numbers like `1 200,50` "
        "get fixed in one go. No API key, everything runs here."
    )
    with gr.Row():
        file_in = gr.File(label="Upload CSV or Excel", file_types=[".csv", ".xlsx"])
        file_out = gr.File(label="Download cleaned file")
    report = gr.Textbox(label="Report")
    btn = gr.Button("Clean it")
    btn.click(clean_file, inputs=file_in, outputs=[file_out, report])
    gr.Examples(
        examples=[["examples/messy.csv"]],
        inputs=file_in,
    )

demo.launch()
