from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_PATH = PROJECT_ROOT / "sql" / "analysis.sql"
CLEAN_CSV_PATH = PROJECT_ROOT / "data" / "processed" / "retail_sales_clean.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "analysis"

EXPECTED_TOTAL_SALES = 6_737_218_987.11
TOTAL_TOLERANCE = 0.05


QUERIES: dict[str, str] = {
    "overall_kpis": """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT Store) AS distinct_stores,
            COUNT(DISTINCT Dept) AS distinct_departments,
            COUNT(DISTINCT Date) AS distinct_dates,
            MIN(Date) AS min_date,
            MAX(Date) AS max_date,
            SUM(Weekly_Sales) AS total_weekly_sales,
            AVG(Weekly_Sales) AS avg_weekly_sales
        FROM retail_sales
    """,
    "monthly_sales_trends": """
        SELECT
            DATE_TRUNC('month', Date) AS month_start,
            SUM(Weekly_Sales) AS total_sales,
            COUNT(DISTINCT Date) AS distinct_weeks_in_month,
            AVG(Weekly_Sales) AS avg_row_sales
        FROM retail_sales
        GROUP BY 1
        ORDER BY 1
    """,
    "sales_by_store": """
        SELECT
            Store,
            SUM(Weekly_Sales) AS total_sales,
            AVG(Weekly_Sales) AS avg_row_sales,
            COUNT(*) AS row_count
        FROM retail_sales
        GROUP BY 1
        ORDER BY total_sales DESC
    """,
    "sales_by_store_type": """
        SELECT
            Type,
            COUNT(DISTINCT Store) AS store_count,
            SUM(Weekly_Sales) AS total_sales,
            AVG(Weekly_Sales) AS avg_row_sales,
            COUNT(*) AS row_count
        FROM retail_sales
        GROUP BY 1
        ORDER BY total_sales DESC
    """,
    "top_10_departments": """
        SELECT
            Dept,
            SUM(Weekly_Sales) AS total_sales,
            AVG(Weekly_Sales) AS avg_row_sales,
            COUNT(*) AS row_count
        FROM retail_sales
        GROUP BY 1
        ORDER BY total_sales DESC
        LIMIT 10
    """,
    "top_bottom_store_dept": """
        WITH store_dept_sales AS (
            SELECT
                Store,
                Dept,
                SUM(Weekly_Sales) AS total_sales,
                COUNT(*) AS row_count
            FROM retail_sales
            GROUP BY 1, 2
        ),
        top_10 AS (
            SELECT
                'top_10' AS segment,
                Store,
                Dept,
                total_sales,
                row_count
            FROM store_dept_sales
            ORDER BY total_sales DESC
            LIMIT 10
        ),
        bottom_10 AS (
            SELECT
                'bottom_10' AS segment,
                Store,
                Dept,
                total_sales,
                row_count
            FROM store_dept_sales
            ORDER BY total_sales ASC
            LIMIT 10
        )
        SELECT *
        FROM top_10
        UNION ALL
        SELECT *
        FROM bottom_10
        ORDER BY segment, total_sales DESC
    """,
    "holiday_vs_nonholiday_weekly": """
        WITH weekly_totals AS (
            SELECT
                Date,
                MAX(CAST(IsHoliday AS BOOLEAN)) AS is_holiday_week,
                SUM(Weekly_Sales) AS total_sales_week
            FROM retail_sales
            GROUP BY 1
        )
        SELECT
            is_holiday_week,
            COUNT(*) AS week_count,
            AVG(total_sales_week) AS avg_total_sales_per_week,
            MIN(total_sales_week) AS min_total_sales_per_week,
            MAX(total_sales_week) AS max_total_sales_per_week
        FROM weekly_totals
        GROUP BY 1
        ORDER BY 1
    """,
    "markdown_availability_summary": """
        SELECT
            COUNT(*) AS row_count,
            SUM(CASE WHEN MarkDown1 IS NULL THEN 1 ELSE 0 END) AS markdown1_missing,
            SUM(CASE WHEN MarkDown2 IS NULL THEN 1 ELSE 0 END) AS markdown2_missing,
            SUM(CASE WHEN MarkDown3 IS NULL THEN 1 ELSE 0 END) AS markdown3_missing,
            SUM(CASE WHEN MarkDown4 IS NULL THEN 1 ELSE 0 END) AS markdown4_missing,
            SUM(CASE WHEN MarkDown5 IS NULL THEN 1 ELSE 0 END) AS markdown5_missing,
            SUM(
                CASE
                    WHEN MarkDown1 IS NULL
                     AND MarkDown2 IS NULL
                     AND MarkDown3 IS NULL
                     AND MarkDown4 IS NULL
                     AND MarkDown5 IS NULL THEN 1
                    ELSE 0
                END
            ) AS all_markdowns_missing_rows,
            SUM(
                CASE
                    WHEN MarkDown1 IS NOT NULL
                      OR MarkDown2 IS NOT NULL
                      OR MarkDown3 IS NOT NULL
                      OR MarkDown4 IS NOT NULL
                      OR MarkDown5 IS NOT NULL THEN 1
                    ELSE 0
                END
            ) AS any_markdown_present_rows
        FROM retail_sales
    """,
    "markdown_sales_summary": """
        SELECT
            CASE
                WHEN MarkDown1 IS NULL
                 AND MarkDown2 IS NULL
                 AND MarkDown3 IS NULL
                 AND MarkDown4 IS NULL
                 AND MarkDown5 IS NULL THEN 'all_markdowns_missing'
                ELSE 'any_markdown_present'
            END AS markdown_group,
            COUNT(*) AS row_count,
            SUM(Weekly_Sales) AS total_sales,
            AVG(Weekly_Sales) AS avg_row_sales
        FROM retail_sales
        GROUP BY 1
        ORDER BY 1
    """,
}


def _validate_inputs() -> None:
    if not CLEAN_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {CLEAN_CSV_PATH}. Run clean_data.py first."
        )
    if not SQL_PATH.exists():
        raise FileNotFoundError(f"SQL file not found: {SQL_PATH}")


def _print_dataframe_preview(name: str, df: pd.DataFrame, max_rows: int = 5) -> None:
    print(f"\n{name} (rows={len(df):,})")
    if df.empty:
        print("Result is empty.")
    else:
        print(df.head(max_rows).to_string(index=False))


def main() -> None:
    _validate_inputs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Reading cleaned CSV: {CLEAN_CSV_PATH}")
    print(f"Documented SQL file: {SQL_PATH}")
    print(f"Output directory: {OUTPUT_DIR}")

    con = duckdb.connect(database=":memory:")

    clean_csv_sql_path = str(CLEAN_CSV_PATH).replace("\\", "\\\\")
    con.execute(
        f"""
        CREATE VIEW retail_sales AS
        SELECT *
        FROM read_csv_auto('{clean_csv_sql_path}', header=TRUE)
        """
    )

    validation = con.execute(
        """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT Store || '|' || Dept || '|' || CAST(Date AS VARCHAR)) AS distinct_grain_count,
            SUM(Weekly_Sales) AS total_sales,
            MIN(Date) AS min_date,
            MAX(Date) AS max_date
        FROM retail_sales
        """
    ).fetchdf()

    row_count = int(validation.loc[0, "row_count"])
    distinct_grain_count = int(validation.loc[0, "distinct_grain_count"])
    total_sales = float(validation.loc[0, "total_sales"])

    print("\n=== Validation checks ===")
    print(f"Row count: {row_count:,}")
    print(f"Distinct Store-Dept-Date grain count: {distinct_grain_count:,}")
    print(f"Date range: {validation.loc[0, 'min_date']} to {validation.loc[0, 'max_date']}")
    print(f"Total Weekly_Sales from SQL: {total_sales:,.2f}")

    assert row_count == distinct_grain_count, (
        "Source grain violation: duplicate Store-Dept-Date rows detected in cleaned CSV."
    )

    diff = abs(total_sales - EXPECTED_TOTAL_SALES)
    assert diff <= TOTAL_TOLERANCE, (
        "Total Weekly_Sales mismatch. "
        f"Expected {EXPECTED_TOTAL_SALES:,.2f}, got {total_sales:,.2f}, diff {diff:.6f}."
    )

    print(
        f"Total sales validation passed within tolerance {TOTAL_TOLERANCE:.2f}. "
        f"Absolute diff: {diff:.6f}"
    )

    print("\n=== Running analysis queries ===")
    for name, query in QUERIES.items():
        df = con.execute(query).fetchdf()
        output_path = OUTPUT_DIR / f"{name}.csv"
        df.to_csv(output_path, index=False)
        print(f"Saved {name}: {len(df):,} rows -> {output_path}")

        if name in {
            "overall_kpis",
            "holiday_vs_nonholiday_weekly",
            "markdown_availability_summary",
            "markdown_sales_summary",
            "top_10_departments",
        }:
            _print_dataframe_preview(name, df, max_rows=10)

    print("\nAnalysis completed successfully.")


if __name__ == "__main__":
    main()
