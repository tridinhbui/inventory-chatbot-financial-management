-- Redshift Schema - Analytical Data Warehouse
-- Optimized for analytical queries and aggregations

-- Date dimension table
CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,
    date_value DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    week INT NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_month_end BOOLEAN NOT NULL
);

-- User dimension
CREATE TABLE dim_user (
    user_id INT PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(255),
    created_at TIMESTAMP
);

-- Account dimension
CREATE TABLE dim_account (
    account_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    account_name VARCHAR(100),
    account_type VARCHAR(50),
    currency VARCHAR(3)
);

-- Category dimension
CREATE TABLE dim_category (
    category_id INT PRIMARY KEY,
    user_id INT,
    category_name VARCHAR(100),
    category_type VARCHAR(20),
    parent_category_id INT
);

-- Fact transactions table (denormalized for analytics)
CREATE TABLE fact_transactions (
    transaction_id BIGINT,
    user_id INT NOT NULL,
    account_id INT,
    category_id INT,
    date_key INT NOT NULL,
    transaction_date DATE NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    description VARCHAR(500),
    merchant_name VARCHAR(200),
    payment_method VARCHAR(50),
    created_at TIMESTAMP,
    -- Distribution and sort keys for performance
    PRIMARY KEY (transaction_id, date_key)
)
DISTKEY (user_id)
SORTKEY (date_key, user_id);

-- Monthly aggregations (materialized view equivalent)
CREATE TABLE fact_monthly_summary (
    summary_id BIGSERIAL,
    user_id INT NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    date_key INT NOT NULL,
    total_income DECIMAL(18,2) DEFAULT 0.00,
    total_expenses DECIMAL(18,2) DEFAULT 0.00,
    net_cashflow DECIMAL(18,2) DEFAULT 0.00,
    transaction_count INT DEFAULT 0,
    avg_transaction_amount DECIMAL(18,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (summary_id),
    UNIQUE (user_id, year, month)
)
DISTKEY (user_id)
SORTKEY (date_key, user_id);

-- Category spending summary
CREATE TABLE fact_category_summary (
    summary_id BIGSERIAL,
    user_id INT NOT NULL,
    category_id INT,
    date_key INT NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    total_amount DECIMAL(18,2) DEFAULT 0.00,
    transaction_count INT DEFAULT 0,
    avg_amount DECIMAL(18,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (summary_id),
    UNIQUE (user_id, category_id, year, month)
)
DISTKEY (user_id)
SORTKEY (date_key, user_id);

-- Indexes (Redshift uses different indexing)
-- Note: Redshift automatically creates indexes on PRIMARY KEY and UNIQUE constraints

-- View for KPI calculations
CREATE VIEW vw_kpi_dashboard AS
SELECT 
    u.user_id,
    u.username,
    d.year,
    d.month,
    d.month_name,
    d.date_value,
    COALESCE(ms.total_income, 0) as total_income,
    COALESCE(ms.total_expenses, 0) as total_expenses,
    COALESCE(ms.net_cashflow, 0) as net_cashflow,
    COALESCE(ms.transaction_count, 0) as transaction_count,
    CASE 
        WHEN COALESCE(ms.total_income, 0) > 0 
        THEN (COALESCE(ms.net_cashflow, 0) / ms.total_income) * 100 
        ELSE 0 
    END as savings_rate,
    COALESCE(ms.avg_transaction_amount, 0) as avg_transaction_amount
FROM dim_user u
CROSS JOIN dim_date d
LEFT JOIN fact_monthly_summary ms ON u.user_id = ms.user_id AND d.date_key = ms.date_key
WHERE d.date_value >= DATEADD(month, -12, CURRENT_DATE::DATE)
ORDER BY u.user_id, d.date_key DESC;

