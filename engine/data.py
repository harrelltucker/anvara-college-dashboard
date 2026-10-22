"""Load and save the CSV tables and the default weights."""

import csv
import tomllib
from pathlib import Path

import pandas as pd

from engine.schema import FINDINGS_COLUMNS, TABLES

ROOT = Path(__file__).resolve().parent.parent
RESEARCH_DIR = ROOT / "data" / "research"
DEMO_DIR = ROOT / "data" / "demo"
PENDING_FILE = ROOT / "data" / "pending" / "findings.csv"
WEIGHTS_FILE = ROOT / "config" / "weights.toml"


def _read(path, columns):
    """Read a CSV as text ('' for blanks). A missing file becomes an empty table."""
    if not path.exists():
        return pd.DataFrame(columns=columns, dtype=str)
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].str.strip()
    for col in columns:          # tolerate older files missing a newer optional column
        if col not in df.columns:
            df[col] = ""
    return df


def load_tables(folder=RESEARCH_DIR):
    folder = Path(folder)
    return {name: _read(folder / f"{name}.csv", spec["columns"]) for name, spec in TABLES.items()}


def load_findings():
    return _read(PENDING_FILE, FINDINGS_COLUMNS)


def save_table(df, path, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    df = df.reindex(columns=columns).fillna("")
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")


def append_record(table, record, folder=RESEARCH_DIR):
    """Append one row to a research table, keeping the column order from the schema."""
    columns = TABLES[table]["columns"]
    path = Path(folder) / f"{table}.csv"
    current = _read(path, columns)
    save_table(pd.concat([current, pd.DataFrame([record])], ignore_index=True), path, columns)


def load_weights(path=WEIGHTS_FILE):
    with open(path, "rb") as f:
        return tomllib.load(f)
