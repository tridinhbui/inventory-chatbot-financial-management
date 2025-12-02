# Quick Start Guide

Get your Personal Finance Insight Engine up and running in 5 minutes!

## Prerequisites Check

- [ ] Python 3.8+ installed
- [ ] Access to Amazon RDS MSSQL instance
- [ ] Access to Amazon Redshift cluster
- [ ] ODBC Driver 17 for SQL Server installed

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Copy the example
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

Fill in your database credentials:
```env
RDS_HOST=your-rds-endpoint.region.rds.amazonaws.com
RDS_DATABASE=finance_db
RDS_USER=admin
RDS_PASSWORD=your-secure-password

REDSHIFT_HOST=your-cluster.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_DATABASE=dev
REDSHIFT_USER=admin
REDSHIFT_PASSWORD=your-secure-password
```

### 3. Setup RDS MSSQL Database

Connect to your RDS MSSQL instance and run:

```bash
# Using sqlcmd or your preferred SQL client
sqlcmd -S your-rds-endpoint -U admin -P your-password -d master -i database/rds_mssql_schema.sql
```

Or execute `database/rds_mssql_schema.sql` in SQL Server Management Studio.

### 4. Setup Redshift Database

```bash
python scripts/setup_database.py
```

This will:
- Create all Redshift tables
- Initialize the date dimension table
- Set up the analytical schema

### 5. Generate Sample Data (Optional)

```bash
python scripts/generate_sample_data.py
```

This creates:
- A demo user
- Sample accounts and categories
- 3 months of transaction history

### 6. Run ETL Pipeline

```bash
python etl/pipeline.py
```

This transfers data from RDS to Redshift and creates aggregations.

### 7. Start the Backend API

```bash
cd backend
python main.py
```

Or with uvicorn:
```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`

### 8. Open the Dashboard

**Option A: Direct file**
- Open `frontend/index.html` in your browser

**Option B: Local server**
```bash
cd frontend
python -m http.server 8080
# Navigate to http://localhost:8080
```

### 9. View Your Dashboard

1. Enter your User ID (default: 1 if you used sample data)
2. Click "Load Dashboard"
3. Explore the 7 KPIs and visualizations!

## Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Dashboard Data
```bash
curl http://localhost:8000/api/kpi/dashboard/1
```

### View API Documentation
Open `http://localhost:8000/docs` in your browser for interactive API documentation.

## Troubleshooting

### Connection Issues

**RDS Connection Failed**
- Verify your RDS endpoint and credentials
- Check security group allows your IP
- Ensure ODBC Driver 17 is installed

**Redshift Connection Failed**
- Verify cluster endpoint and credentials
- Check VPC security group settings
- Ensure cluster is publicly accessible (or use VPN)

### Data Not Showing

1. **Check ETL ran successfully**
   ```bash
   python etl/pipeline.py
   ```

2. **Verify sample data exists**
   ```bash
   python scripts/generate_sample_data.py
   ```

3. **Check date dimension is populated**
   - Query Redshift: `SELECT COUNT(*) FROM dim_date;`
   - Should return thousands of rows

### Dashboard Not Loading

1. **Check API is running**
   - Visit `http://localhost:8000/health`

2. **Check CORS settings**
   - If serving from different port, update CORS in `backend/main.py`

3. **Check browser console**
   - Open Developer Tools (F12)
   - Look for JavaScript errors

## Next Steps

- **Customize Categories**: Add your own expense/income categories
- **Add Real Data**: Import your actual financial transactions
- **Schedule ETL**: Set up automated ETL runs (AWS Lambda, cron, etc.)
- **Enhance Visualizations**: Customize charts in `frontend/index.html`
- **Add Budgets**: Implement budget tracking features

## Architecture Overview

```
RDS MSSQL (Transactional)
    ↓ ETL Pipeline
Redshift (Analytical)
    ↓ FastAPI Backend
Frontend Dashboard
```

## Support

For issues or questions:
1. Check the main README.md
2. Review error messages in console/logs
3. Verify database connections
4. Check API documentation at `/docs`

Happy analyzing! 📊💰


