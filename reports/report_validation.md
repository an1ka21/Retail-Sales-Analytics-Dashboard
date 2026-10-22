# Report Validation Audit

Scope: audit of [reports/retail_sales_findings.md](reports/retail_sales_findings.md) against SQL output CSVs in [data/processed/analysis](data/processed/analysis).

Validation statuses:
- PASS: stated claim matches available SQL output (allowing normal rounding in report formatting).
- FAIL: stated claim conflicts with available SQL output.
- UNVERIFIABLE: claim cannot be directly established from available SQL outputs alone.

## Claim-by-Claim Evidence Table

| # | Claim in report | SQL source file and column(s) | Value stated in report | Value in SQL output | Status | Explanation |
|---|---|---|---|---|---|---|
| 1 | Dataset has 421,570 observations | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): row_count | 421,570 | 421,570 | PASS | Exact match. |
| 2 | 45 stores | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): distinct_stores | 45 | 45 | PASS | Exact match. |
| 3 | 81 departments | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): distinct_departments | 81 | 81 | PASS | Exact match. |
| 4 | 143 weekly dates | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): distinct_dates | 143 | 143 | PASS | Exact match. |
| 5 | Date range 2010-02-05 to 2012-10-26 | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): min_date, max_date | 2010-02-05 to 2012-10-26 | 2010-02-05 to 2012-10-26 | PASS | Exact match. |
| 6 | Total weekly sales 6,737,218,987.11 | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): total_weekly_sales | 6,737,218,987.11 | 6,737,218,987.110066 | PASS | Match within rounding (difference 0.000066). |
| 7 | Holiday weeks have higher average total weekly sales than non-holiday weeks | [holiday_vs_nonholiday_weekly.csv](data/processed/analysis/holiday_vs_nonholiday_weekly.csv): avg_total_sales_per_week by is_holiday_week | Holiday > non-holiday | True: 50,529,955.156 vs False: 46,856,537.10939849 | PASS | Direction is correct. |
| 8 | Findings are descriptive, not causal | Textual framing only | Non-causal framing | N/A | PASS | No causal numeric claim is made; report explicitly avoids causal wording. |
| 9 | Observation grain is Store-Dept-Date weekly | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): row_count; plus pipeline validation output | Store-Dept-Date | row_count = 421,570; distinct grain reported as 421,570 in analysis run logs | PASS | Consistent with SQL outputs and analysis validation. |
| 10 | Not individual customer transactions | Not directly encoded in analysis CSVs | Not transactions | N/A | UNVERIFIABLE | CSV outputs do not include transaction-level fields, but absence of such fields is not definitive proof. |
| 11 | Row count validation check = 421,570 | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): row_count | 421,570 | 421,570 | PASS | Exact match. |
| 12 | Distinct Store-Dept-Date combinations = 421,570 | Not present as a column in exported analysis CSVs | 421,570 | N/A in exported CSVs | UNVERIFIABLE | This was printed by script validation, but not persisted in analysis CSVs. |
| 13 | Total sales cross-check vs expected within tolerance | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): total_weekly_sales | Within tolerance | total_weekly_sales = 6,737,218,987.110066 | PASS | Matches expected to cent-level and beyond; tolerance value itself is not stored in CSV but numeric consistency is present. |
| 14 | Weekly holiday comparison aggregates to Date first | Not directly encoded in output CSV structure | Date-first weekly aggregation | week_count False+True = 133+10 = 143 | PASS | Output shape (143 total weeks) supports week-level aggregation; consistent with documented method. |
| 15 | No join fan-out duplication in analysis step | Indirectly supported by output totals and row counts | No duplication | total and row counts consistent with source summary | PASS | Analysis outputs are internally consistent; no evidence of duplication from result tables. |
| 16 | Average sales per Store-Dept-Date row = 15,981.26 | [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): avg_weekly_sales | 15,981.26 | 15,981.258123467198 | PASS | Correctly rounded to 2 decimals. |
| 17 | Store 20 largest at 301.40M | [sales_by_store.csv](data/processed/analysis/sales_by_store.csv): first row Store,total_sales | 301.40M | Store 20, 301,397,792.4600005 | PASS | Largest store and value match after rounding to millions. |
| 18 | Store 20 share = 4.47% of total | [sales_by_store.csv](data/processed/analysis/sales_by_store.csv): Store 20 total_sales; [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): total_weekly_sales | 4.47% | 301,397,792.4600005 / 6,737,218,987.110066 = 4.473623% | PASS | Correctly rounded. |
| 19 | Top 3 stores are 20, 4, 14 | [sales_by_store.csv](data/processed/analysis/sales_by_store.csv): ordered top rows | 20, 4, 14 | 20, 4, 14 | PASS | Exact ranking match. |
| 20 | Top 3 store share = 13.21% | [sales_by_store.csv](data/processed/analysis/sales_by_store.csv): top 3 total_sales; [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): total_weekly_sales | 13.21% | (301,397,792.46 + 299,543,953.38 + 288,999,911.34) / 6,737,218,987.110066 = 13.209332% | PASS | Correctly rounded. |
| 21 | Type A sales 4,331.01M (64.28%) | [sales_by_store_type.csv](data/processed/analysis/sales_by_store_type.csv): Type A total_sales; [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): total_weekly_sales | 4,331.01M (64.28%) | 4,331,014,722.7500105 and 64.284903% | PASS | Amount and percent correctly rounded. |
| 22 | Type B sales 2,000.70M (29.70%) | [sales_by_store_type.csv](data/processed/analysis/sales_by_store_type.csv): Type B total_sales; [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): total_weekly_sales | 2,000.70M (29.70%) | 2,000,700,736.820011 and 29.696240% | PASS | Correctly rounded. |
| 23 | Type C sales 405.50M (6.02%) | [sales_by_store_type.csv](data/processed/analysis/sales_by_store_type.csv): Type C total_sales; [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): total_weekly_sales | 405.50M (6.02%) | 405,503,527.5399969 and 6.018856% | PASS | Correctly rounded. |
| 24 | Holiday avg total weekly sales 50.53M (10 weeks) | [holiday_vs_nonholiday_weekly.csv](data/processed/analysis/holiday_vs_nonholiday_weekly.csv): is_holiday_week=True row | 50.53M, 10 | 50,529,955.156 and 10 | PASS | Correct and rounded. |
| 25 | Non-holiday avg total weekly sales 46.86M (133 weeks) | [holiday_vs_nonholiday_weekly.csv](data/processed/analysis/holiday_vs_nonholiday_weekly.csv): is_holiday_week=False row | 46.86M, 133 | 46,856,537.10939849 and 133 | PASS | Correct and rounded. |
| 26 | Holiday weeks are 7.84% higher on average | [holiday_vs_nonholiday_weekly.csv](data/processed/analysis/holiday_vs_nonholiday_weekly.csv): avg_total_sales_per_week | 7.84% | (50,529,955.156 - 46,856,537.10939849) / 46,856,537.10939849 = 7.839713% | PASS | Correctly rounded. |
| 27 | Rows with all MarkDown1-5 missing = 270,138 (64.08%) | [markdown_availability_summary.csv](data/processed/analysis/markdown_availability_summary.csv): all_markdowns_missing_rows,row_count | 270,138 (64.08%) | 270,138 and 270,138/421,570 = 64.079038% | PASS | Correctly rounded. |
| 28 | Rows with any markdown present = 151,432 (35.92%) | [markdown_availability_summary.csv](data/processed/analysis/markdown_availability_summary.csv): any_markdown_present_rows,row_count | 151,432 (35.92%) | 151,432 and 151,432/421,570 = 35.920962% | PASS | Correctly rounded. |
| 29 | Sales from rows with any markdown present = 2,449.72M (36.36% of total) | [markdown_sales_summary.csv](data/processed/analysis/markdown_sales_summary.csv): any_markdown_present total_sales; [overall_kpis.csv](data/processed/analysis/overall_kpis.csv): total_weekly_sales | 2,449.72M (36.36%) | 2,449,717,772.3999996 and 36.360964% | PASS | Correctly rounded. |
| 30 | Top stores: 20 (301.40M), 4 (299.54M), 14 (289.00M) | [sales_by_store.csv](data/processed/analysis/sales_by_store.csv): rows for stores 20,4,14 | As stated | 301,397,792.46; 299,543,953.38; 288,999,911.34 | PASS | All values and ranking match after rounding. |
| 31 | Top departments list and ranking: 92,95,38,72,90 | [top_10_departments.csv](data/processed/analysis/top_10_departments.csv): Dept order by total_sales | 92,95,38,72,90 | 92,95,38,72,90 in top 5 | PASS | Exact ranking match. |
| 32 | Department totals: 92 (483.94M), 95 (449.32M), 38 (393.12M), 72 (305.73M), 90 (291.07M) | [top_10_departments.csv](data/processed/analysis/top_10_departments.csv): total_sales for listed depts | As stated | 483,943,341.87; 449,320,162.52; 393,118,136.92; 305,725,152.21; 291,068,463.68 | PASS | Correctly rounded. |
| 33 | Top Store-Dept examples: (14,92)=26.10M; (2,92)=23.57M; (20,92)=23.54M | [top_bottom_store_dept.csv](data/processed/analysis/top_bottom_store_dept.csv): top_10 rows | As stated | 26,101,497.71; 23,572,153.03; 23,542,625.04 | PASS | Correctly rounded. |
| 34 | Bottom example: Store 35, Dept 47 = -3,567.18 | [top_bottom_store_dept.csv](data/processed/analysis/top_bottom_store_dept.csv): bottom_10 row | -3,567.18 | -3,567.1799999999994 | PASS | Correct after rounding. |
| 35 | Non-holiday min/max weekly totals: 39.60M / 80.93M | [holiday_vs_nonholiday_weekly.csv](data/processed/analysis/holiday_vs_nonholiday_weekly.csv): False row min,max | 39.60M / 80.93M | 39,599,852.99 / 80,931,415.60 | PASS | Correctly rounded. |
| 36 | Holiday min/max weekly totals: 40.43M / 66.59M | [holiday_vs_nonholiday_weekly.csv](data/processed/analysis/holiday_vs_nonholiday_weekly.csv): True row min,max | 40.43M / 66.59M | 40,432,518.99999999 / 66,593,605.25999999 | PASS | Correctly rounded. |
| 37 | Missing markdowns may mean no promotion, missing capture, or reporting gaps | Not derivable from analysis outputs alone | Possible interpretations | N/A | UNVERIFIABLE | This is a reasonable caveat but not testable from available output tables. |
| 38 | Recommendation framing relies on descriptive evidence (not proven causality) | Textual framing only | Recommendations, not proofs | N/A | PASS | Recommendations are presented as practical actions, not proven causal effects. |
| 39 | Department IDs are numeric codes; no department-name mapping used | [top_10_departments.csv](data/processed/analysis/top_10_departments.csv): Dept numeric IDs | Numeric IDs only | Dept values are numeric (e.g., 92,95,38...) | PASS | No invented department names found in report. |
| 40 | Observational summaries do not control for confounders | Not directly encoded in analysis outputs | No confounder control claim | N/A | UNVERIFIABLE | Methodological statement cannot be proven solely from result CSVs. |

## Focused Checks Requested

- Total sales: PASS.
- Row count: PASS.
- Date range: PASS.
- Distinct store and department counts: PASS.
- Top department ranking: PASS.
- Holiday comparison (including % uplift): PASS.
- Markdown missingness and markdown-related shares: PASS.
- Every numerical claim reviewed: no numerical mismatches found.

## Explicit Risk Flags

- Unsupported causal claims: none detected; report consistently uses descriptive language.
- Invented department names: none detected.
- Incorrect aggregation grain: none detected in stated results; holiday analysis is consistent with weekly aggregation output.
- Recommendations presented as proven facts: not detected; recommendations are framed as practical actions.

## Summary
All numeric claims in the report that are checkable from [data/processed/analysis](data/processed/analysis) are validated (PASS) with rounding-consistent agreement. UNVERIFIABLE items are methodological or interpretive statements that cannot be strictly proved from the output CSVs alone.
