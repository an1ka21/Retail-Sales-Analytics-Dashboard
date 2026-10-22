-- Retail Sales Analysis Queries
-- Source grain: one row per Store-Dept-Date from data/processed/retail_sales_clean.csv

-- 1) Overall KPIs
SELECT
	COUNT(*) AS row_count,
	COUNT(DISTINCT Store) AS distinct_stores,
	COUNT(DISTINCT Dept) AS distinct_departments,
	COUNT(DISTINCT Date) AS distinct_dates,
	MIN(Date) AS min_date,
	MAX(Date) AS max_date,
	SUM(Weekly_Sales) AS total_weekly_sales,
	AVG(Weekly_Sales) AS avg_weekly_sales
FROM retail_sales;


-- 2) Monthly sales trends
SELECT
	DATE_TRUNC('month', Date) AS month_start,
	SUM(Weekly_Sales) AS total_sales,
	COUNT(DISTINCT Date) AS distinct_weeks_in_month,
	AVG(Weekly_Sales) AS avg_row_sales
FROM retail_sales
GROUP BY 1
ORDER BY 1;


-- 3a) Sales by store
SELECT
	Store,
	SUM(Weekly_Sales) AS total_sales,
	AVG(Weekly_Sales) AS avg_row_sales,
	COUNT(*) AS row_count
FROM retail_sales
GROUP BY 1
ORDER BY total_sales DESC;


-- 3b) Sales by store type
SELECT
	Type,
	COUNT(DISTINCT Store) AS store_count,
	SUM(Weekly_Sales) AS total_sales,
	AVG(Weekly_Sales) AS avg_row_sales,
	COUNT(*) AS row_count
FROM retail_sales
GROUP BY 1
ORDER BY total_sales DESC;


-- 4) Top 10 departments by sales
SELECT
	Dept,
	SUM(Weekly_Sales) AS total_sales,
	AVG(Weekly_Sales) AS avg_row_sales,
	COUNT(*) AS row_count
FROM retail_sales
GROUP BY 1
ORDER BY total_sales DESC
LIMIT 10;


-- 5) Top and bottom Store-Dept combinations by total sales
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
ORDER BY segment, total_sales DESC;


-- 6) Average total sales per week by holiday flag
-- Important: aggregate to Date first so results are at week level, not row level.
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
ORDER BY 1;


-- 7a) MarkDown availability summary
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
FROM retail_sales;


-- 7b) Sales summary split by markdown availability
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
ORDER BY 1;
