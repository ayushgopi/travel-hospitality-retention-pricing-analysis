# Week 1 Data Cleaning Report

## Source

- Dataset: `/Users/ayush/imuages/hotel_bookings.csv`
- Run timestamp: 2026-06-27T08:38:40
- Initial shape: 119,390 rows x 32 columns
- Final shape: 86,638 rows x 57 columns

## Cleaning Actions

| Action | Result |
|---|---:|
| Duplicate rows removed | 31,994 |
| Rows with invalid reservation status dates removed | 0 |
| Rows with negative numeric values removed | 0 |
| Rows with zero guests removed | 166 |
| Rows with zero stay nights removed | 651 |
| Rows with negative ADR removed | 1 |
| ADR cap used | 285.85 |
| ADR rows capped | 434 |
| Lead time cap used | 386 days |
| Lead time rows capped | 410 |

## Missing Value Treatment

| Column | Missing Before | Treatment |
|---|---:|---|
| company | 112,593 | Filled with `0` to mean no company association |
| agent | 16,340 | Filled with `0` to mean direct/no agent |
| country | 488 | Filled with `Unknown` |
| children | 4 | Filled with `0` |

Top missing columns before cleaning:

| column | missing_count |
| --- | --- |
| company | 112,593 |
| agent | 16,340 |
| country | 488 |
| children | 4 |
| hotel | 0 |
| is_canceled | 0 |
| lead_time | 0 |
| arrival_date_year | 0 |
| arrival_date_month | 0 |
| arrival_date_week_number | 0 |

Remaining missing values after cleaning:

```text
No remaining missing values.
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
| Bookings retained | 86,638 |
| Cancellation rate | 27.69% |
| Average ADR | 107.04 |
| Average total stay | 3.65 nights |
| Countries represented | 178 |
| Customer segments | 32 |

## Data Quality Notes

- `agent = 0` and `company = 0` are engineered placeholders for missing identifiers, not real IDs.
- ADR outliers are capped rather than deleted to preserve booking volume while limiting distortion in pricing analysis.
- Zero-night and zero-guest records are removed because they do not represent usable demand for RevPAR, retention, or stay-length analysis.
