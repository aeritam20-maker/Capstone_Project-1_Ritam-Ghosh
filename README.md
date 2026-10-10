# Mamaearth Returns & Growth Intelligence Pipeline

Mamaearth's Growth Analytics team suspected that returns were eating into margins, but nobody had built a pipeline to prove it. 
So I built one with three layers that feed into each other: a SQL layer for the order data, a Python layer that cleans it and finds the real patterns,
and a GenAI layer that turns the verified numbers into a short business story for the ops and finance heads.

The one rule I followed: no layer reports a number it didn't compute itself or receive from the layer before it.

## What's in this repo

```
├── README.md
├── sql/
│   ├── schema.sql          # creates the 3 tables: customers, products, orders
│   ├── seed_data.sql       # loads the data from the CSVs
│   └── reports.sql         # 9 report queries (a to i), outputs pasted as comments
├── data/                   # raw source files, never edited by hand
│   ├── customers.csv       # 45 rows
│   ├── products.csv        # 16 rows
│   └── orders.csv          # 180 rows
├── analysis/
│   ├── clean_and_eda.py    # cleaning, EDA, and writes narrator/findings.json
│   └── visualize.py        # makes the two charts
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json       # written by clean_and_eda.py, never typed by hand
    └── generate_narrative.py
```

## How to run it (in this order)

Run everything from the root folder of the repo.

**1. SQL layer** (I used SQLite)

```
rm -f mamaearth.db
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 mamaearth.db < sql/reports.sql
```

The first line deletes any old database so the steps can be repeated safely. `reports.sql` must run last, because it adds a `loyalty_tier` column to `customers`. After loading, the table counts should be 45 customers, 16 products and 180 orders.

**2. Analysis layer**

```
pip install pandas matplotlib
python analysis/clean_and_eda.py
python analysis/visualize.py
```

`clean_and_eda.py` prints every intermediate result and writes `narrator/findings.json` at the end. `visualize.py` creates the `visualizations/` folder and saves both charts into it.

**3. Narrator layer**

```
pip install google-genai
export GEMINI_API_KEY=your_free_google_ai_studio_key
python narrator/generate_narrative.py
```

I used the free tier of Google AI Studio, so there is no paid key involved. If there is no API key or no internet, the script falls back to an offline version that writes the same Situation, Complication and Resolution narrative from `findings.json` using a fixed template. That way the pipeline still runs with no network and no cost.

## How the layers connect

- # Mamaearth Returns & Growth Intelligence Pipeline

Mamaearth's Growth Analytics team suspected that returns were eating into margins, but nobody had built a pipeline to prove it. So I built one with three layers that feed into each other: a SQL layer for the order data, a Python layer that cleans it and finds the real patterns, and a GenAI layer that turns the verified numbers into a short business story for the ops and finance heads.

The one rule I followed: no layer reports a number it didn't compute itself or receive from the layer before it.

## What's in this repo

```
├── README.md
├── sql/
│   ├── schema.sql          # creates the 3 tables: customers, products, orders
│   ├── seed_data.sql       # loads the data from the CSVs
│   └── reports.sql         # 9 report queries (a to i), outputs pasted as comments
├── data/                   # raw source files, never edited by hand
│   ├── customers.csv       # 45 rows
│   ├── products.csv        # 16 rows
│   └── orders.csv          # 180 rows
├── analysis/
│   ├── clean_and_eda.py    # cleaning, EDA, and writes narrator/findings.json
│   └── visualize.py        # makes the two charts
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json       # written by clean_and_eda.py, never typed by hand
    └── generate_narrative.py
```

## How to run it (in this order)

Run everything from the root folder of the repo.

**1. SQL layer** (I used SQLite)

```
rm -f mamaearth.db
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 mamaearth.db < sql/reports.sql
```

The first line deletes any old database so the steps can be repeated safely. `reports.sql` must run last, because it adds a `loyalty_tier` column to `customers`. After loading, the table counts should be 45 customers, 16 products and 180 orders.

**2. Analysis layer**

```
pip install pandas matplotlib
python analysis/clean_and_eda.py
python analysis/visualize.py
```

`clean_and_eda.py` prints every intermediate result and writes `narrator/findings.json` at the end. `visualize.py` creates the `visualizations/` folder and saves both charts into it.

**3. Narrator layer**

```
pip install google-genai
export GEMINI_API_KEY=your_free_google_ai_studio_key
python narrator/generate_narrative.py
```

I used the free tier of Google AI Studio, so there is no paid key involved. If there is no API key or no internet, the script falls back to an offline version that writes the same Situation, Complication and Resolution narrative from `findings.json` using a fixed template. That way the pipeline still runs with no network and no cost.

## How the layers connect

- **`data/*.csv` is the single source of truth.** The SQL layer loads it into tables and produces the raw figures. For example, Report (a) gives a raw total revenue of 99,860.20 across 180 orders.
- **The analysis layer reads the same CSVs directly with pandas,** so it doesn't depend on the database and can run before or after the SQL layer. It cleans the data in four steps:
  - payment method casing is standardized, from 7 raw spellings down to 3
  - 5 duplicate orders (O0176 to O0180) are removed, leaving 175 rows
  - missing discounts are filled with 0
  - missing ratings are filled with the median rating
- **The two layers reconcile with each other.** The cleaned total revenue is 97,358.30, which is 2,501.90 lower than the SQL raw total. That gap is exactly the combined value of the 5 duplicate rows, so nothing else changed the revenue.
- **Key findings from the analysis:**
  - COD has the highest return rate at 44.4%, compared with 14.7% for card and 18.9% for UPI.
  - The riskiest segment is COD orders in Tier-2 cities, at 54.5%.
  - January only looks like the best month because of two bulk orders (O0011 and O0098). Once they are excluded, March is the real peak month at 20,318.90.
- **The narrator layer only reads `narrator/findings.json`.** That file is generated by code at the end of `clean_and_eda.py`, so it can't drift from the analysis numbers. The narrator is told to use only those numbers with the same values, so it never invents a statistic.

## Notes

- No API key is stored in this repo. The key is read from the `GEMINI_API_KEY` environment variable.
- The CSVs in `data/` are never modified. All cleaning is done in code, so results can be reproduced from the raw files.
