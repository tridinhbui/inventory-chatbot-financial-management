"""
FastAPI Backend for Personal Finance Insight Engine
Provides REST API endpoints for KPI dashboard data
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.csv_analyzer import CSVDataAnalyzer
from analytics.multi_user_analysis import MultiUserFinancialAnalyzer
from qa.validation_system import DashboardSpecValidator
from goals.goal_dashboard import GoalDashboard
from finbud.recommendation_engine import FinBudRecommendationEngine

load_dotenv()

app = FastAPI(title="Personal Finance Insight Engine API", version="2.0.0")

# Initialize services
csv_analyzer = CSVDataAnalyzer('retail_store_inventory.csv', 'Walmart.csv')
multi_user_analyzer = MultiUserFinancialAnalyzer()
spec_validator = DashboardSpecValidator()
goal_dashboard = GoalDashboard()
finbud_engine = FinBudRecommendationEngine()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database connection
def get_db_connection():
    """Get Redshift database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('REDSHIFT_HOST', 'localhost'),
            port=int(os.getenv('REDSHIFT_PORT', 5439)),
            database=os.getenv('REDSHIFT_DATABASE', 'dev'),
            user=os.getenv('REDSHIFT_USER', 'admin'),
            password=os.getenv('REDSHIFT_PASSWORD', 'password')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


# Pydantic models
class KPIMetrics(BaseModel):
    total_income: float
    total_expenses: float
    net_cashflow: float
    savings_rate: float
    transaction_count: int


class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float
    transaction_count: int


class MonthlyTrend(BaseModel):
    year: int
    month: int
    month_name: str
    income: float
    expenses: float
    cashflow: float
    savings_rate: float


class DashboardResponse(BaseModel):
    user_id: int
    current_month: str
    kpi_metrics: KPIMetrics
    category_breakdown: List[CategoryBreakdown]
    monthly_trend: List[MonthlyTrend]
    budget_variance: Optional[Dict] = None


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Personal Finance Insight Engine API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/api/kpi/dashboard/{user_id}", response_model=DashboardResponse)
async def get_dashboard(user_id: int):
    """
    Get comprehensive dashboard data with all 7 KPIs
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # KPI 1-4: Core Metrics (Current Month)
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as total_expenses,
                SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE -amount END) as net_cashflow,
                COUNT(*) as transaction_count
            FROM fact_transactions
            WHERE user_id = %s
                AND date_key >= (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE))
                AND date_key < (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
        """, (user_id,))
        
        core_metrics = cursor.fetchone()
        total_income = float(core_metrics['total_income'] or 0)
        total_expenses = float(core_metrics['total_expenses'] or 0)
        net_cashflow = float(core_metrics['net_cashflow'] or 0)
        transaction_count = int(core_metrics['transaction_count'] or 0)
        savings_rate = (net_cashflow / total_income * 100) if total_income > 0 else 0
        
        # KPI 5: Category Breakdown
        cursor.execute("""
            SELECT 
                dc.category_name as category,
                SUM(ft.amount) as amount,
                COUNT(*) as transaction_count,
                (SUM(ft.amount) * 100.0 / NULLIF(
                    (SELECT SUM(amount) FROM fact_transactions 
                     WHERE user_id = %s AND transaction_type = 'expense'
                     AND date_key >= (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE))
                     AND date_key < (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')),
                    0
                )) as percentage
            FROM fact_transactions ft
            JOIN dim_category dc ON ft.category_id = dc.category_id
            WHERE ft.user_id = %s
                AND ft.transaction_type = 'expense'
                AND ft.date_key >= (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE))
                AND ft.date_key < (SELECT date_key FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')
            GROUP BY dc.category_name
            ORDER BY amount DESC
        """, (user_id, user_id))
        
        category_breakdown = [
            CategoryBreakdown(
                category=row['category'],
                amount=float(row['amount']),
                percentage=float(row['percentage'] or 0),
                transaction_count=int(row['transaction_count'])
            )
            for row in cursor.fetchall()
        ]
        
        # KPI 6: Monthly Trend (Last 12 Months)
        cursor.execute("""
            SELECT 
                year,
                month,
                month_name,
                total_income as income,
                total_expenses as expenses,
                net_cashflow as cashflow,
                CASE 
                    WHEN total_income > 0 
                    THEN (net_cashflow / total_income) * 100 
                    ELSE 0 
                END as savings_rate
            FROM fact_monthly_summary
            WHERE user_id = %s
                AND date_key >= (SELECT date_key FROM dim_date WHERE date_value >= DATEADD(month, -12, CURRENT_DATE::DATE))
            ORDER BY year DESC, month DESC
        """, (user_id,))
        
        monthly_trend = [
            MonthlyTrend(
                year=int(row['year']),
                month=int(row['month']),
                month_name=row['month_name'],
                income=float(row['income'] or 0),
                expenses=float(row['expenses'] or 0),
                cashflow=float(row['cashflow'] or 0),
                savings_rate=float(row['savings_rate'] or 0)
            )
            for row in cursor.fetchall()
        ]
        
        # Get current month name
        cursor.execute("SELECT month_name FROM dim_date WHERE date_value = DATE_TRUNC('month', CURRENT_DATE) LIMIT 1")
        current_month_row = cursor.fetchone()
        current_month = current_month_row['month_name'] if current_month_row else datetime.now().strftime('%B')
        
        return DashboardResponse(
            user_id=user_id,
            current_month=current_month,
            kpi_metrics=KPIMetrics(
                total_income=total_income,
                total_expenses=total_expenses,
                net_cashflow=net_cashflow,
                savings_rate=savings_rate,
                transaction_count=transaction_count
            ),
            category_breakdown=category_breakdown,
            monthly_trend=monthly_trend,
            budget_variance=None  # Placeholder for budget comparison
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.get("/api/kpi/income/{user_id}")
async def get_income_metrics(user_id: int, months: int = 12):
    """Get income metrics over time"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                dd.year,
                dd.month,
                dd.month_name,
                SUM(ft.amount) as total_income,
                COUNT(*) as transaction_count,
                AVG(ft.amount) as avg_transaction
            FROM fact_transactions ft
            JOIN dim_date dd ON ft.date_key = dd.date_key
            WHERE ft.user_id = %s
                AND ft.transaction_type = 'income'
                AND dd.date_value >= DATEADD(month, -%s, CURRENT_DATE::DATE)
            GROUP BY dd.year, dd.month, dd.month_name
            ORDER BY dd.year DESC, dd.month DESC
        """, (user_id, months))
        
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/api/kpi/expenses/{user_id}")
async def get_expense_metrics(user_id: int, months: int = 12):
    """Get expense metrics over time"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                dd.year,
                dd.month,
                dd.month_name,
                SUM(ft.amount) as total_expenses,
                COUNT(*) as transaction_count,
                AVG(ft.amount) as avg_transaction
            FROM fact_transactions ft
            JOIN dim_date dd ON ft.date_key = dd.date_key
            WHERE ft.user_id = %s
                AND ft.transaction_type = 'expense'
                AND dd.date_value >= DATEADD(month, -%s, CURRENT_DATE::DATE)
            GROUP BY dd.year, dd.month, dd.month_name
            ORDER BY dd.year DESC, dd.month DESC
        """, (user_id, months))
        
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/api/kpi/cashflow/{user_id}")
async def get_cashflow_metrics(user_id: int, months: int = 12):
    """Get cashflow metrics over time"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                year,
                month,
                month_name,
                total_income,
                total_expenses,
                net_cashflow,
                savings_rate
            FROM vw_kpi_dashboard
            WHERE user_id = %s
                AND date_value >= DATEADD(month, -%s, CURRENT_DATE::DATE)
            ORDER BY year DESC, month DESC
        """, (user_id, months))
        
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# New API Endpoints for Enhanced Features

@app.get("/api/analytics/csv-insights")
async def get_csv_insights():
    """Get insights from CSV data analysis"""
    try:
        if csv_analyzer.inventory_df is None:
            csv_analyzer.load_data()
        insights = csv_analyzer.generate_financial_insights()
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/multi-user/{user_id}")
async def get_multi_user_analysis(user_id: int):
    """Get multi-user financial behavior analysis"""
    try:
        # This would typically load from database
        # For now, return sample analysis
        volatility = multi_user_analyzer.analyze_cashflow_volatility(user_id)
        spikes = multi_user_analyzer.detect_expense_spikes(user_id)
        risks = multi_user_analyzer.identify_risk_patterns(user_id)
        
        return {
            'user_id': user_id,
            'volatility': volatility,
            'spikes': spikes,
            'risks': risks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/qa/validate-spec")
async def validate_dashboard_spec(spec: Dict):
    """Validate chatbot-generated dashboard specification"""
    try:
        result = spec_validator.validate_spec(spec)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/qa/validation-report")
async def get_validation_report():
    """Get QA validation report"""
    try:
        report = spec_validator.generate_validation_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/goals/dashboard/{user_id}")
async def get_goal_dashboard(user_id: int):
    """Get goal dashboard with SLA tracking"""
    try:
        dashboard = goal_dashboard.get_goal_dashboard(user_id)
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/goals/create")
async def create_goal(goal_data: Dict):
    """Create a new financial goal"""
    try:
        goal = goal_dashboard.create_goal(
            user_id=goal_data['user_id'],
            goal_name=goal_data['goal_name'],
            goal_type=goal_data['goal_type'],
            target_amount=goal_data['target_amount'],
            end_date=datetime.fromisoformat(goal_data['end_date'])
        )
        return {"goal_id": goal.goal_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/goals/adoption-metrics")
async def get_adoption_metrics():
    """Get adoption metrics"""
    try:
        metrics = goal_dashboard.get_adoption_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/finbud/recommendations/{user_id}")
async def get_finbud_recommendations(user_id: int):
    """Get FinBud recommendations for user"""
    try:
        # Get financial data and behavior analysis
        # This would typically come from database
        financial_data = {
            'savings_rate': 15.5,
            'category_breakdown': []
        }
        behavior_analysis = {
            'volatility': {'volatility_level': 'medium'},
            'spikes': {'spike_count': 0},
            'risks': {'risk_level': 'low', 'risk_factors': []}
        }
        
        recommendations = finbud_engine.generate_recommendations(
            user_id, financial_data, behavior_analysis
        )
        summary = finbud_engine.get_recommendation_summary(user_id)
        
        return {
            'user_id': user_id,
            'recommendations': recommendations,
            'summary': summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

