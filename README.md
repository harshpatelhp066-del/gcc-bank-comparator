# GCC Bank Earnings Comparator

**[Live dashboard](https://harshpatelhp066-del.github.io/gcc-bank-comparator/)** · SQLite + CSV + a PDF-to-structured-data extraction engine validated at **100% (56/56 fields)** against three real audited bank filings.

Pulls audited financial statements for three DFM/ADX-listed UAE banks out of
individual PDF filings — the way they're actually published, since neither
exchange has anything like SEC EDGAR — and puts them into one comparable
dataset, a working dashboard, and an automated parser that reads the PDFs
itself instead of relying on manual transcription. See `extractor/README.md`
for how the parser works, the bugs found while building it, and exactly
which fields it can and can't extract yet.

## What's in here

- **`dashboard.html`** — the comparator ([live version](https://harshpatelhp066-del.github.io/gcc-bank-comparator/)). Open it in any browser, no server
  needed. Metric cards, YoY bar charts (total assets, net profit, ROE,
  operating income growth), a full data table, and a source ledger linking
  every number back to the filing it came from.
- **`extractor/`** — the automated PDF extraction engine. Regexes financial
  line items directly out of real filing text; validated field-by-field
  against the manually verified data below.
- **`gcc_banks.db`** — SQLite database with two tables (`banks`, `financials`)
  holding the same data behind the dashboard.
- **`financials.csv`** — flat export of the same data, for opening in Excel
  or re-importing elsewhere.
- **`data.json`** — the raw data as JSON (this is what's embedded in the
  dashboard).
- **`build_db.py`** — the script that built the database. Re-run it if you
  edit the source figures.

## Scope

**Banks:** Emirates NBD (DFM), Abu Dhabi Commercial Bank (ADX), Dubai Islamic
Bank (DFM). Chosen because all three publish accessible, machine-readable PDF
text (confirmed by direct extraction, not assumed) — as opposed to First Abu
Dhabi Bank, whose own site blocks automated fetching via `robots.txt`.

**Period:** FY2025 vs FY2024, from each bank's audited annual consolidated
financial statements. This is a deliberate scope change from the original
"3 banks / 4 quarters" plan: UAE banks report interim periods cumulatively
(Q1, H1, 9M, FY) rather than as discrete quarters, so getting genuinely
quarterly figures means subtracting cumulative periods from each other — a
real parsing step that was out of scope for this pass. Annual audited figures
are the cleanest, most defensible numbers available and are what's here.

**Metrics:** total assets, total liabilities, total equity, operating
income, operating expenses, impairment charge, profit before tax, net
profit, EPS, net loans/financing, customer deposits. All in AED million.

## Data quality — read before using this anywhere formal

- **Emirates NBD and ADCB**: every figure was read directly off the audited
  consolidated statement of financial position and income statement in the
  linked PDF. No estimation.
- **Dubai Islamic Bank**: the income-statement figures (income, expenses,
  profit, EPS) are read directly from the audited PDF the same way. The
  balance-sheet figures (total assets, liabilities, deposits, financing) are
  **not** — DIB's balance-sheet page extracted with its rows and columns out
  of order on this pass, the same kind of PDF-layout problem flagged earlier
  for ADCB's RTL-sourced filings, just a different failure mode (jumbled
  table flow rather than reversed text). Rather than guess at the scrambled
  numbers, those cells use the rounded figures from DIB's own FY2025 results
  press release instead, and are flagged `EST` in the table and dashboard.
  **Spot-check these against the source PDF before using them for anything
  beyond this demo** — see the To-do section below.
- **DIB total liabilities** specifically is not from any source directly; it's
  computed as `total assets − total equity` to keep the balance sheet
  internally consistent, since the press release doesn't state it. Treat it
  as the least reliable number in the dataset.

## To verify any figure yourself

Every number traces back to one of these three source documents (also linked
in the dashboard's "Source ledger" section):

- Emirates NBD FY2025: https://cdn.emiratesnbd.com/en/assets/file/ir/quarterly/2025/emirates_nbd_financial_statements_q4_2025_english.pdf
- ADCB FY2025: https://apigateway.adx.ae/adx/cdn/1.0/content/download/4676640
- DIB FY2025: https://www.dib.ae/docs/default-source/financial-reports/dib-fs-ye-2025-en.pdf

## Extending this

To add a quarter, a bank, or a metric:

1. Find the filing PDF (bank's own IR page first — cleanest text; ADX's
   `apigateway.adx.ae/.../content/download/<id>` links as fallback if the
   bank's own site blocks bots, which FAB's does and ADCB's now does too).
2. Pull the relevant figures by hand or by extracting the PDF text.
3. Add a row in `build_db.py`'s `rows` list, or insert directly into
   `gcc_banks.db` with any SQLite client.
4. Re-run `build_db.py` to regenerate `financials.csv` and `data.json`, then
   re-embed `data.json` into `dashboard.html` (replace the `DATA = {...}`
   line, or ask for that step to be redone).

## Known limitations / what's not done

- No quarterly (non-cumulative) breakdown — see Scope above.
- No USD convenience columns, even though ADCB's filing includes them.
- DIB balance-sheet figures need the spot-check described above.
- Only 3 banks / 1 sector — matches the "scope it small" advice from the
  planning thread, not a broader index.
- Not investment research or advice — this is a portfolio/CV proof point,
  built to be checkable, not a trading tool.
