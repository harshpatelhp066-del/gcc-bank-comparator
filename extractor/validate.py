"""
validate.py -- cross-checks extractor.py's automated output against
gcc_banks.db (the figures manually read off the same PDFs and entered by
hand in build_db.py). This is the honesty check for the whole exercise:
does the parser actually agree with a human reader, field by field?
"""
import json
import sqlite3
import extractor

DB_PATH = "/mnt/user-data/uploads/gcc_banks.db"

# DIB reports in AED'000 in its PDF; the DB stores everything in AED million.
SCALE = {"EMIRATESNBD": 1, "ADCB": 1, "DIB": 1000}

FILES = {
    "EMIRATESNBD": "raw_text/emiratesnbd.txt",
    "ADCB": "raw_text/adcb.txt",
    "DIB": "raw_text/dib.txt",
}

def load_db_values():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM financials")
    rows = {}
    for r in cur.fetchall():
        rows.setdefault(r["ticker"], {})[r["fiscal_year"]] = dict(r)
    conn.close()
    return rows

ABS_COMPARE_FIELDS = {"operating_expenses", "impairment_charge"}
NO_SCALE_FIELDS = {"eps"}

def main():
    db = load_db_values()
    total_checked = 0
    total_matched = 0
    report_lines = []

    for ticker, path in FILES.items():
        with open(path, encoding="utf-8") as f:
            text = f.read()
        extracted = extractor.extract_bank(ticker, text)
        scale = SCALE[ticker]

        report_lines.append(f"\n=== {ticker} ===")
        for fy_key, fy_num in [("fy2025", 2025), ("fy2024", 2024)]:
            db_row = db[ticker][fy_num]
            for field, ex_val in extracted[fy_key].items():
                db_val = db_row.get(field)
                if db_val is None:
                    continue
                ex_scaled = ex_val if field in NO_SCALE_FIELDS else ex_val / scale
                cmp_extracted = abs(ex_scaled) if field in ABS_COMPARE_FIELDS else ex_scaled
                cmp_db = abs(db_val) if field in ABS_COMPARE_FIELDS else db_val
                total_checked += 1
                if abs(cmp_extracted - cmp_db) < 0.6:
                    total_matched += 1
                    status = "MATCH"
                else:
                    status = "MISMATCH"
                note = "  (sign convention: PDF shows as a deduction, DB stores magnitude)" if field in ABS_COMPARE_FIELDS else ""
                report_lines.append(
                    f"  FY{fy_num} {field:28s} extracted={ex_scaled:>14,.2f}  "
                    f"db={db_val:>14,.2f}  [{status}]{note}"
                )
            if extracted["unmatched"]:
                report_lines.append(f"  FY{fy_num} not extracted (config gap): {extracted['unmatched']}")

    report_lines.append(
        f"\n=== SUMMARY: {total_matched}/{total_checked} extracted values matched "
        f"the manually verified database ({total_matched/total_checked*100:.1f}%) ==="
    )
    report = "\n".join(report_lines)
    print(report)
    with open("validation_report.txt", "w") as f:
        f.write(report)

if __name__ == "__main__":
    main()
