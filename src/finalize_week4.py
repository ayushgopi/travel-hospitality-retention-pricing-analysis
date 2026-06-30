"""Week 4: final dashboard summaries, executive report, and handoff notes."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from clean_data import clean_and_engineer, load_dataset  # noqa: E402
from config import (  # noqa: E402
    CLEANED_DATA_PATH,
    MODEL_METRICS_PATH,
    WEEK4_DASHBOARD_SUMMARY_PATH,
    WEEK4_EXECUTIVE_SUMMARY_PATH,
    WEEK4_FINAL_REPORT_PATH,
    ensure_directories,
)


def load_clean_data() -> pd.DataFrame:
    """Load cleaned data or rebuild it from the approved source file."""
    if CLEANED_DATA_PATH.exists():
        return pd.read_csv(CLEANED_DATA_PATH)

    raw = load_dataset()
    cleaned, _ = clean_and_engineer(raw)
    cleaned.to_csv(CLEANED_DATA_PATH, index=False)
    return cleaned


def pct(value: float) -> str:
    return f"{value:.2%}"


def money(value: float) -> str:
    return f"{value:,.2f}"


def markdown_table(df: pd.DataFrame, floatfmt: str = ".2f") -> str:
    formatted = df.copy()
    for column in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[column]):
            formatted[column] = formatted[column].map(lambda value: format(value, floatfmt))
    formatted = formatted.astype(str)
    columns = list(formatted.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(row[column] for column in columns) + " |"
        for _, row in formatted.iterrows()
    ]
    return "\n".join([header, separator, *rows])


def build_dashboard_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create dashboard-ready business metric table."""
    summary_rows = [
        {
            "metric_group": "Portfolio",
            "metric": "Cleaned bookings",
            "value": len(df),
            "display_value": f"{len(df):,}",
            "business_use": "Dataset volume available for reporting and modeling",
        },
        {
            "metric_group": "Retention",
            "metric": "Cancellation rate",
            "value": df["is_canceled"].mean(),
            "display_value": pct(df["is_canceled"].mean()),
            "business_use": "Primary retention KPI",
        },
        {
            "metric_group": "Pricing",
            "metric": "Average ADR",
            "value": df["adr"].mean(),
            "display_value": money(df["adr"].mean()),
            "business_use": "Baseline daily rate indicator",
        },
        {
            "metric_group": "Demand",
            "metric": "Average lead time",
            "value": df["lead_time"].mean(),
            "display_value": f"{df['lead_time'].mean():.1f} days",
            "business_use": "Booking curve and cancellation-risk input",
        },
        {
            "metric_group": "Revenue",
            "metric": "Gross booking value",
            "value": df["booking_value"].sum(),
            "display_value": money(df["booking_value"].sum()),
            "business_use": "Revenue opportunity before cancellations",
        },
        {
            "metric_group": "Revenue",
            "metric": "Realized booking value proxy",
            "value": (df["booking_value"] * (1 - df["is_canceled"])).sum(),
            "display_value": money((df["booking_value"] * (1 - df["is_canceled"])).sum()),
            "business_use": "Cancellation-adjusted historical value",
        },
    ]

    hotel_summary = (
        df.groupby("hotel", observed=True)
        .agg(
            bookings=("is_canceled", "size"),
            cancellation_rate=("is_canceled", "mean"),
            avg_adr=("adr", "mean"),
            gross_booking_value=("booking_value", "sum"),
        )
        .reset_index()
    )
    for _, row in hotel_summary.iterrows():
        summary_rows.append(
            {
                "metric_group": "Hotel Type",
                "metric": f"{row['hotel']} cancellation rate",
                "value": row["cancellation_rate"],
                "display_value": pct(row["cancellation_rate"]),
                "business_use": "Hotel-level retention and forecasting benchmark",
            }
        )

    season_summary = (
        df.groupby("booking_season", observed=True)["booking_value"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    for _, row in season_summary.iterrows():
        summary_rows.append(
            {
                "metric_group": "Season",
                "metric": f"{row['booking_season']} gross booking value",
                "value": row["booking_value"],
                "display_value": money(row["booking_value"]),
                "business_use": "Seasonal pricing and staffing benchmark",
            }
        )

    return pd.DataFrame(summary_rows)


def write_reports(df: pd.DataFrame, dashboard: pd.DataFrame) -> None:
    metrics = pd.read_csv(MODEL_METRICS_PATH) if MODEL_METRICS_PATH.exists() else pd.DataFrame()
    best_model = metrics.sort_values("roc_auc", ascending=False).iloc[0] if not metrics.empty else None

    top_segments = (
        df.groupby(["traveller_segment", "lead_time_bucket", "customer_value_segment"], observed=True)
        .agg(
            bookings=("is_canceled", "size"),
            cancellation_rate=("is_canceled", "mean"),
            avg_booking_value=("booking_value", "mean"),
        )
        .reset_index()
        .query("bookings >= 100")
        .sort_values("cancellation_rate", ascending=False)
        .head(8)
    )

    seasonal = (
        df.groupby("booking_season", observed=True)
        .agg(bookings=("is_canceled", "size"), avg_adr=("adr", "mean"), gross_booking_value=("booking_value", "sum"))
        .reset_index()
        .sort_values("gross_booking_value", ascending=False)
    )

    WEEK4_EXECUTIVE_SUMMARY_PATH.write_text(
        f"""# Week 4 Executive Summary

The final analysis confirms that cancellation risk is a major revenue-management problem: the cleaned dataset contains {len(df):,} bookings with a {pct(df['is_canceled'].mean())} cancellation rate. Average ADR is {money(df['adr'].mean())}, average lead time is {df['lead_time'].mean():.1f} days, and Summer contributes the highest gross booking value. The Week 3 baseline model selected Logistic Regression as the strongest model by ROC-AUC{f" ({best_model['roc_auc']:.3f})" if best_model is not None else ""}, making it suitable as a starting point for cancellation-risk scoring and retention prioritization.
""",
        encoding="utf-8",
    )

    WEEK4_FINAL_REPORT_PATH.write_text(
        f"""# Week 4 Final Business Report

## Project Objective

Analyze historical hotel booking behavior to reduce cancellation-driven revenue leakage, identify customer retention opportunities, and create a data foundation for dynamic pricing decisions.

## Final KPI Snapshot

{markdown_table(dashboard[["metric_group", "metric", "display_value", "business_use"]].head(12))}

## Highest Risk Customer Segments

{markdown_table(top_segments)}

## Seasonal Pricing Summary

{markdown_table(seasonal)}

## Final Strategic Recommendations

### Revenue Optimization

- Use cancellation-adjusted expected revenue instead of raw booking value.
- Track hotel-specific performance because City Hotel and Resort Hotel have different cancellation profiles.
- Protect high-value bookings with targeted retention offers before arrival.
- Review deposit policy for high-risk lead-time and market-segment combinations.

### Dynamic Pricing

- Use season, month, hotel type, lead time, market segment, country, and deposit type in future pricing rules.
- Increase rates in high-demand, high-ADR periods such as Summer while monitoring cancellation risk.
- Apply selective last-minute discounts only when unsold inventory remains.
- Use expected revenue formula: `booking_value * (1 - cancellation_probability)`.

### Customer Retention

- Prioritize early planners and high-value customers for pre-arrival engagement.
- Build market-segment-specific campaigns for segments with high cancellation rates.
- Use special requests, parking needs, and family indicators as signals for stronger booking intent.
- Create risk bands from Week 3 model scores: low, medium, and high cancellation risk.

## Week 4 Handoff

- Cleaned dataset: `data/processed/cleaned_hotel_bookings.csv`
- Dashboard summary table: `data/processed/week4_dashboard_summary.csv`
- Final presentation: `reports/week4_final_presentation.pptx`
- Final executive summary: `reports/week4_executive_summary.md`
- Final model report: `reports/week3_modeling_report.md`
""",
        encoding="utf-8",
    )


def main() -> None:
    ensure_directories()
    df = load_clean_data()
    dashboard = build_dashboard_summary(df)
    dashboard.to_csv(WEEK4_DASHBOARD_SUMMARY_PATH, index=False)
    write_reports(df, dashboard)

    print(f"Dashboard summary saved to: {WEEK4_DASHBOARD_SUMMARY_PATH}")
    print(f"Executive summary saved to: {WEEK4_EXECUTIVE_SUMMARY_PATH}")
    print(f"Final business report saved to: {WEEK4_FINAL_REPORT_PATH}")


if __name__ == "__main__":
    main()
