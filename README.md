# Travel, Tourism & Hospitality - Customer Retention and Dynamic Pricing Analysis

Week 1 through Week 4 analytics project using the Kaggle Hotel Booking Demand dataset by Jesse Mostipak.

## Project Structure

```text
travel_hospitality_retention_pricing/
  data/
    raw/                  # optional local dataset copy
    processed/            # generated cleaned datasets
  docs/
    git_commit_messages.md
  notebooks/
    01_week1_data_cleaning.ipynb
    02_week2_eda.ipynb
    03_week3_predictive_modeling.ipynb
    04_week4_final_handoff.ipynb
  reports/
    data_cleaning_report.md
    eda_summary_report.md
    business_recommendations.md
    week3_modeling_report.md
    week4_executive_summary.md
    week4_final_business_report.md
    week4_final_presentation.pptx
  sql/
    business_metrics.sql
  src/
    config.py
    clean_data.py
    eda_analysis.py
    predictive_modeling.py
    finalize_week4.py
  visualizations/         # generated charts
```

## Dataset

The scripts use this source file by default:

```bash
/Users/ayush/imuages/hotel_bookings.csv
```

You can override it:

```bash
export HOTEL_BOOKINGS_SOURCE="/absolute/path/to/hotel_bookings.csv"
```

## macOS / VS Code Setup

```bash
cd "/Users/ayush/Documents/New project/travel_hospitality_retention_pricing"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Week 1

```bash
python src/clean_data.py
```

Outputs:

- `data/processed/cleaned_hotel_bookings.csv`
- `data/processed/customer_segments.csv`
- `reports/data_cleaning_report.md`

## Run Week 2

```bash
python src/eda_analysis.py
```

Outputs:

- charts in `visualizations/`
- `reports/eda_summary_report.md`
- `reports/business_recommendations.md`

## Run Week 3

```bash
python src/predictive_modeling.py
```

Outputs:

- `data/processed/week3_model_metrics.csv`
- `data/processed/week3_feature_importance.csv`
- `reports/week3_modeling_report.md`
- modeling charts in `visualizations/`

## Run Week 4

```bash
python src/finalize_week4.py
```

Outputs:

- `data/processed/week4_dashboard_summary.csv`
- `reports/week4_executive_summary.md`
- `reports/week4_final_business_report.md`
- `reports/week4_final_presentation.pptx`

## SQL

Use `sql/business_metrics.sql` in MySQL after loading `cleaned_hotel_bookings.csv` into a table named `cleaned_hotel_bookings`.

## Suggested Workflow

1. Run Week 1 cleaning.
2. Inspect `reports/data_cleaning_report.md`.
3. Run Week 2 EDA.
4. Run Week 3 modeling.
5. Run Week 4 final handoff.
6. Inspect generated charts, model metrics, reports, and presentation.
7. Open the notebooks in VS Code for an analyst-friendly, step-by-step view.
