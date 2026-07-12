import sqlite3, json, csv

conn = sqlite3.connect('gcc_banks.db')
cur = conn.cursor()

cur.executescript('''
DROP TABLE IF EXISTS banks;
DROP TABLE IF EXISTS financials;

CREATE TABLE banks (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    exchange TEXT NOT NULL,
    source_pdf_url TEXT NOT NULL,
    filing_type TEXT NOT NULL
);

CREATE TABLE financials (
    ticker TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'AED',
    unit TEXT NOT NULL DEFAULT 'million',
    total_assets REAL,
    total_liabilities REAL,
    total_equity REAL,
    total_operating_income REAL,
    operating_expenses REAL,
    impairment_charge REAL,
    profit_before_tax REAL,
    net_profit REAL,
    eps REAL,
    loans_or_financing_net REAL,
    customer_deposits REAL,
    is_estimated INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(ticker) REFERENCES banks(ticker)
);
''')

banks = [
    ("EMIRATESNBD", "Emirates NBD", "DFM",
     "https://cdn.emiratesnbd.com/en/assets/file/ir/quarterly/2025/emirates_nbd_financial_statements_q4_2025_english.pdf",
     "Audited consolidated financial statements FY2025 (incl. FY2024 comparatives)"),
    ("ADCB", "Abu Dhabi Commercial Bank", "ADX",
     "https://apigateway.adx.ae/adx/cdn/1.0/content/download/4676640",
     "Audited consolidated financial statements FY2025 (incl. FY2024 comparatives)"),
    ("DIB", "Dubai Islamic Bank", "DFM",
     "https://www.dib.ae/docs/default-source/financial-reports/dib-fs-ye-2025-en.pdf",
     "Audited consolidated financial statements FY2025 (incl. FY2024 comparatives)"),
]
cur.executemany("INSERT INTO banks VALUES (?,?,?,?,?)", banks)

# All figures in AED million unless noted. is_estimated=1 flags figures derived from
# rounded press-release percentages rather than read directly off the audited statement line item.
rows = [
    # ticker, year, currency, unit, total_assets, total_liabilities, total_equity,
    # total_operating_income, operating_expenses, impairment_charge, profit_before_tax,
    # net_profit, eps, loans_or_financing_net, customer_deposits, is_estimated
    ("EMIRATESNBD", 2025, "AED", "million", 1164442, 1019623, 144819, 49319, 15035, 1468, 29838, 24007, 3.71, 632847, 786024, 0),
    ("EMIRATESNBD", 2024, "AED", "million", 996582, 870368, 126214, 44134, 13751, 106, 27141, 23008, 3.56, 501627, 666777, 0),

    ("ADCB", 2025, "AED", "million", 773654, 684913, 88741, 22183, 6246, 3103, 12843, 11445, 1.45, 405967, 499775, 0),
    ("ADCB", 2024, "AED", "million", 652814, 577247, 75567, 19479, 6031, 2874, 10585, 9419, 1.17, 350638, 421060, 0),

    ("DIB", 2025, "AED", "million", 416000, 362865, 53135, 23826.774, 3762.769, 485.446, 9002.654, 7807.542, 0.98, 353000, 320000, 1),
    ("DIB", 2024, "AED", "million", 343800, 290947, 52853, 23341.102, 3424.803, 406.813, 9004.924, 8165.038, 1.04, 295000, 267000, 1),
]
cur.executemany('''INSERT INTO financials
    (ticker, fiscal_year, currency, unit, total_assets, total_liabilities, total_equity,
     total_operating_income, operating_expenses, impairment_charge, profit_before_tax,
     net_profit, eps, loans_or_financing_net, customer_deposits, is_estimated)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', rows)

conn.commit()

# Sanity check: DIB total_liabilities was derived (assets - equity), fix ADCB total_liabilities cross-check
cur.execute("SELECT ticker, fiscal_year, total_assets, total_liabilities, total_equity, total_assets-total_liabilities-total_equity AS residual FROM financials")
for r in cur.fetchall():
    print(r)

conn.close()
