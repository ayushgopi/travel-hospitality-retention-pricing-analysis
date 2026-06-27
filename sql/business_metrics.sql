-- Travel, Tourism & Hospitality - Customer Retention and Dynamic Pricing Analysis
-- MySQL business metric queries.
-- Assumption: cleaned_hotel_bookings.csv has been loaded into a table named cleaned_hotel_bookings.

-- 1. Overall booking, cancellation, and ADR metrics
SELECT
    COUNT(*) AS total_bookings,
    SUM(is_canceled) AS canceled_bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(total_stay), 2) AS avg_total_stay,
    ROUND(SUM(booking_value), 2) AS gross_booking_value
FROM cleaned_hotel_bookings;

-- 2. Hotel-level revenue and cancellation performance
SELECT
    hotel,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(SUM(booking_value), 2) AS gross_booking_value,
    ROUND(SUM(booking_value * (1 - is_canceled)), 2) AS realized_booking_value
FROM cleaned_hotel_bookings
GROUP BY hotel
ORDER BY gross_booking_value DESC;

-- 3. Monthly booking curve and pricing trend
SELECT
    arrival_date_year,
    arrival_month_number,
    arrival_date_month,
    COUNT(*) AS bookings,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(SUM(booking_value), 2) AS gross_booking_value
FROM cleaned_hotel_bookings
GROUP BY arrival_date_year, arrival_month_number, arrival_date_month
ORDER BY arrival_date_year, arrival_month_number;

-- 4. Seasonal demand and pricing trend
SELECT
    booking_season,
    COUNT(*) AS bookings,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(total_stay), 2) AS avg_stay,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(SUM(booking_value), 2) AS gross_booking_value
FROM cleaned_hotel_bookings
GROUP BY booking_season
ORDER BY gross_booking_value DESC;

-- 5. Market segment cancellation exposure
SELECT
    market_segment,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(lead_time), 1) AS avg_lead_time,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(SUM(booking_value * is_canceled), 2) AS canceled_booking_value
FROM cleaned_hotel_bookings
GROUP BY market_segment
ORDER BY cancellation_rate_pct DESC, bookings DESC;

-- 6. Distribution channel performance
SELECT
    distribution_channel,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(SUM(booking_value), 2) AS gross_booking_value
FROM cleaned_hotel_bookings
GROUP BY distribution_channel
ORDER BY gross_booking_value DESC;

-- 7. Deposit type risk
SELECT
    deposit_type,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(lead_time), 1) AS avg_lead_time,
    ROUND(AVG(adr), 2) AS avg_adr
FROM cleaned_hotel_bookings
GROUP BY deposit_type
ORDER BY cancellation_rate_pct DESC;

-- 8. Booking curve: lead-time buckets
SELECT
    lead_time_bucket,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(SUM(booking_value), 2) AS gross_booking_value
FROM cleaned_hotel_bookings
GROUP BY lead_time_bucket
ORDER BY FIELD(
    lead_time_bucket,
    'Last-minute booker',
    'Short-window planner',
    'Medium-window planner',
    'Early planner'
);

-- 9. Top 20 countries by bookings
SELECT
    country,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(SUM(booking_value), 2) AS gross_booking_value
FROM cleaned_hotel_bookings
GROUP BY country
ORDER BY bookings DESC
LIMIT 20;

-- 10. Country-level cancellation risk with meaningful volume
SELECT
    country,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(lead_time), 1) AS avg_lead_time,
    ROUND(AVG(adr), 2) AS avg_adr
FROM cleaned_hotel_bookings
GROUP BY country
HAVING COUNT(*) >= 100
ORDER BY cancellation_rate_pct DESC
LIMIT 20;

-- 11. Customer segmentation summary
SELECT
    traveller_segment,
    lead_time_bucket,
    customer_value_segment,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(booking_value), 2) AS avg_booking_value,
    ROUND(AVG(total_stay), 2) AS avg_total_stay
FROM cleaned_hotel_bookings
GROUP BY traveller_segment, lead_time_bucket, customer_value_segment
ORDER BY bookings DESC;

-- 12. High-value customer cancellation exposure
SELECT
    customer_value_segment,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(SUM(booking_value), 2) AS gross_booking_value,
    ROUND(SUM(booking_value * is_canceled), 2) AS canceled_booking_value
FROM cleaned_hotel_bookings
GROUP BY customer_value_segment
ORDER BY gross_booking_value DESC;

-- 13. Weekday vs weekend consumed-room-night mix
SELECT
    SUM(stays_in_week_nights) AS weekday_nights,
    SUM(stays_in_weekend_nights) AS weekend_nights,
    ROUND(SUM(stays_in_week_nights) / NULLIF(SUM(total_stay), 0) * 100, 2) AS weekday_share_pct,
    ROUND(SUM(stays_in_weekend_nights) / NULLIF(SUM(total_stay), 0) * 100, 2) AS weekend_share_pct
FROM cleaned_hotel_bookings;

-- 14. Length-of-stay pricing and cancellation
SELECT
    stay_length_bucket,
    COUNT(*) AS bookings,
    ROUND(AVG(is_canceled) * 100, 2) AS cancellation_rate_pct,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(booking_value), 2) AS avg_booking_value
FROM cleaned_hotel_bookings
GROUP BY stay_length_bucket
ORDER BY avg_booking_value DESC;

-- 15. Expected revenue using cancellation-adjusted realized value
SELECT
    hotel,
    booking_season,
    market_segment,
    COUNT(*) AS bookings,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(is_canceled), 4) AS cancellation_probability,
    ROUND(SUM(booking_value * (1 - is_canceled)), 2) AS realized_revenue_proxy
FROM cleaned_hotel_bookings
GROUP BY hotel, booking_season, market_segment
ORDER BY realized_revenue_proxy DESC;
