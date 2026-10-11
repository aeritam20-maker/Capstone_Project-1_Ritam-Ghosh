# Mamaearth Returns & Growth Intelligence Pipeline

1. Project Overview

This project analyses Mamaearth-style sales order data using SQL and
Python, creates visual reports, and generates a business-focused
Situation--Complication--Resolution (SCR) narrative. It is designed
so another person can reproduce the reported figures by following the
steps in this README in order.

The project has three main parts:

SQL reporting --- create the database tables, load the CSV data,
and run business reports.

Python analysis and visualisation --- clean the data, check
duplicates and missing values, analyse returns and outliers,
calculate revenue, and create charts.

GenAI narrator --- generate a narrative from the findings using
Gemini, or use a deterministic offline narrative when no API key is
available.

2. Repository Structure

The project should have this structure:

```text
Capstone_Project-1_Ritam-Ghosh/
├── README.md
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json
    └── generate_narrative.py 

```


3. Requirements

Install or prepare the following:

Python 3.10 or later

MySQL Server and MySQL Workbench, or a MySQL command-line client

The CSV files in the data/ directory

Python packages used by the scripts: pandas, matplotlib, and the
Google GenAI SDK (google-genai) for Gemini mode

From the project root, install the Python packages:

python -m pip install pandas matplotlib google-genai

If your system uses python3 rather than python, replace python
with python3 in the commands.

4. Part 1 --- Run the SQL Pipeline

Run the SQL files in this exact order: schema → seed data → reports.

Option A: MySQL Workbench

Open MySQL Workbench and connect to your MySQL Server.

Open sql/schema.sql and execute the complete script. This creates
the database objects required by the project.

Open sql/seed_data.sql and execute the complete script. This loads
the project data into the tables.

Open sql/reports.sql and execute the complete script. Review the
report queries and their results.

If a script expects a particular database to be selected, follow the
database name and USE statement in schema.sql. Do not run the seed
script repeatedly against already-populated tables unless the script or
database has been reset; repeated inserts may create duplicate rows or
primary-key errors.

Option B: MySQL command line

Open a terminal in the project root and run the scripts in order. If the
SQL scripts do not select a database themselves, replace YOUR_DATABASE
with the database created by schema.sql:

mysql -u YOUR_USERNAME -p < sql/schema.sql
mysql -u YOUR_USERNAME -p YOUR_DATABASE < sql/seed_data.sql
mysql -u YOUR_USERNAME -p YOUR_DATABASE < sql/reports.sql

Enter your MySQL password when prompted. If schema.sql creates and
selects the database itself, use the database name it defines for the
later commands.

SQL validation

The raw SQL revenue report should produce a total revenue of
₹99,860.20 for the supplied data. Use the other results in
reports.sql to inspect the customer, product, order, payment-method,
and return patterns.

5. Part 2 --- Run Python Cleaning and EDA

Run the analysis script from the project root so the relative
project paths resolve correctly:

python analysis/clean_and_eda.py

The script loads the CSV files from data/ and performs the cleaning
and analysis tasks, including:

standardising payment-method labels;

identifying and removing duplicate orders according to the project's
natural-key rule;

handling missing discount and rating values;

joining order, product, and customer information;

calculating order revenue;

identifying quantity outliers using the IQR rule;

comparing return rates by payment method and customer segment;

checking correlations and monthly revenue, including the
outlier-corrected trend.

Important: Task 5 of Part 2 must write the calculated findings
automatically to narrator/findings.json. This JSON file is the input
for the narrator in Part 3. It should be generated from the current
analysis results---not maintained by manually typing fixed figures. Run
this script again whenever the input CSV files or analysis logic change.

The expected headline figures for the supplied project data are:

Measure                                                 Expected result

Raw revenue before duplicate removal                         ₹99,860.20
Cleaned revenue after duplicate removal                      ₹97,358.30
Revenue difference reconciled to removed duplicates           ₹2,501.90
COD return rate                                                   44.4%
CARD return rate                                                  14.7%
UPI return rate                                                   18.9%
Highest-risk segment                                        COD, Tier 2
Return rate for COD, Tier 2                                       54.5%
Peak month after quantity-outlier correction                 March 2026
Corrected revenue in March 2026                              ₹20,318.90
January 2026 apparent revenue before correction              ₹29,582.10
January 2026 revenue after correction                        ₹11,637.10

These values are validation targets for the supplied data. If your
results differ, check that you are using the supplied CSVs and that the
scripts ran successfully in the required order.

6. Part 2 --- Create the Visualisations

After clean_and_eda.py has completed successfully, run:

python analysis/visualize.py

The script should save the following files in visualizations/:

return_rate_by_payment.png --- return rate by payment method, with
the rate labels and finding-focused title.

monthly_revenue_trend.png --- monthly revenue after the
quantity-outlier correction, with the peak month identified in the
title.

Run the analysis script first so that the charts and findings are based
on the same current source data.

7. Part 3 --- Generate the SCR Narrative

The narrator reads narrator/findings.json, creates a
Situation--Complication--Resolution narrative, checks the required
numeric facts, and saves the result to narrator/sample_output.txt.

Run it from the project root:

python narrator/generate_narrative.py

Option A: Use Gemini with an API key

Set GEMINI_API_KEY as an environment variable before running the
script. Do not paste the key into the Python file and do not commit it
to GitHub.

Windows PowerShell (current terminal only):

$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
python narrator/generate_narrative.py

macOS/Linux (current terminal only):

export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
python narrator/generate_narrative.py

Replace YOUR_GEMINI_API_KEY with your actual key. These commands set
the variable for the current terminal session. Then run the script. The
script should use Gemini when the key is available, validate the
generated narrative, and save the output to
narrator/sample_output.txt.

Option B: Run without an API key (offline mode)

If GEMINI_API_KEY is not set, run the same command:

python narrator/generate_narrative.py

The script should use generate_scr_narrative_offline(findings)
instead. This path should not make a network request or require an API
key. It produces a deterministic SCR narrative from the JSON findings
and runs the same numeric checks. This is useful for reproducible
testing or when internet/API access is unavailable.

If Gemini returns an error, the script should fall back to the offline
narrative. The script should report whether the numeric accuracy checks
pass and save the resulting narrative to narrator/sample_output.txt.

8. Reproduce the Project from Start to Finish

From a fresh checkout, follow this order:

Confirm the three CSV files are present in data/.

Run sql/schema.sql.

Run sql/seed_data.sql.

Run sql/reports.sql and verify the raw SQL revenue total is
₹99,860.20.

From the project root, run python analysis/clean_and_eda.py.

Confirm that Task 5 has generated or updated
narrator/findings.json.

Run python analysis/visualize.py and confirm both PNG files exist
in visualizations/.

Run python narrator/generate_narrative.py, either with
GEMINI_API_KEY set or with no key for offline mode.

Review narrator/sample_output.txt and confirm that the numeric
accuracy checks pass.

The main reported values to verify are cleaned revenue ₹97,358.30,
COD return rate 44.4%, COD Tier-2 return rate 54.5%, duplicate
reconciliation difference ₹2,501.90, and corrected March 2026
revenue ₹20,318.90.

9. Troubleshooting

A CSV file cannot be found: Run commands from the repository
root and check the filenames and spelling under data/.

findings.json is missing: Run analysis/clean_and_eda.py
first and confirm that its Task 5 export step writes to
narrator/findings.json.

The narrator cannot import google.genai: Install the SDK with
python -m pip install google-genai.

Gemini mode reports an API-key error: Check that
GEMINI_API_KEY is set in the same terminal where the script is
running. You can still run without a key using the offline path.

The numeric checker fails: Inspect narrator/findings.json,
rerun the analysis pipeline, and confirm that the narrative includes
the required figures and March 2026 peak finding.

SQL insert errors occur on a second run: The seed script may
already have inserted the rows. Reset the project database or clear
the relevant tables using an appropriate reset procedure before
reseeding.

10. Data Analysis Summary

The analysis indicates that COD has the highest return rate among the
three payment methods in this dataset. The COD + Tier-2 segment is the
highest-risk segment by return rate. Duplicate removal reconciles the
difference between raw and cleaned revenue. Quantity outliers make
January 2026 appear to be the highest-revenue month; after correction,
March 2026 is the peak month.

These are descriptive findings from the supplied dataset. They show
associations and patterns in the data; they do not, by themselves,
establish that payment method, city tier, or discount levels cause
returns.
