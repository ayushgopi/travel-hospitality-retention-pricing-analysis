# Power BI Dashboard Specification

## Data Source

Use:

`data/processed/cleaned_hotel_bookings.csv`

Optional supporting files:

- `data/processed/customer_segments.csv`
- `data/processed/week3_model_metrics.csv`
- `data/processed/week4_dashboard_summary.csv`

Rename the main table in Power BI to:

`cleaned_hotel_bookings`

## Theme

Import:

`powerbi/hospitality_dark_blue_theme.json`

Recommended colors:

| Role | HEX |
|---|---|
| Page background | `#071A2F` |
| Visual background | `#0B2744` |
| Accent blue | `#2F80ED` |
| Light blue | `#56CCF2` |
| Success green | `#27AE60` |
| Warning orange | `#F2994A` |
| Cancellation red | `#EB5757` |
| Text white | `#FFFFFF` |
| Muted text | `#AFCBEA` |

Use Segoe UI / Segoe UI Semibold. Keep slicers on a top or left filter rail.

## Data Model Setup

Create a date column if needed:

```DAX
Arrival Date =
DATE(
    cleaned_hotel_bookings[arrival_date_year],
    cleaned_hotel_bookings[arrival_month_number],
    cleaned_hotel_bookings[arrival_date_day_of_month]
)
```

Create status labels:

```DAX
Booking Status =
IF(cleaned_hotel_bookings[is_canceled] = 1, "Cancelled", "Completed")
```

Create a month sort column:

```DAX
Month Sort = cleaned_hotel_bookings[arrival_month_number]
```

Sort `arrival_date_month` by `Month Sort`.

## Page Size and Grid

- Canvas: 16:9
- Page background: `#071A2F`
- Outer margin: 24 px
- Visual corner radius: 12 px
- Header height: 70 px
- Filter rail height: 54 px
- KPI card height: 105 px

## Page 1 - Executive Summary

Purpose: Give leadership a portfolio-level view of demand, cancellations, ADR, and market mix.

### Layout

| Section | Position |
|---|---|
| Title | x 24, y 16, w 760, h 42 |
| Filter rail | x 24, y 72, w 1230, h 54 |
| KPI cards | x 24, y 145, six cards across |
| Monthly trend | x 24, y 275, w 560, h 275 |
| Hotel type + booking status | x 604, y 275, w 300 each, h 275 |
| Top countries map | x 24, y 570, w 560, h 125 |
| Market segment bar | x 604, y 570, w 650, h 125 |

### KPI Cards

| KPI | Measure |
|---|---|
| Total Bookings | `[Total Bookings]` |
| Total Cancelled Bookings | `[Cancelled Bookings]` |
| Cancellation Rate % | `[Cancellation Rate %]` |
| Average Daily Rate | `[Average Daily Rate]` |
| Average Stay Duration | `[Average Stay Duration]` |
| Average Lead Time | `[Average Lead Time]` |
| Total Guests | `[Total Guests]` |

### Visuals

| Visual | Type | Fields |
|---|---|---|
| Monthly Booking Trend | Line chart | Axis: `arrival_date_month`; Values: `[Total Bookings]`; Sort: `arrival_month_number` |
| Booking by Hotel Type | Clustered bar | Axis: `hotel`; Values: `[Total Bookings]` |
| Booking Status | Donut chart | Legend: `Booking Status`; Values: `[Total Bookings]` |
| Top 10 Countries | Filled map or map | Location: `country`; Size: `[Total Bookings]`; Filter: Top N 10 by bookings |
| Market Segment | Bar chart | Axis: `market_segment`; Values: `[Total Bookings]`; Tooltips: `[Cancellation Rate %]`, `[Average Daily Rate]` |

### Slicers

- `hotel`
- `arrival_date_month`
- `country`
- `customer_type`

### Page Insight

The executive page should show whether demand growth is coming with healthy ADR and manageable cancellation risk. Use cancellation rate as the primary warning KPI and ADR as the primary pricing KPI.

## Page 2 - Customer Insights

Purpose: Explain who books, through which channels, and which customer groups should receive retention or pricing actions.

### Layout

| Section | Position |
|---|---|
| Title and insight banner | x 24, y 16, w 1230, h 70 |
| Filter rail | x 24, y 92, w 1230, h 54 |
| Customer Type Distribution | x 24, y 165, w 360, h 230 |
| Market Segment Analysis | x 404, y 165, w 420, h 230 |
| Distribution Channel | x 844, y 165, w 410, h 230 |
| Deposit Type | x 24, y 420, w 300, h 230 |
| Lead Time Distribution | x 344, y 420, w 390, h 230 |
| Weekend vs Weekday Stay | x 754, y 420, w 250, h 230 |
| Guest Composition | x 1024, y 420, w 230, h 230 |
| Customer Segmentation | x 24, y 660, w 1230, h 40 compact strip |

### Visuals

| Visual | Type | Fields |
|---|---|---|
| Customer Type Distribution | Donut chart | Legend: `customer_type`; Values: `[Total Bookings]` |
| Market Segment Analysis | Clustered bar | Axis: `market_segment`; Values: `[Total Bookings]`, `[Cancellation Rate %]` as tooltip |
| Distribution Channel | Bar chart | Axis: `distribution_channel`; Values: `[Total Bookings]` |
| Deposit Type | Donut chart | Legend: `deposit_type`; Values: `[Total Bookings]` |
| Lead Time Distribution | Histogram or column chart | Axis: `lead_time_bucket`; Values: `[Total Bookings]` |
| Weekend vs Weekday Stay | Clustered column | Axis: `Stay Type`; Values: `[Weekend Nights]`, `[Weekday Nights]` |
| Guest Composition | Stacked bar | Values: `[Total Adults]`, `[Total Children]`, `[Total Babies]` |
| Customer Segmentation | Matrix or bar | Rows: `traveller_segment`, `lead_time_bucket`, `customer_value_segment`; Values: `[Total Bookings]`, `[Cancellation Rate %]`, `[Gross Booking Value]` |

### Insights Beside Visuals

- Customer Type: Transient customers dominate booking volume, so retention should focus on high-risk transient bookings.
- Market Segment: Online TA volume is high; monitor OTA cancellation exposure and commission impact.
- Distribution Channel: TA/TO-heavy bookings should be tracked separately from direct bookings.
- Deposit Type: Deposit policy is a strong retention lever and should be reviewed by segment.
- Lead Time: Early planners carry higher cancellation exposure and need pre-arrival engagement.
- Weekend vs Weekday: Weekday demand supports corporate and midweek pricing opportunities.
- Guest Composition: Families and multi-guest stays are useful for package and upsell targeting.
- Segmentation: Combine traveller segment, lead-time bucket, and value segment to prioritize offers.

## Page 3 - Pricing & Retention

Purpose: Connect pricing behavior, cancellation risk, and revenue-management recommendations.

### Layout

| Section | Position |
|---|---|
| Title and slicers | x 24, y 16, w 1230, h 125 |
| ADR Trend | x 24, y 160, w 420, h 230 |
| ADR vs Cancellation | x 464, y 160, w 390, h 230 |
| Cancellation by Market Segment | x 874, y 160, w 380, h 230 |
| Cancellation by Deposit Type | x 24, y 410, w 300, h 210 |
| Cancellation by Hotel Type | x 344, y 410, w 300, h 210 |
| Seasonal Booking Trend | x 664, y 410, w 310, h 210 |
| Booking Changes Analysis | x 994, y 410, w 260, h 100 |
| Special Requests Analysis | x 994, y 520, w 260, h 100 |
| Recommendation panel | x 24, y 640, w 1230, h 60 |

### Visuals

| Visual | Type | Fields |
|---|---|---|
| ADR Trend | Line chart | Axis: `arrival_date_month`; Values: `[Average Daily Rate]`; Tooltips: `[Total Bookings]`, `[Cancellation Rate %]` |
| ADR vs Cancellation | Scatter plot | X: `adr`; Y: `is_canceled` or `[Cancellation Rate %]` by ADR bin; Size: `booking_value`; Details: `market_segment` |
| Cancellation by Market Segment | Bar chart | Axis: `market_segment`; Values: `[Cancellation Rate %]`; Tooltip: `[Cancelled Bookings]` |
| Cancellation by Deposit Type | Bar chart | Axis: `deposit_type`; Values: `[Cancellation Rate %]` |
| Cancellation by Hotel Type | Bar chart | Axis: `hotel`; Values: `[Cancellation Rate %]` |
| Seasonal Booking Trend | Combo chart | Axis: `booking_season`; Column: `[Total Bookings]`; Line: `[Average Daily Rate]` |
| Booking Changes Analysis | Card or bar | Values: `[Booking Change Rate %]`; Axis optional: `booking_changes` |
| Special Requests Analysis | Card or bar | Values: `[Special Request Rate %]`; Axis optional: `total_of_special_requests` |

### Business Recommendation Section

Revenue Optimization:

- Use cancellation-adjusted expected revenue, not raw booking value.
- Protect high-value bookings with retention actions before arrival.
- Monitor City Hotel and Resort Hotel independently.

Dynamic Pricing:

- Use seasonal price floors.
- Increase rates in high-demand months while checking cancellation rate.
- Use last-minute pricing only when unsold inventory remains.

Customer Retention:

- Trigger pre-arrival reminders for early planners.
- Use targeted offers for high-risk, high-value customers.
- Review deposit policy for high-risk segments.

Operational Recommendations:

- Staff and inventory planning should use expected demand after cancellation adjustment.
- Track OTA-heavy segments separately from direct bookings.
- Build weekly dashboard refresh cadence.

## Tooltips

Create a tooltip page with:

- `hotel`
- `market_segment`
- `[Total Bookings]`
- `[Cancellation Rate %]`
- `[Average Daily Rate]`
- `[Gross Booking Value]`
- `[Average Lead Time]`

Use this tooltip on market, country, hotel, and pricing visuals.

## Drill-Through

Recommended drill-through page:

`Country / Segment Detail`

Drill-through fields:

- `country`
- `market_segment`
- `hotel`

Detail visuals:

- Booking trend by month
- Cancellation rate
- ADR trend
- Customer type split
- Deposit type split

## Power BI Best Practices

- Use measures, not implicit aggregations.
- Sort months by `arrival_month_number`.
- Use Top N filters for country maps and long categorical charts.
- Keep slicers synced across all pages.
- Use consistent visual titles and tooltips.
- Format percentages with one or two decimals.
- Use conditional formatting: red for high cancellation, green for high completion.
- Keep every page to one business question.
- Avoid too many colors; use blue for volume, orange for ADR, red for cancellation.
- Use bookmarks only for optional views, not core navigation.

## Final Dashboard Story

Page 1 answers: What is happening overall?

Page 2 answers: Who is booking and which customer groups matter?

Page 3 answers: Where should pricing and retention actions change revenue outcomes?
