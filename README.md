# Retail Sales Analytics

An end-to-end retail analytics project that cleans weekly sales data, validates data quality, runs SQL-based analysis with DuckDB, and produces business-facing findings.

## Project Overview
This project analyzes historical retail performance at the Store-Department-Week level. It combines data engineering, analytical SQL, and business reporting to answer questions such as:

- How much did the business sell in total?
- Which stores and departments contribute the most?
- How do holiday weeks compare with non-holiday weeks?
- How complete is markdown (promotion) data, and how should it be interpreted?

The project is designed for reproducibility and transparency:

- Cleaning scripts include assertions and validation checks.
- Analysis scripts verify totals and export traceable result tables.
- Business findings are documented and independently audited against SQL outputs.

## Power BI Dashboard
Power BI dashboard link (to be added once dashboard is published):

- TBD

## What Has Been Done
The following pipeline is fully implemented:

1. Raw data cleaning and merge
	- Loads train, features, and stores files.
	- Parses dates and validates required columns.
	- Checks duplicate keys and merge cardinality.
	- Compares duplicated holiday flags before resolving them.
	- Preserves sales row count and sales total through assertions.
	- Handles markdown missing values carefully (does not blindly force all missing to zero).
2. Analytical SQL output generation (DuckDB)
	- Computes overall KPIs, monthly trends, store/store-type performance, department rankings, holiday comparison, and markdown summaries.
	- Exports each query result to CSV for downstream reporting.
3. Business reporting and validation
	- Produces a business findings report.
	- Produces a claim-by-claim validation report against SQL outputs.

## Repository Structure
```text
retail-sales-analytics/
├── data/
│   ├── raw/                           # Input files (train, features, stores, test)
│   └── processed/
│       ├── retail_sales_clean.csv     # Clean merged analytical dataset
│       ├── retail_sales_powerbi.csv   # Power BI-friendly companion dataset
│       └── analysis/                  # SQL output tables as CSVs
├── python/
│   ├── clean_data.py                  # Data cleaning + validation pipeline
│   ├── run_analysis.py                # DuckDB analysis runner + exports
│   └── analysis.py                    # Reserved/legacy file (currently empty)
├── sql/
│   └── analysis.sql                   # Documented SQL query set
├── reports/
│   ├── retail_sales_findings.md       # Business findings report
│   └── report_validation.md           # Audit of report claims vs SQL outputs
└── README.md
```

## Data Scope and Grain
- Observation grain: one row per Store-Dept-Date (weekly).
- This is not individual customer transaction data.
- Coverage in cleaned dataset:
  - Rows: 421,570
  - Stores: 45
  - Departments: 81
  - Weekly dates: 143
  - Date range: 2010-02-05 to 2012-10-26

## Tech Stack
- Python (pandas)
- DuckDB (SQL analytics)
- Markdown reporting
- Power BI (planned dashboarding)

## Setup
1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies from requirements.txt.
4. Ensure raw input files exist in data/raw:
	- train.csv
	- features.csv
	- stores.csv

Example (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## How to Run
### Step 1: Clean and merge data
Run from project root:

```powershell
python python/clean_data.py
```

Outputs:
- data/processed/retail_sales_clean.csv
- data/processed/retail_sales_powerbi.csv

### Step 2: Run SQL analysis
Run from project root:

```powershell
python python/run_analysis.py
```

Outputs are exported to data/processed/analysis:
- overall_kpis.csv
- monthly_sales_trends.csv
- sales_by_store.csv
- sales_by_store_type.csv
- top_10_departments.csv
- top_bottom_store_dept.csv
- holiday_vs_nonholiday_weekly.csv
- markdown_availability_summary.csv
- markdown_sales_summary.csv

## Validation and Data Quality Safeguards
The pipeline includes explicit checks to avoid silent errors:

- Required file and column checks.
- Duplicate key checks on expected grains.
- Merge cardinality validation (many-to-one where required).
- IsHoliday conflict detection between sources.
- Row-count preservation checks through merges.
- Sales total preservation checks.
- SQL total cross-check against expected overall sales with tolerance.

If checks fail, scripts raise clear error messages instead of silently dropping or altering records.

## Business Findings Report
Primary report:
- reports/retail_sales_findings.md

Independent claim audit:
- reports/report_validation.md

The findings report is written for business readers and clearly distinguishes descriptive comparisons from causal conclusions.

## Key Findings Snapshot
From the current validated outputs:

- Total weekly sales: 6,737,218,987.11
- Holiday weeks show higher average total weekly sales than non-holiday weeks (descriptive comparison).
- Sales are concentrated in specific stores, store types, and department IDs.
- Markdown fields contain substantial missingness, so markdown-based interpretation is treated cautiously.

For full numbers and evidence, refer to:
- data/processed/analysis/
- reports/retail_sales_findings.md
- reports/report_validation.md

## Notes and Limitations
- Department values are numeric IDs; no department-name mapping is assumed.
- Dataset is observational and aggregated weekly; it is not customer-level behavioral data.
- Markdown missing values may represent different real-world states (no promo vs unknown), so they should not be interpreted naively.

## Next Steps
- Publish the Power BI dashboard and replace the placeholder link.
- Add dashboard screenshots and usage notes.
- Extend analysis with forecasting or causal methods if decision support requires effect estimation.
