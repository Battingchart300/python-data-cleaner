"""Tests for python-data-cleaner (pytest).

Run:  pytest -v
Covers the main cleaning steps on the real example file
(examples/messy.csv: 10 rows -> 7 rows after cleaning).
"""

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main  # noqa: E402


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def load_messy() -> pd.DataFrame:
    """Load examples/messy.csv exactly like main.py does."""
    df = pd.read_csv(EXAMPLES / "messy.csv", dtype=str, keep_default_na=False)
    return df.replace(r"^\s*$", pd.NA, regex=True)


@pytest.fixture(scope="module")
def cleaned():
    df, report = main.clean(load_messy())
    return df, report


def test_messy_to_7_rows(cleaned):
    df, report = cleaned
    assert report["rows_in"] == 10
    assert report["rows_out"] == 7
    assert len(df) == 7


def test_empty_row_removed(cleaned):
    _, report = cleaned
    assert report["empty_rows_removed"] == 1


def test_duplicates_removed(cleaned):
    df, report = cleaned
    assert report["duplicates_removed"] == 2
    assert df["name"].tolist().count("Ján Novák") == 1


def test_dates_normalized(cleaned):
    df, _ = cleaned
    dates = df["signup_date"].tolist()
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d)) for d in dates)
    assert dates[0] == "2024-03-12"  # 12.03.2024
    assert dates[2] == "2024-03-14"  # 14/03/2024


def test_numbers_fixed(cleaned):
    df, _ = cleaned
    amounts = df["amount"].tolist()
    assert 1200.5 in amounts
    assert 2500.0 in amounts
    assert 3100.75 in amounts
    assert 450.5 in amounts


def test_whitespace_trimmed(cleaned):
    df, _ = cleaned
    assert "Mária Kováčová" in df["name"].tolist()
    assert "Anna Nová" in df["name"].tolist()
    assert "Košice" in df["city"].tolist()
    assert not any(str(v).startswith(" ") or str(v).endswith(" ") for v in df["name"])


def test_empty_cells_stay_empty(cleaned):
    df, _ = cleaned
    lucia = df[df["name"] == "Lucia Malá"].iloc[0]
    assert pd.isna(lucia["email"])
    tomas = df[df["name"] == "Tomáš Veľký"].iloc[0]
    assert pd.isna(tomas["amount"])


def test_clean_text():
    assert main.clean_text("  a   b  ") == "a b"
    assert main.clean_text("Anna  Nová") == "Anna Nová"
    assert main.clean_text(123) == 123
    assert main.clean_text(None) is None


def test_numbers_not_forced_on_text():
    s = pd.Series(["Bratislava", "Košice", "Žilina"], dtype=str)
    assert main.clean_numbers(s).tolist() == ["Bratislava", "Košice", "Žilina"]


def test_dates_not_forced_on_text():
    s = pd.Series(["Bratislava", "Košice", "Žilina"], dtype=str)
    assert main.clean_dates(s).tolist() == ["Bratislava", "Košice", "Žilina"]


def test_number_formats():
    s = pd.Series(["1 200,50", "2 500,00", "999.99", "750"], dtype=str)
    result = main.clean_numbers(s)
    assert result.tolist() == [1200.5, 2500.0, 999.99, 750.0]


def test_cli_writes_clean_file(tmp_path, monkeypatch):
    out = tmp_path / "clean.csv"
    monkeypatch.setattr(
        sys, "argv", ["main.py", str(EXAMPLES / "messy.csv"), "-o", str(out)]
    )
    assert main.main() == 0
    assert out.exists()
    result = pd.read_csv(out, dtype=str)
    assert len(result) == 7
