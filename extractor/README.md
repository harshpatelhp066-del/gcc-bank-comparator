# PDF Financial Statement Extractor

An automated parser that pulls financial statement line items directly out of
real audited bank PDF filings — no manual transcription. This is the
"how the numbers actually got into `gcc_banks.db`" layer underneath the
GCC Bank Comparator, built to replace hand-copying with code.

## What it does

`extractor.py` takes raw text extracted from a bank's PDF filing and, using a
per-bank label configuration (bank terminology genuinely differs — ADCB says
"Operating income", DIB says "Total income" for the equivalent line), regexes
out each financial statement line item as a `(FY2025, FY2024)` pair.

`validate.py` then cross-checks every extracted value against
`gcc_banks.db` — the same figures, already read and entered by hand earlier
in this project — and reports a match/mismatch for each field.

## Results, run against the real PDFs

**56 / 56 extracted values matched the manually verified database (100%)**,
across all three banks, once the label config and regex were correct. See
`validation_report.txt` for the full field-by-field diff.

Coverage isn't total, though, and that's disclosed rather than hidden:

- **DIB's balance sheet (total assets, liabilities, financing, deposits)
  isn't in this parser's output at all.** Page 7 of DIB's PDF has not
  extracted as parseable text on any fetch attempt (3 tries, different
  settings) — it isn't there to regex against. Those fields stay sourced
  from DIB's press release, same as before, still flagged `is_estimated`.
- **DIB's total equity** isn't extracted either — it lives inside a
  multi-column statement-of-changes-in-equity table (10+ columns per row),
  a genuinely different parsing problem from the simple "label: value value"
  lines this regex approach handles. A real fix would need actual table
  structure recovery, not a label regex.

## Bugs found and fixed while building this — kept in, on purpose

A parser that "worked on the first try" against real filings would be a red
flag, not an achievement. Three real bugs came up during testing against
actual fetched PDF text, all now fixed in `extractor.py`:

1. **Substring collision**: an unanchored search for "Operating income"
   silently matched inside "**Other** operating income" — a different line
   item entirely. Fixed by anchoring the label to the start of a line.
2. **Swallowed real data**: the optional pattern meant to skip a unit tag
   like `(AED)` before EPS values was written loosely enough that it also
   matched a real parenthesized negative number like `(3,762,769)`, eating
   the actual figure. Fixed by requiring the parenthetical to contain
   letters, not just digits.
3. **A number split in two**: regex backtracking could split one token like
   `3,424,803` into `3,424` + `803` when the pattern needed two numbers but
   only one was actually present on the line. Fixed by requiring number
   tokens to start on a digit boundary, not mid-sequence.

## One correction to an earlier claim in this project

The original README asserted ADCB's PDF has a right-to-left text-direction
artifact that reverses word order per line (e.g. "assets Total" instead of
"Total assets"). Re-testing the actual PDF for this extraction engine, the
text came back completely clean — normal word order throughout, no reversal.
Whether that was fixed on ADX's end, was specific to a different filing, or
was simply inaccurate the first time isn't fully clear from this pass, but
the claim didn't hold up under a fresh check, so it's corrected here rather
than carried forward silently.

## Architecture note

PDF fetching and PDF parsing are deliberately separate. In this sandboxed
build, fetching used Claude's own `web_fetch` tool, since the sandbox's
general-purpose network doesn't reach `dib.ae` / `adx.ae` /
`emiratesnbd.com` directly. The parsing logic in `extractor.py` has zero
network dependency and zero knowledge of how the text arrived — on a normal
machine, the same functions run unchanged against text from
`pdfplumber.open(path).pages[i].extract_text()`.

## Files

- `extractor.py` — the extraction engine + per-bank field label config
- `validate.py` — cross-checks output against `gcc_banks.db`
- `raw_text/*.txt` — real extracted PDF text used for testing (income
  statement + balance sheet pages, trimmed of unrelated content like
  accounting-policy notes)
- `validation_report.txt` — full field-by-field match report
