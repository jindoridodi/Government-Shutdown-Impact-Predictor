"""
Script: find_malformed_unemployment_rows.py
Finds malformed rows in a CSV (default: data/datasets/unemploymentByCounty.csv).
Checks performed:
 - encoding fallback (utf-8, latin-1, cp1252)
 - delimiter sniffing
 - rows with wrong number of fields (different from header)
 - rows that are entirely empty or whitespace
 - rows with non-numeric values in columns that appear numeric based on a sample

Usage (from repo root):
python scripts/find_malformed_unemployment_rows.py \
    --input data/datasets/unemploymentByCounty.csv \
    --output data/processed/malformed_unemployment_rows.csv

The script prints a concise summary and writes a CSV report (line_no,issue,header_name,field_index,raw_value,row_repr).
"""

from __future__ import annotations
import argparse
import csv
import io
import os
from typing import List, Tuple, Dict, Any

ENCODINGS = ["utf-8", "latin-1", "cp1252"]


def try_open_with_encodings(path: str):
    """Try opening file with a set of encodings and return text content and encoding used."""
    last_exc = None
    for enc in ENCODINGS:
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                data = f.read()
            return data, enc
        except UnicodeDecodeError as e:
            last_exc = e
            continue
    # Fallback: read with latin-1 but replace errors
    with open(path, "r", encoding="latin-1", errors="replace") as f:
        data = f.read()
    return data, "latin-1-replaced"


def sniff_dialect(sample: str) -> csv.Dialect:
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample)
    except Exception:
        # default to excel
        dialect = csv.get_dialect("excel")
    return dialect


def is_blank_row(row: List[str]) -> bool:
    return all((cell is None or str(cell).strip() == "") for cell in row)


def is_number_like(s: str) -> bool:
    if s is None:
        return False
    t = str(s).strip()
    if t == "":
        return False
    # strip common thousand separators and percent signs
    t = t.replace(",", "").replace("%", "")
    try:
        float(t)
        return True
    except Exception:
        return False


def detect_numeric_columns(rows: List[List[str]], header_len: int, sample_size: int = 200) -> List[bool]:
    """Return boolean mask for columns that look numeric based on sample rows."""
    counts = [0] * header_len
    numeric_counts = [0] * header_len
    n = 0
    for row in rows:
        if n >= sample_size:
            break
        if len(row) != header_len:
            continue
        n += 1
        for i, cell in enumerate(row):
            counts[i] += 1
            if is_number_like(cell):
                numeric_counts[i] += 1
    mask = [False] * header_len
    for i in range(header_len):
        if counts[i] == 0:
            mask[i] = False
        else:
            # if >70% of sampled non-empty cells are numeric, consider numeric
            if numeric_counts[i] / counts[i] >= 0.7:
                mask[i] = True
    return mask


def find_malformed_rows(path: str, output_path: str | None = None) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    text, used_encoding = try_open_with_encodings(path)
    sample = text[:8192]
    dialect = sniff_dialect(sample)

    reader = csv.reader(io.StringIO(text), dialect)
    all_rows = list(reader)
    if not all_rows:
        raise SystemExit(f"No rows read from {path}")

    header = all_rows[0]
    header_len = len(header)

    # detect numeric-like columns using a sample of rows after header
    sample_rows = all_rows[1:1 + 500]
    numeric_mask = detect_numeric_columns(sample_rows, header_len)

    malformed = []
    stats = {
        "total_rows": 0,
        "malformed_rows": 0,
        "encoding_used": used_encoding,
        "wrong_field_count": 0,
        "blank_rows": 0,
        "numeric_mismatch": 0,
    }

    for i, row in enumerate(all_rows[1:], start=2):
        stats["total_rows"] += 1
        issues = []
        if is_blank_row(row):
            issues.append("blank_row")
            stats["blank_rows"] += 1

        if len(row) != header_len:
            issues.append(f"field_count_mismatch (got {len(row)}, expected {header_len})")
            stats["wrong_field_count"] += 1

        # numeric checks only when length matches
        if len(row) == header_len:
            for idx, should_be_numeric in enumerate(numeric_mask):
                if not should_be_numeric:
                    continue
                val = row[idx]
                if val is None or str(val).strip() == "":
                    # empty numeric field is malformed
                    issues.append(f"numeric_missing:col={idx}:{header[idx]}")
                    stats["numeric_mismatch"] += 1
                else:
                    if not is_number_like(val):
                        issues.append(f"numeric_parse_fail:col={idx}:{header[idx]}:{val}")
                        stats["numeric_mismatch"] += 1

        if issues:
            stats["malformed_rows"] += 1
            malformed.append({
                "line_no": i,
                "issues": ";".join(issues),
                "row_repr": "|".join(row),
                "raw_row": row,
            })

    # Optionally write a CSV report
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="") as outf:
            w = csv.writer(outf)
            w.writerow(["line_no", "issues", "field_index", "header_name", "raw_value", "row_repr"])
            for item in malformed:
                line_no = item["line_no"]
                issues = item["issues"].split(";")
                row = item["raw_row"]
                for iss in issues:
                    # try to parse numeric issue details to provide context
                    if iss.startswith("numeric_parse_fail:") or iss.startswith("numeric_missing:"):
                        parts = iss.split(":")
                        # parts: ['numeric_parse_fail','col=IDX','Header','value'] or ['numeric_missing','col=IDX','Header']
                        col_part = parts[1] if len(parts) > 1 else "col=?"
                        idx_str = col_part.split("=")[1] if "=" in col_part else "?"
                        try:
                            idx = int(idx_str)
                        except Exception:
                            idx = "?"
                        header_name = parts[2] if len(parts) > 2 else ""
                        raw_value = parts[3] if len(parts) > 3 else (row[idx] if isinstance(idx, int) and idx < len(row) else "")
                        w.writerow([line_no, iss, idx, header_name, raw_value, "|".join(row)])
                    else:
                        w.writerow([line_no, iss, "", "", "", "|".join(row)])

    return malformed, stats


def main():
    p = argparse.ArgumentParser(description="Find malformed rows in a CSV file.")
    p.add_argument("--input", "-i", default="data/datasets/unemploymentByCounty.csv", help="Path to CSV file")
    p.add_argument("--output", "-o", default="data/processed/malformed_unemployment_rows.csv", help="CSV report output path (optional)")
    args = p.parse_args()

    print(f"Scanning: {args.input}")
    malformed, stats = find_malformed_rows(args.input, args.output)

    print("\nSummary:")
    print(f" Encoding used: {stats['encoding_used']}")
    print(f" Total data rows scanned: {stats['total_rows']}")
    print(f" Malformed rows found: {stats['malformed_rows']}")
    print(f"  - wrong field count: {stats['wrong_field_count']}")
    print(f"  - blank rows: {stats['blank_rows']}")
    print(f"  - numeric mismatches: {stats['numeric_mismatch']}")

    if stats['malformed_rows'] > 0:
        print(f"\nDetailed report written to: {os.path.abspath(args.output)}")
    else:
        # if file created but empty, remove it to avoid confusion
        try:
            if os.path.exists(args.output):
                os.remove(args.output)
        except Exception:
            pass
        print("No malformed rows detected based on the heuristics.")


if __name__ == '__main__':
    main()
