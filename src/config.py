"""Project configuration for the hotel booking analytics pipeline."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SOURCE_DATA = Path("/Users/ayush/imuages/hotel_bookings.csv")
SOURCE_DATA = Path(os.getenv("HOTEL_BOOKINGS_SOURCE", DEFAULT_SOURCE_DATA))

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
VISUALIZATIONS_DIR = PROJECT_ROOT / "visualizations"

CLEANED_DATA_PATH = PROCESSED_DIR / "cleaned_hotel_bookings.csv"
SEGMENTS_PATH = PROCESSED_DIR / "customer_segments.csv"
CLEANING_REPORT_PATH = REPORTS_DIR / "data_cleaning_report.md"
EDA_REPORT_PATH = REPORTS_DIR / "eda_summary_report.md"
BUSINESS_RECOMMENDATIONS_PATH = REPORTS_DIR / "business_recommendations.md"
MODELING_REPORT_PATH = REPORTS_DIR / "week3_modeling_report.md"
MODEL_METRICS_PATH = PROCESSED_DIR / "week3_model_metrics.csv"
MODEL_FEATURE_IMPORTANCE_PATH = PROCESSED_DIR / "week3_feature_importance.csv"
WEEK4_DASHBOARD_SUMMARY_PATH = PROCESSED_DIR / "week4_dashboard_summary.csv"
WEEK4_FINAL_REPORT_PATH = REPORTS_DIR / "week4_final_business_report.md"
WEEK4_EXECUTIVE_SUMMARY_PATH = REPORTS_DIR / "week4_executive_summary.md"

MONTH_ORDER = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

SEASON_MAP = {
    "December": "Winter",
    "January": "Winter",
    "February": "Winter",
    "March": "Spring",
    "April": "Spring",
    "May": "Spring",
    "June": "Summer",
    "July": "Summer",
    "August": "Summer",
    "September": "Autumn",
    "October": "Autumn",
    "November": "Autumn",
}


def ensure_directories() -> None:
    """Create project output directories."""
    for path in [RAW_DIR, PROCESSED_DIR, REPORTS_DIR, VISUALIZATIONS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
