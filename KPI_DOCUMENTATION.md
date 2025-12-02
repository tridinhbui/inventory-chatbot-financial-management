# 7-Metric KPI Documentation

This document describes the 7 key performance indicators (KPIs) implemented in the Personal Finance Insight Engine.

## KPI Overview

The dashboard provides 7 comprehensive metrics for analyzing personal finances:

### 1. Total Income (Current Month)
**Description**: Sum of all income transactions for the current month.

**Calculation**:
```sql
SUM(amount) WHERE transaction_type = 'income' 
AND transaction_date >= start_of_current_month
```

**Display**: Currency format (e.g., $5,000.00)

**Use Case**: Track monthly income trends and identify income sources.

---

### 2. Total Expenses (Current Month)
**Description**: Sum of all expense transactions for the current month.

**Calculation**:
```sql
SUM(amount) WHERE transaction_type = 'expense' 
AND transaction_date >= start_of_current_month
```

**Display**: Currency format (e.g., $3,500.00)

**Use Case**: Monitor spending levels and identify high-spending months.

---

### 3. Net Cash Flow (Current Month)
**Description**: Difference between total income and total expenses.

**Calculation**:
```sql
SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE -amount END)
```

**Display**: Currency format, color-coded:
- Green: Positive cash flow
- Red: Negative cash flow

**Use Case**: Understand if you're saving or spending more than you earn.

---

### 4. Savings Rate (Current Month)
**Description**: Percentage of income that is saved (not spent).

**Calculation**:
```sql
(net_cashflow / total_income) * 100
```

**Display**: Percentage (e.g., 30.5%)

**Use Case**: Track savings efficiency and financial health.

**Target**: Generally 20%+ is considered healthy.

---

### 5. Expense Categories Breakdown (Current Month)
**Description**: Detailed breakdown of spending by category with percentages.

**Calculation**:
```sql
SUM(amount) GROUP BY category
(amount / total_expenses) * 100 as percentage
```

**Display**: 
- Doughnut chart visualization
- List with category name, amount, and percentage

**Use Case**: Identify spending patterns and areas for cost reduction.

**Categories Include**:
- Groceries
- Dining Out
- Transportation
- Utilities
- Rent/Mortgage
- Entertainment
- Shopping
- Healthcare
- Education
- Travel
- Subscriptions
- Other

---

### 6. Monthly Trend Analysis (Last 12 Months)
**Description**: Historical trend of income, expenses, and cash flow over the past year.

**Calculation**:
```sql
Monthly aggregations from fact_monthly_summary
GROUP BY year, month
ORDER BY date DESC
LIMIT 12
```

**Display**: 
- Line chart showing income and expenses over time
- Bar chart comparing income vs expenses
- Cash flow trend line

**Use Case**: 
- Identify seasonal spending patterns
- Track financial progress over time
- Compare month-over-month performance

**Metrics Tracked**:
- Total Income per month
- Total Expenses per month
- Net Cash Flow per month
- Savings Rate per month

---

### 7. Budget vs Actual (Current Month)
**Description**: Comparison of actual spending against budgeted amounts or historical averages.

**Calculation**:
```sql
actual_spending - avg_monthly_spending as variance
((actual_spending - avg_monthly_spending) / avg_monthly_spending) * 100 as variance_percent
```

**Display**: 
- Variance amount and percentage
- Category-level comparisons
- Visual indicators for over/under budget

**Use Case**: 
- Monitor budget adherence
- Identify categories exceeding budget
- Plan future spending adjustments

**Note**: Full budget comparison requires budget data from RDS. Currently shows variance from historical average.

---

## Dashboard Visualizations

### KPI Cards
- 5 main KPI cards displayed at the top
- Real-time values with color coding
- Current month context

### Charts

1. **Monthly Trend Line Chart**
   - Shows income and expenses over 12 months
   - Dual-line visualization
   - Interactive tooltips

2. **Expense Categories Doughnut Chart**
   - Visual breakdown of spending by category
   - Color-coded segments
   - Percentage labels

3. **Income vs Expenses Bar Chart**
   - Side-by-side comparison
   - Monthly view
   - Easy to spot trends

4. **Cash Flow Trend Chart**
   - Net cash flow over time
   - Gradient fill
   - Positive/negative visualization

---

## Data Sources

### RDS MSSQL (Transactional)
- Real-time transaction data
- User accounts and categories
- Budget definitions

### Redshift (Analytical)
- Aggregated monthly summaries
- Pre-calculated KPIs
- Historical trend data
- Optimized for analytical queries

---

## Performance Considerations

### Query Optimization
- Monthly summaries pre-aggregated in `fact_monthly_summary`
- Date dimension table for efficient date filtering
- Distribution keys optimized for user-based queries
- Sort keys on date for time-series queries

### Caching Strategy
- Monthly summaries updated via ETL pipeline
- Real-time queries only for current month
- Historical data served from pre-aggregated tables

---

## API Endpoints

### Get All KPIs
```
GET /api/kpi/dashboard/{user_id}
```

Returns:
```json
{
  "user_id": 1,
  "current_month": "December",
  "kpi_metrics": {
    "total_income": 5000.00,
    "total_expenses": 3500.00,
    "net_cashflow": 1500.00,
    "savings_rate": 30.0,
    "transaction_count": 45
  },
  "category_breakdown": [...],
  "monthly_trend": [...],
  "budget_variance": null
}
```

### Individual Metric Endpoints
- `GET /api/kpi/income/{user_id}?months=12`
- `GET /api/kpi/expenses/{user_id}?months=12`
- `GET /api/kpi/cashflow/{user_id}?months=12`

---

## Customization

### Adding New KPIs
1. Add calculation to `database/kpi_queries.sql`
2. Update `backend/main.py` to include in API response
3. Add visualization to `frontend/index.html`

### Modifying Categories
1. Update categories in RDS MSSQL
2. Run ETL pipeline to sync to Redshift
3. Categories automatically appear in breakdown

### Changing Time Periods
- Modify `months` parameter in API calls
- Update date filters in SQL queries
- Adjust chart date ranges in frontend

---

## Best Practices

1. **Regular ETL Runs**: Schedule daily or hourly ETL to keep data fresh
2. **Data Quality**: Validate transactions before loading
3. **Performance Monitoring**: Track query performance in Redshift
4. **User Segmentation**: Consider user-specific KPI thresholds
5. **Historical Retention**: Maintain at least 2 years of historical data

---

## Future Enhancements

- [ ] Predictive analytics (forecasting)
- [ ] Anomaly detection (unusual spending patterns)
- [ ] Goal tracking (savings goals, budget goals)
- [ ] Multi-currency support
- [ ] Recurring transaction detection
- [ ] AI-powered spending insights
- [ ] Mobile app integration
- [ ] Email/SMS alerts for budget thresholds


