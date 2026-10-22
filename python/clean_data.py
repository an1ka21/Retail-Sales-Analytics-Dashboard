from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TRAIN_PATH = RAW_DIR / "train.csv"
FEATURES_PATH = RAW_DIR / "features.csv"
STORES_PATH = RAW_DIR / "stores.csv"

OUTPUT_CLEAN_PATH = PROCESSED_DIR / "retail_sales_clean.csv"
OUTPUT_POWERBI_PATH = PROCESSED_DIR / "retail_sales_powerbi.csv"

TRAIN_REQUIRED_COLUMNS = {
	"Store",
	"Dept",
	"Date",
	"Weekly_Sales",
	"IsHoliday",
}

FEATURES_REQUIRED_COLUMNS = {
	"Store",
	"Date",
	"Temperature",
	"Fuel_Price",
	"MarkDown1",
	"MarkDown2",
	"MarkDown3",
	"MarkDown4",
	"MarkDown5",
	"CPI",
	"Unemployment",
	"IsHoliday",
}

STORES_REQUIRED_COLUMNS = {
	"Store",
	"Type",
	"Size",
}

MARKDOWN_COLUMNS = ["MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5"]


def _require_file(path: Path) -> None:
	if not path.exists():
		raise FileNotFoundError(
			f"Required input file is missing: {path}. "
			"Place the file in data/raw and rerun."
		)


def _require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
	missing = required - set(df.columns)
	if missing:
		missing_sorted = sorted(missing)
		raise ValueError(
			f"{name} is missing required columns: {missing_sorted}. "
			f"Found columns: {list(df.columns)}"
		)


def _print_dataset_overview(
	train_df: pd.DataFrame,
	features_df: pd.DataFrame,
	stores_df: pd.DataFrame,
) -> None:
	print("=== Raw dataset overview ===")
	print(f"train rows: {len(train_df):,}")
	print(f"features rows: {len(features_df):,}")
	print(f"stores rows: {len(stores_df):,}")
	print(
		"train date range: "
		f"{train_df['Date'].min().date()} to {train_df['Date'].max().date()}"
	)
	print(
		"features date range: "
		f"{features_df['Date'].min().date()} to {features_df['Date'].max().date()}"
	)
	print(f"train distinct stores: {train_df['Store'].nunique():,}")
	print(f"train distinct departments: {train_df['Dept'].nunique():,}")
	print()


def _validate_keys(
	train_df: pd.DataFrame,
	features_df: pd.DataFrame,
	stores_df: pd.DataFrame,
) -> None:
	print("=== Key and duplicate checks ===")
	train_dup_count = train_df.duplicated(["Store", "Dept", "Date"]).sum()
	features_dup_count = features_df.duplicated(["Store", "Date"]).sum()
	stores_dup_count = stores_df.duplicated(["Store"]).sum()

	print(f"train duplicate keys (Store, Dept, Date): {train_dup_count:,}")
	print(f"features duplicate keys (Store, Date): {features_dup_count:,}")
	print(f"stores duplicate keys (Store): {stores_dup_count:,}")

	assert train_dup_count == 0, (
		"Duplicate sales records found in train.csv for key "
		"(Store, Dept, Date). Resolve duplicates before merging."
	)
	assert features_dup_count == 0, (
		"Duplicate records found in features.csv for key (Store, Date). "
		"This breaks many-to-one merge cardinality."
	)
	assert stores_dup_count == 0, (
		"Duplicate records found in stores.csv for key (Store). "
		"This breaks many-to-one merge cardinality."
	)

	missing_store_in_features = (
		train_df["Store"].drop_duplicates().isin(features_df["Store"].drop_duplicates())
	)
	missing_store_count = (~missing_store_in_features).sum()
	print(f"train stores missing in features: {missing_store_count:,}")

	missing_store_in_stores = (
		train_df["Store"].drop_duplicates().isin(stores_df["Store"].drop_duplicates())
	)
	missing_store_master_count = (~missing_store_in_stores).sum()
	print(f"train stores missing in stores master: {missing_store_master_count:,}")

	assert missing_store_count == 0, (
		"At least one Store in train.csv has no matching Store in features.csv. "
		"Cannot safely perform full merge."
	)
	assert missing_store_master_count == 0, (
		"At least one Store in train.csv has no matching Store in stores.csv. "
		"Cannot safely enrich with store attributes."
	)
	print()


def _print_missing_values(df: pd.DataFrame, title: str) -> pd.Series:
	missing = df.isna().sum().sort_values(ascending=False)
	print(title)
	print(missing[missing > 0] if (missing > 0).any() else "No missing values")
	print()
	return missing


def _merge_and_validate(
	train_df: pd.DataFrame,
	features_df: pd.DataFrame,
	stores_df: pd.DataFrame,
) -> pd.DataFrame:
	train_rows_before = len(train_df)
	sales_total_before = train_df["Weekly_Sales"].sum()

	merged = train_df.merge(
		features_df,
		on=["Store", "Date"],
		how="left",
		validate="many_to_one",
		indicator=True,
		suffixes=("_sales", "_features"),
	)

	merge_status = merged["_merge"].value_counts().to_dict()
	print("=== Merge status: train + features ===")
	print(merge_status)
	print()

	assert merge_status.get("left_only", 0) == 0, (
		"Some sales rows in train.csv did not find a match in features.csv "
		"on (Store, Date)."
	)
	assert len(merged) == train_rows_before, (
		"Row count changed after merging train and features. "
		f"Expected {train_rows_before:,}, found {len(merged):,}."
	)

	# Keep sales-side holiday flag only after confirming it matches features.
	holiday_mismatch = (
		merged["IsHoliday_sales"].astype(str).str.upper()
		!= merged["IsHoliday_features"].astype(str).str.upper()
	).sum()
	print(f"IsHoliday mismatches between train/features: {holiday_mismatch:,}")
	if holiday_mismatch > 0:
		mismatch_sample = merged.loc[
			merged["IsHoliday_sales"].astype(str).str.upper()
			!= merged["IsHoliday_features"].astype(str).str.upper(),
			["Store", "Dept", "Date", "IsHoliday_sales", "IsHoliday_features"],
		].head(10)
		raise ValueError(
			"IsHoliday mismatch detected between train.csv and features.csv. "
			"Refusing to pick one silently. Sample mismatches:\n"
			f"{mismatch_sample.to_string(index=False)}"
		)

	merged = merged.drop(columns=["IsHoliday_features", "_merge"]).rename(
		columns={"IsHoliday_sales": "IsHoliday"}
	)

	merged = merged.merge(
		stores_df,
		on="Store",
		how="left",
		validate="many_to_one",
		indicator=True,
	)

	stores_merge_status = merged["_merge"].value_counts().to_dict()
	print("=== Merge status: + stores ===")
	print(stores_merge_status)
	print()

	assert stores_merge_status.get("left_only", 0) == 0, (
		"Some merged sales rows did not find a Store match in stores.csv."
	)

	merged = merged.drop(columns=["_merge"])

	assert len(merged) == train_rows_before, (
		"Row count changed after adding stores data. "
		f"Expected {train_rows_before:,}, found {len(merged):,}."
	)

	sales_total_after = merged["Weekly_Sales"].sum()
	assert abs(sales_total_after - sales_total_before) < 1e-9, (
		"Weekly_Sales total changed after merges. "
		f"Before: {sales_total_before:,.2f}, after: {sales_total_after:,.2f}."
	)

	print(f"sales rows preserved: {len(merged):,}")
	print(f"weekly sales total preserved: {sales_total_after:,.2f}")
	print()

	return merged


def _document_markdown_treatment(df: pd.DataFrame) -> pd.DataFrame:
	print("=== MarkDown missing-value treatment ===")
	missing_counts = df[MARKDOWN_COLUMNS].isna().sum()
	print("Raw MarkDown missing counts:")
	print(missing_counts)
	print()
	print(
		"Treatment: MarkDown1-MarkDown5 are retained as missing in the main cleaned dataset. "
		"This avoids assuming that missing means 0 promotion spend."
	)
	print(
		"Power BI companion output includes both a zero-filled copy and missingness flags "
		"for each markdown field so visuals can choose a strategy explicitly."
	)
	print(
		"Limitation: Without source-system metadata, missing markdowns may represent "
		"no promotion, unknown promotion, or unreported values."
	)
	print()

	return df


def _build_powerbi_compact(df: pd.DataFrame) -> pd.DataFrame:
	powerbi = df.copy()

	for col in MARKDOWN_COLUMNS:
		powerbi[f"{col}_was_missing"] = powerbi[col].isna().astype("int8")
		powerbi[f"{col}_filled0"] = powerbi[col].fillna(0)

	powerbi["Year"] = powerbi["Date"].dt.year
	powerbi["Month"] = powerbi["Date"].dt.month
	powerbi["YearMonth"] = powerbi["Date"].dt.to_period("M").astype(str)

	columns = [
		"Store",
		"Dept",
		"Date",
		"Year",
		"Month",
		"YearMonth",
		"Weekly_Sales",
		"IsHoliday",
		"Temperature",
		"Fuel_Price",
		"CPI",
		"Unemployment",
		"Type",
		"Size",
	] + MARKDOWN_COLUMNS

	for col in MARKDOWN_COLUMNS:
		columns.extend([f"{col}_was_missing", f"{col}_filled0"])

	return powerbi[columns]


def main() -> None:
	for input_path in [TRAIN_PATH, FEATURES_PATH, STORES_PATH]:
		_require_file(input_path)

	train_df = pd.read_csv(TRAIN_PATH, parse_dates=["Date"])
	features_df = pd.read_csv(FEATURES_PATH, parse_dates=["Date"], na_values=["NA"])
	stores_df = pd.read_csv(STORES_PATH)

	_require_columns(train_df, TRAIN_REQUIRED_COLUMNS, "train.csv")
	_require_columns(features_df, FEATURES_REQUIRED_COLUMNS, "features.csv")
	_require_columns(stores_df, STORES_REQUIRED_COLUMNS, "stores.csv")

	_print_dataset_overview(train_df, features_df, stores_df)
	_print_missing_values(train_df, "Missing values in train (before cleaning):")
	_print_missing_values(features_df, "Missing values in features (before cleaning):")
	_print_missing_values(stores_df, "Missing values in stores (before cleaning):")

	_validate_keys(train_df, features_df, stores_df)
	merged = _merge_and_validate(train_df, features_df, stores_df)
	merged = _document_markdown_treatment(merged)

	_print_missing_values(merged, "Missing values in merged data (after cleaning):")

	print("=== Final dataset summary ===")
	print(f"row count: {len(merged):,}")
	print(
		"date range: "
		f"{merged['Date'].min().date()} to {merged['Date'].max().date()}"
	)
	print(f"distinct stores: {merged['Store'].nunique():,}")
	print(f"distinct departments: {merged['Dept'].nunique():,}")
	print(f"weekly sales total: {merged['Weekly_Sales'].sum():,.2f}")
	print()

	PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
	merged.to_csv(OUTPUT_CLEAN_PATH, index=False)

	powerbi_compact = _build_powerbi_compact(merged)
	powerbi_compact.to_csv(OUTPUT_POWERBI_PATH, index=False)

	print("=== Output files ===")
	print(f"Saved cleaned merged dataset to: {OUTPUT_CLEAN_PATH}")
	print(f"Saved Power BI-ready companion dataset to: {OUTPUT_POWERBI_PATH}")


if __name__ == "__main__":
	main()
