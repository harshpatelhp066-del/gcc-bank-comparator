"""
extractor.py -- pulls financial statement line items out of raw text extracted
from audited bank PDF filings (DFM/ADX-listed UAE banks).

This module is deliberately decoupled from *how* the PDF text was obtained.
In this sandboxed demo the raw text came from Claude's own web_fetch tool
(network-limited sandbox has no route to dib.ae / adx.ae / emiratesnbd.com
directly). On a normal machine, the same raw text would come from
`pdfplumber.open(path).pages[i].extract_text()` -- the parsing logic below
is pure Python / regex, has no network dependency, and is unchanged either way.
"""
import re
import json

NUM_TOKEN = r"\(?-?\d[\d,]*(?:\.\d+)?\)?(?!\d)"

def parse_number(tok: str):
    tok = tok.strip()
    neg = tok.startswith("(") and tok.endswith(")")
    tok = tok.strip("()").replace(",", "")
    val = float(tok)
    return -val if neg else val

def extract_field(text: str, label: str, n: int = 2):
    """
    Find `label` anchored at the start of a line (case-insensitive) --
    this matters because e.g. 'Operating income' is a literal substring of
    'Other operating income', a completely different line item, so an
    unanchored search silently grabs the wrong row. After the label, skip
    an optional unit tag like '(AED)' or '(AED/USD)' and an optional short
    note-reference number (e.g. '17' or '22.1'), then capture exactly the
    next n numeric tokens -- AED figures come first in every filing checked,
    before any USD convenience columns.
    Returns a list of n floats, or None if no match found.
    """
    pattern = re.compile(
        rf"(?m)^\s*{re.escape(label)}\s*"
        rf"(?:\([A-Za-z /]*\)\s*)?"
        rf"(?:\d{{1,3}}(?:\.\d+)?\s+)?"
        + r"\s*".join([rf"({NUM_TOKEN})"] * n),
        re.IGNORECASE,
    )
    m = pattern.search(text)
    if not m:
        return None
    return [parse_number(g) for g in m.groups()]

# Per-bank label mapping: canonical field -> (label text as it appears in the
# filing, number of year-columns to capture). Terminology genuinely differs
# bank to bank -- this is the real reason a generic regex alone isn't enough;
# each filing needs its own small config, same as a human reader would need
# to know where to look.
BANK_FIELD_LABELS = {
    "EMIRATESNBD": {
        "total_assets": ("Total assets", 2),
        "total_liabilities": ("Total liabilities", 2),
        "total_equity": ("Total equity", 2),
        "total_operating_income": ("Total operating income", 2),
        "operating_expenses": ("General and administrative expenses", 2),
        "impairment_charge": ("Net impairment", 2),
        "profit_before_tax": ("Profit for the year before taxation", 2),
        "net_profit": ("Profit for the year", 2),
        "eps": ("Earnings per share", 2),
        "loans_or_financing_net": ("Loans and receivables", 2),
        "customer_deposits": ("Customer deposits", 2),
    },
    "ADCB": {
        "total_assets": ("Total assets", 2),
        "total_liabilities": ("Total liabilities", 2),
        "total_equity": ("Total equity", 2),
        "total_operating_income": ("Operating income", 2),
        "operating_expenses": ("Operating expenses", 2),
        "impairment_charge": ("Impairment charge", 2),
        "profit_before_tax": ("Profit before taxation", 2),
        "net_profit": ("Profit for the year", 2),
        "eps": ("Basic earnings per share", 2),
        "loans_or_financing_net": ("Loans and advances to customers, net", 2),
        "customer_deposits": ("Deposits from customers", 2),
    },
    "DIB": {
        # Balance-sheet fields intentionally absent: page 7 of DIB's PDF has
        # never extracted as parseable text on any fetch attempt (3 tries,
        # different token limits) -- see raw_text/dib.txt note. Nothing to
        # regex-match against; those fields stay press-release-sourced.
        "total_operating_income": ("Total income", 2),
        "operating_expenses": ("Total operating expenses", 2),
        "impairment_charge": ("Impairment charges, net", 2),
        "profit_before_tax": ("Profit for the year before income tax expense", 2),
        "net_profit": ("Net profit for the year", 2),
        "eps": ("Basic and diluted earnings per share", 2),
    },
}

def extract_bank(ticker: str, raw_text: str) -> dict:
    fields = BANK_FIELD_LABELS[ticker]
    out = {"fy2025": {}, "fy2024": {}, "unmatched": []}
    for field, (label, n) in fields.items():
        result = extract_field(raw_text, label, n)
        if result is None:
            out["unmatched"].append(field)
            continue
        out["fy2025"][field] = result[0]
        out["fy2024"][field] = result[1]
    return out

if __name__ == "__main__":
    results = {}
    for ticker, path in [
        ("EMIRATESNBD", "raw_text/emiratesnbd.txt"),
        ("ADCB", "raw_text/adcb.txt"),
        ("DIB", "raw_text/dib.txt"),
    ]:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        results[ticker] = extract_bank(ticker, text)
    print(json.dumps(results, indent=2))
