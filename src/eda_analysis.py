"""Week 2: professional EDA, customer segmentation, and recommendations."""

from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import Callable

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.append(str(Path(__file__).resolve().parent))
from clean_data import build_segment_summary, clean_and_engineer, load_dataset  # noqa: E402
from config import (  # noqa: E402
    BUSINESS_RECOMMENDATIONS_PATH,
    CLEANED_DATA_PATH,
    EDA_REPORT_PATH,
    MONTH_ORDER,
    SEGMENTS_PATH,
    VISUALIZATIONS_DIR,
    ensure_directories,
)


sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.figsize"] = (12, 7)
plt.rcParams["axes.titlesize"] = 15
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["savefig.dpi"] = 160
plt.rcParams["font.family"] = "DejaVu Sans"


Insight = dict[str, str]


def markdown_table(df: pd.DataFrame, floatfmt: str = ".2f") -> str:
    """Render a DataFrame as Markdown without optional tabulate dependency."""
    if df.empty:
        return "No rows available."
    formatted = df.copy()
    for column in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[column]):
            formatted[column] = formatted[column].map(lambda value: format(value, floatfmt))
    formatted = formatted.astype(str)
    columns = list(formatted.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = [
        "| " + " | ".join(row[column] for column in columns) + " |"
        for _, row in formatted.iterrows()
    ]
    return "\n".join([header, separator, *body])


def load_cleaned_dataset() -> pd.DataFrame:
    """Load existing cleaned data or create it from the raw source."""
    if CLEANED_DATA_PATH.exists():
        df = pd.read_csv(CLEANED_DATA_PATH, parse_dates=["reservation_status_date", "arrival_date"])
    else:
        raw = load_dataset()
        df, _ = clean_and_engineer(raw)
        df.to_csv(CLEANED_DATA_PATH, index=False)
        build_segment_summary(df).to_csv(SEGMENTS_PATH, index=False)
    return df


def save_current_plot(filename: str) -> str:
    path = VISUALIZATIONS_DIR / filename
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return str(path.relative_to(VISUALIZATIONS_DIR.parent))


def add_bar_labels(ax: plt.Axes, fmt: str = "{:.0f}") -> None:
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, fontsize=8, padding=2)


def cancellation_rate_table(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    return (
        df.groupby(group_col, observed=True)
        .agg(bookings=("is_canceled", "size"), cancellation_rate=("is_canceled", "mean"), avg_adr=("adr", "mean"))
        .reset_index()
        .sort_values("bookings", ascending=False)
    )


def plot_booking_distribution(df: pd.DataFrame) -> Insight:
    ax = sns.countplot(data=df, x="hotel", hue="hotel", palette="Set2", legend=False)
    ax.set_title("Booking Distribution by Hotel Type")
    ax.set_xlabel("Hotel Type")
    ax.set_ylabel("Number of Bookings")
    add_bar_labels(ax)
    path = save_current_plot("01_booking_distribution.png")
    dominant = df["hotel"].value_counts().idxmax()
    return {
        "title": "Booking distribution",
        "path": path,
        "insight": f"{dominant} contributes the largest share of bookings.",
        "interpretation": "Demand is not evenly distributed across hotel types, so pricing and retention strategy should not be averaged across the portfolio.",
        "recommendation": "Track RevPAR, cancellation rate, and ADR separately for City Hotel and Resort Hotel before setting rate fences.",
    }


def plot_cancellation_analysis(df: pd.DataFrame) -> Insight:
    rate = df["is_canceled"].mean()
    ax = sns.countplot(data=df, x="is_canceled", hue="is_canceled", palette=["#4C78A8", "#F58518"], legend=False)
    ax.set_title("Cancellation vs Completed Booking Volume")
    ax.set_xlabel("Canceled Flag")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Not canceled", "Canceled"])
    ax.set_ylabel("Bookings")
    add_bar_labels(ax)
    path = save_current_plot("02_cancellation_analysis.png")
    return {
        "title": "Cancellation analysis",
        "path": path,
        "insight": f"The cleaned dataset cancellation rate is {rate:.1%}.",
        "interpretation": "Cancellation behavior is large enough to materially affect demand forecasting, staffing, and room inventory protection.",
        "recommendation": "Create pre-arrival retention triggers for high-risk bookings and include cancellation probability in demand forecasts.",
    }


def plot_adr_analysis(df: pd.DataFrame) -> Insight:
    ax = sns.histplot(df["adr"], bins=60, kde=True, color="#4C78A8")
    ax.set_title("Average Daily Rate Distribution")
    ax.set_xlabel("ADR")
    ax.set_ylabel("Booking Count")
    path = save_current_plot("03_adr_distribution.png")
    return {
        "title": "ADR analysis",
        "path": path,
        "insight": f"ADR is right-skewed with a median of {df['adr'].median():.2f} and mean of {df['adr'].mean():.2f}.",
        "interpretation": "Premium-priced bookings exist, but central tendency is lower than the upper tail, so mean-only pricing views can exaggerate normal demand.",
        "recommendation": "Use median ADR and percentile bands in pricing dashboards alongside average ADR.",
    }


def plot_category_distribution(df: pd.DataFrame, column: str, filename: str, title: str) -> Insight:
    counts = df[column].value_counts().head(12)
    ax = sns.barplot(x=counts.values, y=counts.index, hue=counts.index, palette="viridis", legend=False)
    ax.set_title(title)
    ax.set_xlabel("Bookings")
    ax.set_ylabel(column.replace("_", " ").title())
    path = save_current_plot(filename)
    leader = counts.index[0]
    return {
        "title": title,
        "path": path,
        "insight": f"`{leader}` is the largest category for {column.replace('_', ' ')}.",
        "interpretation": "Concentration in one or two categories can hide underperforming smaller channels or segments.",
        "recommendation": f"Benchmark ADR and cancellation rate within `{column}` categories instead of relying only on total booking volume.",
    }


def plot_lead_time(df: pd.DataFrame) -> Insight:
    ax = sns.histplot(df["lead_time"], bins=70, kde=True, color="#59A14F")
    ax.set_title("Lead Time Distribution")
    ax.set_xlabel("Lead Time in Days")
    ax.set_ylabel("Bookings")
    path = save_current_plot("10_lead_time_distribution.png")
    early_share = (df["lead_time"] > 90).mean()
    return {
        "title": "Lead time",
        "path": path,
        "insight": f"{early_share:.1%} of bookings are made more than 90 days before arrival.",
        "interpretation": "Long booking windows increase exposure to cancellations and rate-shopping behavior.",
        "recommendation": "Use stricter deposit policies or targeted reminders for long-lead bookings with high cancellation likelihood.",
    }


def plot_monthly_trends(df: pd.DataFrame) -> Insight:
    monthly = (
        df.groupby("arrival_date_month", observed=True)
        .agg(bookings=("is_canceled", "size"), avg_adr=("adr", "mean"), cancellation_rate=("is_canceled", "mean"))
        .reindex(MONTH_ORDER)
        .reset_index()
    )
    fig, ax1 = plt.subplots(figsize=(13, 7))
    sns.lineplot(data=monthly, x="arrival_date_month", y="bookings", marker="o", ax=ax1, color="#4C78A8", label="Bookings")
    ax1.set_xlabel("Arrival Month")
    ax1.set_ylabel("Bookings")
    ax1.tick_params(axis="x", rotation=35)
    ax2 = ax1.twinx()
    sns.lineplot(data=monthly, x="arrival_date_month", y="avg_adr", marker="s", ax=ax2, color="#F58518", label="Average ADR")
    ax2.set_ylabel("Average ADR")
    ax1.set_title("Monthly Booking Volume and ADR Trend")
    path = save_current_plot("11_monthly_booking_trends.png")
    peak_month = monthly.loc[monthly["bookings"].idxmax(), "arrival_date_month"]
    adr_peak = monthly.loc[monthly["avg_adr"].idxmax(), "arrival_date_month"]
    return {
        "title": "Monthly booking trends",
        "path": path,
        "insight": f"Booking volume peaks in {peak_month}, while ADR peaks in {adr_peak}.",
        "interpretation": "Volume and price peaks may not occur in the same month, indicating opportunities for yield management.",
        "recommendation": "Review months where high demand is not matched by high ADR and test controlled rate increases.",
    }


def plot_seasonal_trends(df: pd.DataFrame) -> Insight:
    seasonal = (
        df.groupby("booking_season", observed=True)
        .agg(bookings=("is_canceled", "size"), avg_adr=("adr", "mean"), cancellation_rate=("is_canceled", "mean"))
        .reset_index()
    )
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    sns.barplot(data=seasonal, x="booking_season", y="bookings", hue="booking_season", palette="Set2", legend=False, ax=axes[0])
    sns.barplot(data=seasonal, x="booking_season", y="avg_adr", hue="booking_season", palette="Set2", legend=False, ax=axes[1])
    sns.barplot(data=seasonal, x="booking_season", y="cancellation_rate", hue="booking_season", palette="Set2", legend=False, ax=axes[2])
    axes[0].set_title("Bookings")
    axes[1].set_title("Average ADR")
    axes[2].set_title("Cancellation Rate")
    for ax in axes:
        ax.set_xlabel("Season")
        ax.tick_params(axis="x", rotation=20)
    path = save_current_plot("12_seasonal_trends.png")
    best_season = seasonal.loc[seasonal["avg_adr"].idxmax(), "booking_season"]
    return {
        "title": "Seasonal trends",
        "path": path,
        "insight": f"{best_season} has the highest average ADR.",
        "interpretation": "Seasonality is a clear input for dynamic pricing because demand, ADR, and cancellation behavior shift together.",
        "recommendation": "Build seasonal price floors and cancellation-risk adjustments into future rate recommendations.",
    }


def plot_country_analysis(df: pd.DataFrame) -> Insight:
    country = df["country"].value_counts().head(20)
    ax = sns.barplot(x=country.values, y=country.index, hue=country.index, palette="mako", legend=False)
    ax.set_title("Top 20 Countries by Booking Volume")
    ax.set_xlabel("Bookings")
    ax.set_ylabel("Country")
    path = save_current_plot("13_top_20_countries.png")
    top_country = country.index[0]
    return {
        "title": "Country analysis and top 20 countries",
        "path": path,
        "insight": f"{top_country} is the largest source market by booking volume.",
        "interpretation": "Geographic concentration affects cancellation forecasting, campaign language, and rate sensitivity.",
        "recommendation": "Create country-level dashboards for cancellation rate, ADR, and booking lead time before allocating marketing budget.",
    }


def plot_weekday_weekend(df: pd.DataFrame) -> Insight:
    stay = df[["stays_in_weekend_nights", "stays_in_week_nights"]].sum().rename(
        {"stays_in_weekend_nights": "Weekend nights", "stays_in_week_nights": "Weekday nights"}
    )
    ax = sns.barplot(x=stay.index, y=stay.values, hue=stay.index, palette=["#E45756", "#72B7B2"], legend=False)
    ax.set_title("Weekday vs Weekend Stay Nights")
    ax.set_xlabel("Stay Type")
    ax.set_ylabel("Total Nights")
    add_bar_labels(ax)
    path = save_current_plot("14_weekday_vs_weekend_stays.png")
    return {
        "title": "Weekday vs weekend stays",
        "path": path,
        "insight": "Weekday nights represent the larger share of consumed room nights.",
        "interpretation": "Demand is not purely weekend leisure-driven; midweek occupancy matters for RevPAR.",
        "recommendation": "Use weekday-specific pricing and corporate packages to protect midweek occupancy.",
    }


def plot_correlation_heatmap(df: pd.DataFrame) -> Insight:
    columns = [
        "is_canceled",
        "lead_time",
        "total_stay",
        "total_guests",
        "adr",
        "booking_value",
        "previous_cancellations",
        "booking_changes",
        "days_in_waiting_list",
        "required_car_parking_spaces",
        "total_of_special_requests",
        "room_type_changed",
        "is_repeated_guest",
    ]
    corr = df[columns].corr(numeric_only=True)
    ax = sns.heatmap(corr, cmap="vlag", center=0, annot=True, fmt=".2f", linewidths=0.4)
    ax.set_title("Correlation Heatmap of Core Booking Features")
    path = save_current_plot("15_correlation_heatmap.png")
    top_cancel_corr = corr["is_canceled"].drop("is_canceled").abs().sort_values(ascending=False).index[0]
    return {
        "title": "Correlation heatmap",
        "path": path,
        "insight": f"`{top_cancel_corr}` has the strongest linear relationship with cancellation among selected numeric features.",
        "interpretation": "Correlation is not causation, but it helps prioritize variables for churn modeling and dashboard filters.",
        "recommendation": "Use the strongest cancellation-correlated features as baseline inputs for Week 3 predictive modeling.",
    }


def plot_pairplot(df: pd.DataFrame) -> Insight:
    sample = df[["is_canceled", "lead_time", "adr", "total_stay", "total_guests", "booking_value"]].sample(
        n=min(2500, len(df)), random_state=42
    )
    grid = sns.pairplot(
        sample,
        vars=["lead_time", "adr", "total_stay", "total_guests", "booking_value"],
        hue="is_canceled",
        diag_kind="hist",
        corner=True,
        plot_kws={"alpha": 0.35, "s": 14},
    )
    grid.fig.suptitle("Pairplot of Pricing, Lead Time, Stay Length, and Cancellation", y=1.02)
    path = VISUALIZATIONS_DIR / "16_pairplot_core_features.png"
    grid.savefig(path, bbox_inches="tight", dpi=140)
    plt.close("all")
    return {
        "title": "Pairplots where useful",
        "path": str(path.relative_to(VISUALIZATIONS_DIR.parent)),
        "insight": "The pairplot shows cancellation separation most visibly across lead time and booking value ranges.",
        "interpretation": "Feature interactions matter; cancellation risk is unlikely to be explained by a single variable.",
        "recommendation": "Use multivariate models rather than one-way threshold rules for cancellation prediction.",
    }


def plot_cancellation_by_dimension(df: pd.DataFrame, column: str, filename: str, title: str) -> Insight:
    table = cancellation_rate_table(df, column).head(12)
    ax = sns.barplot(data=table, x="cancellation_rate", y=column, hue=column, palette="rocket", legend=False)
    ax.set_title(title)
    ax.set_xlabel("Cancellation Rate")
    ax.set_ylabel(column.replace("_", " ").title())
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    path = save_current_plot(filename)
    riskiest = table.sort_values("cancellation_rate", ascending=False).iloc[0][column]
    return {
        "title": title,
        "path": path,
        "insight": f"`{riskiest}` has the highest cancellation rate among the displayed {column.replace('_', ' ')} groups.",
        "interpretation": "Cancellation risk varies materially by segment, making blanket retention tactics inefficient.",
        "recommendation": f"Prioritize retention offers and deposit-policy review for high-risk `{column}` categories.",
    }


def plot_adr_vs_cancellation(df: pd.DataFrame) -> Insight:
    temp = df.copy()
    temp["adr_bin"] = pd.qcut(temp["adr"], q=10, duplicates="drop")
    table = temp.groupby("adr_bin", observed=True).agg(cancellation_rate=("is_canceled", "mean"), bookings=("is_canceled", "size")).reset_index()
    table["adr_bin"] = table["adr_bin"].astype(str)
    ax = sns.lineplot(data=table, x="adr_bin", y="cancellation_rate", marker="o", color="#F58518")
    ax.set_title("ADR Decile vs Cancellation Rate")
    ax.set_xlabel("ADR Decile")
    ax.set_ylabel("Cancellation Rate")
    ax.tick_params(axis="x", rotation=45)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    path = save_current_plot("19_adr_vs_cancellation.png")
    return {
        "title": "ADR vs cancellation",
        "path": path,
        "insight": "Cancellation rate changes across ADR bands rather than remaining flat.",
        "interpretation": "Price level is connected to booking confidence, perceived value, and customer flexibility.",
        "recommendation": "Test cancellation-risk-adjusted pricing and value-add bundles in ADR bands with elevated cancellation.",
    }


def plot_lead_time_vs_cancellation(df: pd.DataFrame) -> Insight:
    order = ["Last-minute booker", "Short-window planner", "Medium-window planner", "Early planner"]
    table = (
        df.groupby("lead_time_bucket", observed=True)
        .agg(cancellation_rate=("is_canceled", "mean"), bookings=("is_canceled", "size"))
        .reindex(order)
        .reset_index()
    )
    ax = sns.barplot(data=table, x="lead_time_bucket", y="cancellation_rate", hue="lead_time_bucket", palette="crest", legend=False)
    ax.set_title("Lead Time Segment vs Cancellation Rate")
    ax.set_xlabel("Lead Time Segment")
    ax.set_ylabel("Cancellation Rate")
    ax.tick_params(axis="x", rotation=25)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    path = save_current_plot("20_lead_time_vs_cancellation.png")
    highest = table.loc[table["cancellation_rate"].idxmax(), "lead_time_bucket"]
    return {
        "title": "Lead time vs cancellation",
        "path": path,
        "insight": f"{highest} bookings have the highest cancellation rate.",
        "interpretation": "Lead time is a practical early warning signal because it is known at booking time.",
        "recommendation": "Trigger retention communications and stricter inventory controls for high-risk lead-time buckets.",
    }


def plot_length_of_stay(df: pd.DataFrame) -> Insight:
    table = df.groupby("stay_length_bucket", observed=True).agg(bookings=("is_canceled", "size"), cancellation_rate=("is_canceled", "mean"), avg_adr=("adr", "mean")).reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    sns.barplot(data=table, x="stay_length_bucket", y="bookings", hue="stay_length_bucket", palette="Set3", legend=False, ax=axes[0])
    sns.barplot(data=table, x="stay_length_bucket", y="cancellation_rate", hue="stay_length_bucket", palette="Set3", legend=False, ax=axes[1])
    axes[0].set_title("Bookings by Stay Length")
    axes[1].set_title("Cancellation Rate by Stay Length")
    axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    for ax in axes:
        ax.tick_params(axis="x", rotation=25)
        ax.set_xlabel("Stay Length Segment")
    path = save_current_plot("21_length_of_stay_analysis.png")
    return {
        "title": "Length of stay analysis",
        "path": path,
        "insight": "Booking volume and cancellation rate differ by length-of-stay segment.",
        "interpretation": "Long-stay and short-stay guests should be managed with different cancellation and pricing rules.",
        "recommendation": "Create length-of-stay controls such as minimum-stay rules in peak periods and targeted discounts in low-demand periods.",
    }


def build_segmentation_report(df: pd.DataFrame) -> str:
    segment_summary = build_segment_summary(df)
    segment_summary.to_csv(SEGMENTS_PATH, index=False)

    definitions = """
## Customer Segmentation

| Segment | Rule | Business Use |
|---|---|---|
| Business travellers | Corporate market segment or corporate distribution channel | Weekday occupancy, negotiated rates, lower-friction booking workflows |
| Leisure travellers | Non-corporate demand, including families and vacation stays | Packages, seasonal promotions, ancillary upsell |
| Early planners | Lead time greater than 90 days | Cancellation-risk monitoring and early-bird rate fences |
| Last-minute bookers | Lead time up to 7 days | Yield capture and distressed inventory sales |
| High-value customers | Booking value at or above the 75th percentile | VIP retention, upgrade offers, and revenue protection |
"""
    risky_segments = (
        segment_summary[segment_summary["bookings"] >= 100]
        .sort_values("cancellation_rate", ascending=False)
        .head(10)
    )
    top_segments_md = markdown_table(segment_summary.head(12))
    risky_segments_md = markdown_table(risky_segments)
    return f"""{definitions}

### Largest Customer Segments

{top_segments_md}

### Highest Cancellation Segments With Meaningful Volume

{risky_segments_md}
"""


def write_reports(df: pd.DataFrame, insights: list[Insight]) -> None:
    overall_cancel = df["is_canceled"].mean()
    avg_adr = df["adr"].mean()
    avg_lead = df["lead_time"].mean()
    rev_by_season = df.groupby("booking_season", observed=True)["booking_value"].sum().sort_values(ascending=False)
    top_market = df["market_segment"].value_counts().idxmax()

    insight_sections = "\n\n".join(
        f"""### {item["title"]}

![{item["title"]}](../{item["path"]})

- Business insight: {item["insight"]}
- Interpretation: {item["interpretation"]}
- Recommendation: {item["recommendation"]}"""
        for item in insights
    )

    segmentation = build_segmentation_report(df)

    EDA_REPORT_PATH.write_text(
        f"""# Week 2 EDA Summary Report

## Executive Summary

- Cleaned bookings analyzed: {len(df):,}
- Cancellation rate: {overall_cancel:.2%}
- Average ADR: {avg_adr:.2f}
- Average lead time: {avg_lead:.1f} days
- Largest market segment: {top_market}
- Highest booking-value season: {rev_by_season.index[0]}

This EDA establishes the analytical foundation for customer retention and dynamic pricing. Cancellation risk is visibly associated with lead time, market segment, deposit type, hotel type, and value bands. ADR and demand also vary across months, seasons, countries, and stay patterns, supporting a future dynamic pricing engine.

## Visualization Insights

{insight_sections}

{segmentation}
""",
        encoding="utf-8",
    )

    BUSINESS_RECOMMENDATIONS_PATH.write_text(
        f"""# Business Recommendations

## Revenue Optimization Recommendations

- Manage City Hotel and Resort Hotel independently because demand mix, ADR, and cancellation behavior differ.
- Use monthly and seasonal ADR bands rather than one annual average rate.
- Raise rate floors in months or seasons where booking volume is high but ADR is not peaking.
- Monitor booking value and ADR percentile bands to avoid overreacting to extreme rates.
- Add length-of-stay rules during high-demand periods to improve total booking value.

## Customer Retention Recommendations

- Prioritize high-lead-time bookings for automated retention messaging and pre-arrival confirmation.
- Review deposit and cancellation policies for market segments with high cancellation rates.
- Build country-specific retention campaigns for high-volume origin markets.
- Protect high-value customers with targeted upgrade, parking, meal, or flexible check-in incentives.
- Treat repeated guests separately from first-time guests because loyalty behavior changes cancellation risk.

## Dynamic Pricing Recommendations

- Include season, month, hotel type, market segment, distribution channel, lead time, and country in future pricing rules.
- Apply cancellation-risk-adjusted expected revenue: `expected_revenue = ADR * total_stay * (1 - cancellation_probability)`.
- Use last-minute demand to capture yield when occupancy is strong, but discount selectively when unsold inventory remains.
- Use early-planner price fences: offer value-adds instead of pure discounts where cancellation risk is high.
- Compare weekday and weekend demand separately before setting promotional rates.

## Dashboard Metrics to Track

- RevPAR proxy using ADR and consumed room nights.
- Cancellation rate by hotel, market segment, deposit type, country, and lead-time bucket.
- ADR by month, season, country, and stay-length bucket.
- Booking curve: cumulative bookings by lead time.
- High-value customer cancellation exposure.
""",
        encoding="utf-8",
    )


def run_eda() -> None:
    ensure_directories()
    df = load_cleaned_dataset()

    plotters: list[Callable[[pd.DataFrame], Insight]] = [
        plot_booking_distribution,
        plot_cancellation_analysis,
        plot_adr_analysis,
        lambda data: plot_category_distribution(data, "hotel", "04_hotel_type.png", "Hotel type"),
        lambda data: plot_category_distribution(data, "customer_type", "05_customer_type.png", "Customer type"),
        lambda data: plot_category_distribution(data, "market_segment", "06_market_segment.png", "Market segment"),
        lambda data: plot_category_distribution(data, "distribution_channel", "07_distribution_channel.png", "Distribution channel"),
        lambda data: plot_category_distribution(data, "deposit_type", "08_deposit_type.png", "Deposit type"),
        plot_lead_time,
        plot_monthly_trends,
        plot_seasonal_trends,
        plot_country_analysis,
        plot_weekday_weekend,
        plot_correlation_heatmap,
        plot_pairplot,
        lambda data: plot_cancellation_by_dimension(data, "hotel", "17_cancellation_by_hotel_type.png", "Cancellation by hotel type"),
        lambda data: plot_cancellation_by_dimension(data, "market_segment", "18_cancellation_by_market_segment.png", "Cancellation by market segment"),
        plot_adr_vs_cancellation,
        plot_lead_time_vs_cancellation,
        plot_length_of_stay,
    ]

    insights = [plotter(df) for plotter in plotters]
    write_reports(df, insights)

    print(f"EDA report saved to: {EDA_REPORT_PATH}")
    print(f"Business recommendations saved to: {BUSINESS_RECOMMENDATIONS_PATH}")
    print(f"Visualizations saved to: {VISUALIZATIONS_DIR}")


if __name__ == "__main__":
    run_eda()
