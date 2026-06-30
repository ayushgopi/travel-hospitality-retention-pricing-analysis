# Week 4 Final Business Report

## Project Objective

Analyze historical hotel booking behavior to reduce cancellation-driven revenue leakage, identify customer retention opportunities, and create a data foundation for dynamic pricing decisions.

## Final KPI Snapshot

| metric_group | metric | display_value | business_use |
| --- | --- | --- | --- |
| Portfolio | Cleaned bookings | 86,638 | Dataset volume available for reporting and modeling |
| Retention | Cancellation rate | 27.69% | Primary retention KPI |
| Pricing | Average ADR | 107.04 | Baseline daily rate indicator |
| Demand | Average lead time | 80.0 days | Booking curve and cancellation-risk input |
| Revenue | Gross booking value | 34,389,455.24 | Revenue opportunity before cancellations |
| Revenue | Realized booking value proxy | 22,932,035.93 | Cancellation-adjusted historical value |
| Hotel Type | City Hotel cancellation rate | 30.21% | Hotel-level retention and forecasting benchmark |
| Hotel Type | Resort Hotel cancellation rate | 23.71% | Hotel-level retention and forecasting benchmark |
| Season | Summer gross booking value | 16,544,773.80 | Seasonal pricing and staffing benchmark |
| Season | Spring gross booking value | 7,949,671.47 | Seasonal pricing and staffing benchmark |
| Season | Autumn gross booking value | 5,938,183.33 | Seasonal pricing and staffing benchmark |
| Season | Winter gross booking value | 3,956,826.65 | Seasonal pricing and staffing benchmark |

## Highest Risk Customer Segments

| traveller_segment | lead_time_bucket | customer_value_segment | bookings | cancellation_rate | avg_booking_value |
| --- | --- | --- | --- | --- | --- |
| Leisure traveller | Early planner | Premium value | 4905 | 0.41 | 1267.67 |
| Leisure traveller | Short-window planner | Premium value | 1112 | 0.40 | 1233.75 |
| Leisure traveller | Medium-window planner | Premium value | 2237 | 0.38 | 1221.50 |
| Leisure traveller | Early planner | High value | 6194 | 0.37 | 634.44 |
| Leisure traveller | Early planner | Standard value | 16853 | 0.36 | 296.33 |
| Leisure traveller | Medium-window planner | High value | 3732 | 0.35 | 629.13 |
| Solo short-stay traveller | Early planner | Standard value | 1429 | 0.35 | 182.80 |
| Solo short-stay traveller | Medium-window planner | Standard value | 1506 | 0.32 | 177.85 |

## Seasonal Pricing Summary

| booking_season | bookings | avg_adr | gross_booking_value |
| --- | --- | --- | --- |
| Summer | 28903 | 137.70 | 16544773.80 |
| Spring | 23605 | 99.77 | 7949671.47 |
| Autumn | 18417 | 94.35 | 5938183.33 |
| Winter | 15713 | 76.42 | 3956826.65 |

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
