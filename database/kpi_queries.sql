-- KPI Calculation Queries for Redshift
-- These queries power the 7-metric KPI dashboard

-- ============================================
-- KPI 1: Total Income (Current Month)
-- ============================================
SELECT 
    user_id,
    SUM(amount) as total_income,
    COUNT(*) as income_transactions
FROM fact_transactions
WHERE transaction_type = 'income'
    AND date_key >= (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE))
    AND date_key < (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
GROUP BY user_id;

-- ============================================
-- KPI 2: Total Expenses (Current Month)
-- ============================================
SELECT 
    user_id,
    SUM(amount) as total_expenses,
    COUNT(*) as expense_transactions
FROM fact_transactions
WHERE transaction_type = 'expense'
    AND date_key >= (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE))
    AND date_key < (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
GROUP BY user_id;

-- ============================================
-- KPI 3: Net Cash Flow (Current Month)
-- ============================================
SELECT 
    user_id,
    SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE -amount END) as net_cashflow
FROM fact_transactions
WHERE date_key >= (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE))
    AND date_key < (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
GROUP BY user_id;

-- ============================================
-- KPI 4: Savings Rate (Current Month)
-- ============================================
SELECT 
    user_id,
    total_income,
    total_expenses,
    net_cashflow,
    CASE 
        WHEN total_income > 0 
        THEN (net_cashflow / total_income) * 100 
        ELSE 0 
    END as savings_rate_percent
FROM (
    SELECT 
        user_id,
        SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as total_income,
        SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as total_expenses,
        SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE -amount END) as net_cashflow
    FROM fact_transactions
    WHERE date_key >= (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE))
        AND date_key < (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
    GROUP BY user_id
) monthly_totals;

-- ============================================
-- KPI 5: Expense Categories Breakdown (Current Month)
-- ============================================
SELECT 
    ft.user_id,
    dc.category_id,
    dc.category_name,
    SUM(ft.amount) as category_total,
    COUNT(*) as transaction_count,
    (SUM(ft.amount) * 100.0 / NULLIF(SUM(SUM(ft.amount)) OVER (PARTITION BY ft.user_id), 0)) as percentage_of_total
FROM fact_transactions ft
JOIN dim_category dc ON ft.category_id = dc.category_id
WHERE ft.transaction_type = 'expense'
    AND ft.date_key >= (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE))
    AND ft.date_key < (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
GROUP BY ft.user_id, dc.category_id, dc.category_name
ORDER BY category_total DESC;

-- ============================================
-- KPI 6: Monthly Trend Analysis (Last 12 Months)
-- ============================================
SELECT 
    user_id,
    year,
    month,
    month_name,
    total_income,
    total_expenses,
    net_cashflow,
    savings_rate,
    transaction_count
FROM vw_kpi_dashboard
WHERE date_value >= DATEADD(month, -12, CURRENT_DATE)
ORDER BY user_id, year DESC, month DESC;

-- ============================================
-- KPI 7: Budget vs Actual (Current Month)
-- ============================================
-- Note: This requires joining with budget data from RDS
-- For now, showing category spending vs average
SELECT 
    ft.user_id,
    dc.category_id,
    dc.category_name,
    SUM(ft.amount) as actual_spending,
    AVG(ft.amount) as avg_monthly_spending,
    SUM(ft.amount) - AVG(ft.amount) as variance,
    CASE 
        WHEN AVG(ft.amount) > 0 
        THEN ((SUM(ft.amount) - AVG(ft.amount)) / AVG(ft.amount)) * 100 
        ELSE 0 
    END as variance_percent
FROM fact_transactions ft
JOIN dim_category dc ON ft.category_id = dc.category_id
WHERE ft.transaction_type = 'expense'
    AND ft.date_key >= (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE))
    AND ft.date_key < (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
GROUP BY ft.user_id, dc.category_id, dc.category_name
ORDER BY variance DESC;

-- ============================================
-- Comprehensive Dashboard Query (All 7 KPIs)
-- ============================================
WITH current_month AS (
    SELECT 
        date_key,
        date_value
    FROM dim_date
    WHERE date_value = DATE_TRUNC('month', CURRENT_DATE)
),
monthly_totals AS (
    SELECT 
        ft.user_id,
        SUM(CASE WHEN ft.transaction_type = 'income' THEN ft.amount ELSE 0 END) as total_income,
        SUM(CASE WHEN ft.transaction_type = 'expense' THEN ft.amount ELSE 0 END) as total_expenses,
        SUM(CASE WHEN ft.transaction_type = 'income' THEN ft.amount ELSE -ft.amount END) as net_cashflow,
        COUNT(*) as transaction_count
    FROM fact_transactions ft
    CROSS JOIN current_month cm
    WHERE ft.date_key >= cm.date_key
        AND ft.date_key < cm.date_key + 31
    GROUP BY ft.user_id
),
category_breakdown AS (
    SELECT 
        ft.user_id,
        dc.category_name,
        SUM(ft.amount) as category_amount
    FROM fact_transactions ft
    JOIN dim_category dc ON ft.category_id = dc.category_id
    CROSS JOIN current_month cm
    WHERE ft.transaction_type = 'expense'
        AND ft.date_key >= cm.date_key
        AND ft.date_key < cm.date_key + 31
    GROUP BY ft.user_id, dc.category_name
),
trend_data AS (
    SELECT 
        user_id,
        year,
        month,
        total_income,
        total_expenses,
        net_cashflow
    FROM fact_monthly_summary
    WHERE date_key >= (SELECT date_key FROM dim_date WHERE date_value >= DATEADD(month, -12, CURRENT_DATE))
)
SELECT 
    mt.user_id,
    -- KPI 1-4: Core Metrics
    COALESCE(mt.total_income, 0) as kpi_total_income,
    COALESCE(mt.total_expenses, 0) as kpi_total_expenses,
    COALESCE(mt.net_cashflow, 0) as kpi_net_cashflow,
    CASE 
        WHEN mt.total_income > 0 
        THEN (mt.net_cashflow / mt.total_income) * 100 
        ELSE 0 
    END as kpi_savings_rate,
    -- KPI 5: Category Breakdown (JSON format for frontend)
    (SELECT json_agg(json_build_object(
        'category', category_name,
        'amount', category_amount
    )) FROM category_breakdown WHERE user_id = mt.user_id) as kpi_category_breakdown,
    -- KPI 6: Trend Data (JSON format)
    (SELECT json_agg(json_build_object(
        'year', year,
        'month', month,
        'income', total_income,
        'expenses', total_expenses,
        'cashflow', net_cashflow
    ) ORDER BY year DESC, month DESC) FROM trend_data WHERE user_id = mt.user_id) as kpi_monthly_trend,
    -- KPI 7: Budget Variance (placeholder - requires budget data)
    mt.transaction_count as kpi_transaction_count
FROM monthly_totals mt;


