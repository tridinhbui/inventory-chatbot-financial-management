-- Initialize Date Dimension Table for Redshift
-- This script populates the dim_date table with date values

-- Generate dates for the last 5 years and next 2 years
INSERT INTO dim_date (date_key, date_value, year, quarter, month, month_name, week, day_of_month, day_of_week, day_name, is_weekend, is_month_end)
SELECT 
    CAST(TO_CHAR(d, 'YYYYMMDD') AS INT) as date_key,
    d::DATE as date_value,
    EXTRACT(YEAR FROM d)::INT as year,
    EXTRACT(QUARTER FROM d)::INT as quarter,
    EXTRACT(MONTH FROM d)::INT as month,
    TO_CHAR(d, 'Month') as month_name,
    EXTRACT(WEEK FROM d)::INT as week,
    EXTRACT(DAY FROM d)::INT as day_of_month,
    EXTRACT(DOW FROM d)::INT as day_of_week,
    TO_CHAR(d, 'Day') as day_name,
    CASE WHEN EXTRACT(DOW FROM d) IN (0, 6) THEN TRUE ELSE FALSE END as is_weekend,
    CASE WHEN d = DATE_TRUNC('month', d) + INTERVAL '1 month' - INTERVAL '1 day' THEN TRUE ELSE FALSE END as is_month_end
FROM (
    SELECT generate_series(
        DATE '2019-01-01',
        DATE '2026-12-31',
        INTERVAL '1 day'
    )::DATE as d
) dates
WHERE NOT EXISTS (
    SELECT 1 FROM dim_date WHERE date_value = d::DATE
);


