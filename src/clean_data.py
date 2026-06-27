"""Week 1: data loading, cleaning, feature engineering, and reporting."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from config import (  # noqa: E402
    CLEANED_DATA_PATH,
    CLEANING_REPORT_PATH,
    MONTH_ORDER,
    SEASON_MAP,
    SEGMENTS_PATH,
    SOURCE_DATA,
    ensure_directories,
)


def load_dataset(path: Path = SOURCE_DATA) -> pd.DataFrame:
    """Load the hotel bookings dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_csv(path)


def _iqr_bounds(series: pd.Series, multiplier: float = 1.5) -> tuple[float, float]:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    return q1 - multiplier * iqr, q3 + multiplier * iqr


def _lead_time_bucket(lead_time: float) -> str:
    if lead_time <= 7:
        return "Last-minute booker"
    if lead_time <= 30:
        return "Short-window planner"
    if lead_time <= 90:
        return "Medium-window planner"
    return "Early planner"


def _stay_length_bucket(total_stay: float) -> str:
    if total_stay <= 1:
        return "One-night stay"
    if total_stay <= 3:
        return "Short stay"
    if total_stay <= 7:
        return "Standard stay"
    return "Extended stay"


def _traveller_segment(row: pd.Series) -> str:
    if row["market_segment"] == "Corporate" or row["distribution_channel"] == "Corporate":
        return "Business traveller"
    if row["adults"] == 1 and row["children"] == 0 and row["babies"] == 0 and row["total_stay"] <= 3:
        return "Solo short-stay traveller"
    return "Leisure traveller"


def _booking_value_bucket(value: float, q75: float, q90: float) -> str:
    if value >= q90:
        return "Premium value"
    if value >= q75:
        return "High value"
    return "Standard value"


def clean_and_engineer(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Clean the raw dataset and create analytics-ready features."""
    report: dict[str, Any] = {
        "run_timestamp": datetime.now().isoformat(timespec="seconds"),
        "source_path": str(SOURCE_DATA),
        "initial_rows": len(df),
        "initial_columns": df.shape[1],
        "missing_before": df.isna().sum().to_dict(),
        "duplicates_before": int(df.duplicated().sum()),
    }

    cleaned = df.copy()
    cleaned.columns = cleaned.columns.str.strip().str.lower()

    cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    report["duplicates_removed"] = report["initial_rows"] - len(cleaned)

    cleaned["children"] = cleaned["children"].fillna(0)
    cleaned["country"] = cleaned["country"].fillna("Unknown")
    cleaned["agent"] = cleaned["agent"].fillna(0)
    cleaned["company"] = cleaned["company"].fillna(0)

    cleaned["reservation_status_date"] = pd.to_datetime(
        cleaned["reservation_status_date"], errors="coerce"
    )

    numeric_integer_columns = [
        "is_canceled",
        "lead_time",
        "arrival_date_year",
        "arrival_date_week_number",
        "arrival_date_day_of_month",
        "stays_in_weekend_nights",
        "stays_in_week_nights",
        "adults",
        "children",
        "babies",
        "is_repeated_guest",
        "previous_cancellations",
        "previous_bookings_not_canceled",
        "booking_changes",
        "agent",
        "company",
        "days_in_waiting_list",
        "required_car_parking_spaces",
        "total_of_special_requests",
    ]
    for column in numeric_integer_columns:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce").fillna(0).astype(int)

    cleaned["adr"] = pd.to_numeric(cleaned["adr"], errors="coerce")

    invalid_status_dates = int(cleaned["reservation_status_date"].isna().sum())
    cleaned = cleaned.dropna(subset=["reservation_status_date"])

    numeric_non_negative_columns = [
        "lead_time",
        "stays_in_weekend_nights",
        "stays_in_week_nights",
        "adults",
        "children",
        "babies",
        "previous_cancellations",
        "previous_bookings_not_canceled",
        "booking_changes",
        "days_in_waiting_list",
        "required_car_parking_spaces",
        "total_of_special_requests",
    ]
    invalid_negative_rows = cleaned[numeric_non_negative_columns].lt(0).any(axis=1)
    cleaned = cleaned.loc[~invalid_negative_rows].copy()

    cleaned["total_stay"] = cleaned["stays_in_weekend_nights"] + cleaned["stays_in_week_nights"]
    cleaned["total_guests"] = cleaned["adults"] + cleaned["children"] + cleaned["babies"]

    zero_guest_rows = cleaned["total_guests"] == 0
    zero_night_rows = cleaned["total_stay"] == 0
    cleaned = cleaned.loc[~zero_guest_rows & ~zero_night_rows].copy()

    negative_adr_rows = cleaned["adr"] < 0
    cleaned = cleaned.loc[~negative_adr_rows].copy()

    adr_upper_cap = _iqr_bounds(cleaned["adr"], multiplier=3.0)[1]
    adr_upper_cap = min(float(adr_upper_cap), float(cleaned["adr"].quantile(0.995)))
    adr_outlier_rows = cleaned["adr"] > adr_upper_cap
    cleaned["adr_original"] = cleaned["adr"]
    cleaned["adr"] = cleaned["adr"].clip(lower=0, upper=adr_upper_cap)
    cleaned["adr_was_capped"] = adr_outlier_rows.astype(int)

    lead_time_upper_cap = float(cleaned["lead_time"].quantile(0.995))
    cleaned["lead_time_original"] = cleaned["lead_time"]
    cleaned["lead_time"] = cleaned["lead_time"].clip(upper=lead_time_upper_cap).astype(int)
    cleaned["lead_time_was_capped"] = (cleaned["lead_time_original"] > lead_time_upper_cap).astype(int)

    cleaned["arrival_month_name"] = pd.Categorical(
        cleaned["arrival_date_month"], categories=MONTH_ORDER, ordered=True
    )
    cleaned["arrival_month_number"] = cleaned["arrival_month_name"].cat.codes + 1
    cleaned["booking_season"] = cleaned["arrival_date_month"].map(SEASON_MAP).fillna("Unknown")
    cleaned["arrival_date"] = pd.to_datetime(
        dict(
            year=cleaned["arrival_date_year"],
            month=cleaned["arrival_month_number"],
            day=cleaned["arrival_date_day_of_month"],
        ),
        errors="coerce",
    )
    cleaned = cleaned.dropna(subset=["arrival_date"]).copy()

    cleaned["booking_value"] = cleaned["adr"] * cleaned["total_stay"]
    cleaned["adr_per_guest"] = np.where(
        cleaned["total_guests"] > 0, cleaned["adr"] / cleaned["total_guests"], 0
    )
    cleaned["room_type_changed"] = (
        cleaned["reserved_room_type"] != cleaned["assigned_room_type"]
    ).astype(int)
    cleaned["has_agent"] = (cleaned["agent"] > 0).astype(int)
    cleaned["has_company"] = (cleaned["company"] > 0).astype(int)
    cleaned["has_special_requests"] = (cleaned["total_of_special_requests"] > 0).astype(int)
    cleaned["is_family_booking"] = ((cleaned["children"] + cleaned["babies"]) > 0).astype(int)
    cleaned["is_weekend_stay"] = (cleaned["stays_in_weekend_nights"] > 0).astype(int)
    cleaned["is_long_stay"] = (cleaned["total_stay"] >= 7).astype(int)
    cleaned["lead_time_bucket"] = cleaned["lead_time"].apply(_lead_time_bucket)
    cleaned["stay_length_bucket"] = cleaned["total_stay"].apply(_stay_length_bucket)
    cleaned["traveller_segment"] = cleaned.apply(_traveller_segment, axis=1)

    q75 = float(cleaned["booking_value"].quantile(0.75))
    q90 = float(cleaned["booking_value"].quantile(0.90))
    cleaned["customer_value_segment"] = cleaned["booking_value"].apply(
        lambda value: _booking_value_bucket(value, q75, q90)
    )
    cleaned["is_high_value_customer"] = cleaned["customer_value_segment"].isin(
        ["High value", "Premium value"]
    ).astype(int)

    cleaned["customer_segment"] = (
        cleaned["traveller_segment"]
        + " | "
        + cleaned["lead_time_bucket"]
        + " | "
        + cleaned["customer_value_segment"]
    )

    category_columns = [
        "hotel",
        "arrival_date_month",
        "meal",
        "country",
        "market_segment",
        "distribution_channel",
        "reserved_room_type",
        "assigned_room_type",
        "deposit_type",
        "customer_type",
        "reservation_status",
        "booking_season",
        "lead_time_bucket",
        "stay_length_bucket",
        "traveller_segment",
        "customer_value_segment",
        "customer_segment",
    ]
    for column in category_columns:
        cleaned[column] = cleaned[column].astype("category")

    report.update(
        {
            "invalid_status_dates_removed": invalid_status_dates,
            "negative_numeric_rows_removed": int(invalid_negative_rows.sum()),
            "zero_guest_rows_removed": int(zero_guest_rows.sum()),
            "zero_night_rows_removed": int(zero_night_rows.sum()),
            "negative_adr_rows_removed": int(negative_adr_rows.sum()),
            "adr_upper_cap": round(float(adr_upper_cap), 2),
            "adr_rows_capped": int(adr_outlier_rows.sum()),
            "lead_time_upper_cap": int(lead_time_upper_cap),
            "lead_time_rows_capped": int((cleaned["lead_time_original"] > lead_time_upper_cap).sum()),
            "final_rows": len(cleaned),
            "final_columns": cleaned.shape[1],
            "missing_after": cleaned.isna().sum().to_dict(),
        }
    )

    return cleaned.reset_index(drop=True), report


def build_segment_summary(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Create a compact customer segment table for retention and pricing decisions."""
    segment_summary = (
        cleaned.groupby(
            ["traveller_segment", "lead_time_bucket", "customer_value_segment"],
            observed=True,
        )
        .agg(
            bookings=("is_canceled", "size"),
            cancellation_rate=("is_canceled", "mean"),
            avg_adr=("adr", "mean"),
            avg_booking_value=("booking_value", "mean"),
            avg_total_stay=("total_stay", "mean"),
            avg_lead_time=("lead_time", "mean"),
            avg_special_requests=("total_of_special_requests", "mean"),
        )
        .reset_index()
        .sort_values(["bookings", "avg_booking_value"], ascending=False)
    )
    return segment_summary


def markdown_table(rows: list[dict[str, Any]]) -> str:
    """Render a simple Markdown table without optional dependencies."""
    if not rows:
        return ""
    columns = list(rows[0].keys())
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = [
        "| " + " | ".join(str(row.get(column, "")) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def write_cleaning_report(report: dict[str, Any], cleaned: pd.DataFrame) -> None:
    """Write a Markdown data cleaning report."""
    top_missing_before = sorted(
        report["missing_before"].items(), key=lambda item: item[1], reverse=True
    )[:10]
    remaining_missing = {
        column: value for column, value in report["missing_after"].items() if value > 0
    }

    cancellation_rate = cleaned["is_canceled"].mean()
    avg_adr = cleaned["adr"].mean()
    avg_stay = cleaned["total_stay"].mean()

    text = f"""# Week 1 Data Cleaning Report

## Source

- Dataset: `{report["source_path"]}`
- Run timestamp: {report["run_timestamp"]}
- Initial shape: {report["initial_rows"]:,} rows x {report["initial_columns"]:,} columns
- Final shape: {report["final_rows"]:,} rows x {report["final_columns"]:,} columns

## Cleaning Actions

| Action | Result |
|---|---:|
| Duplicate rows removed | {report["duplicates_removed"]:,} |
| Rows with invalid reservation status dates removed | {report["invalid_status_dates_removed"]:,} |
| Rows with negative numeric values removed | {report["negative_numeric_rows_removed"]:,} |
| Rows with zero guests removed | {report["zero_guest_rows_removed"]:,} |
| Rows with zero stay nights removed | {report["zero_night_rows_removed"]:,} |
| Rows with negative ADR removed | {report["negative_adr_rows_removed"]:,} |
| ADR cap used | {report["adr_upper_cap"]:,} |
| ADR rows capped | {report["adr_rows_capped"]:,} |
| Lead time cap used | {report["lead_time_upper_cap"]:,} days |
| Lead time rows capped | {report["lead_time_rows_capped"]:,} |

## Missing Value Treatment

| Column | Missing Before | Treatment |
|---|---:|---|
| company | {report["missing_before"].get("company", 0):,} | Filled with `0` to mean no company association |
| agent | {report["missing_before"].get("agent", 0):,} | Filled with `0` to mean direct/no agent |
| country | {report["missing_before"].get("country", 0):,} | Filled with `Unknown` |
| children | {report["missing_before"].get("children", 0):,} | Filled with `0` |

Top missing columns before cleaning:

{markdown_table([{"column": column, "missing_count": f"{count:,}"} for column, count in top_missing_before])}

Remaining missing values after cleaning:

```text
{remaining_missing if remaining_missing else "No remaining missing values."}
```

## Feature Engineering

Created production-ready analytical features:

- `total_stay`: weekend plus weekday nights.
- `total_guests`: adults plus children plus babies.
- `arrival_month_name` and `arrival_month_number`.
- `booking_season`: Winter, Spring, Summer, Autumn.
- `arrival_date`: full arrival date from year, month, and day fields.
- `booking_value`: ADR multiplied by total stay.
- `adr_per_guest`: ADR normalized by guest count.
- `room_type_changed`, `has_agent`, `has_company`, `has_special_requests`, `is_family_booking`, `is_weekend_stay`, `is_long_stay`.
- `lead_time_bucket`, `stay_length_bucket`, `traveller_segment`, `customer_value_segment`, `customer_segment`.

## Cleaned Dataset Snapshot

| Metric | Value |
|---|---:|
| Bookings retained | {len(cleaned):,} |
| Cancellation rate | {cancellation_rate:.2%} |
| Average ADR | {avg_adr:.2f} |
| Average total stay | {avg_stay:.2f} nights |
| Countries represented | {cleaned["country"].nunique():,} |
| Customer segments | {cleaned["customer_segment"].nunique():,} |

## Data Quality Notes

- `agent = 0` and `company = 0` are engineered placeholders for missing identifiers, not real IDs.
- ADR outliers are capped rather than deleted to preserve booking volume while limiting distortion in pricing analysis.
- Zero-night and zero-guest records are removed because they do not represent usable demand for RevPAR, retention, or stay-length analysis.
"""
    CLEANING_REPORT_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    ensure_directories()
    raw = load_dataset()
    cleaned, report = clean_and_engineer(raw)
    segments = build_segment_summary(cleaned)

    cleaned.to_csv(CLEANED_DATA_PATH, index=False)
    segments.to_csv(SEGMENTS_PATH, index=False)
    write_cleaning_report(report, cleaned)

    print(f"Cleaned dataset saved to: {CLEANED_DATA_PATH}")
    print(f"Customer segments saved to: {SEGMENTS_PATH}")
    print(f"Cleaning report saved to: {CLEANING_REPORT_PATH}")
    print(f"Final shape: {cleaned.shape}")


if __name__ == "__main__":
    main()
