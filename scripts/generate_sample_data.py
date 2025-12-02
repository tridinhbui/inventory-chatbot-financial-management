"""
Generate sample data for testing the finance insight engine
Inserts sample users, accounts, categories, and transactions
"""

import os
import sys
import random
from datetime import datetime, timedelta
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def connect_rds():
    """Connect to RDS MSSQL"""
    try:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.getenv('RDS_HOST', 'localhost')};"
            f"DATABASE={os.getenv('RDS_DATABASE', 'finance_db')};"
            f"UID={os.getenv('RDS_USER', 'admin')};"
            f"PWD={os.getenv('RDS_PASSWORD', 'password')}"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Error connecting to RDS: {e}")
        sys.exit(1)

def generate_sample_data():
    """Generate comprehensive sample data"""
    conn = connect_rds()
    cursor = conn.cursor()
    
    try:
        # Create sample user
        print("Creating sample user...")
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'demo_user')
            INSERT INTO users (username, email) VALUES ('demo_user', 'demo@example.com')
        """)
        cursor.execute("SELECT user_id FROM users WHERE username = 'demo_user'")
        user_id = cursor.fetchone()[0]
        print(f"✅ Created user with ID: {user_id}")
        
        # Create sample account
        print("Creating sample account...")
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM accounts WHERE user_id = ? AND account_name = 'Primary Checking')
            INSERT INTO accounts (user_id, account_name, account_type, balance, currency)
            VALUES (?, 'Primary Checking', 'checking', 5000.00, 'USD')
        """, (user_id, user_id))
        cursor.execute("SELECT account_id FROM accounts WHERE user_id = ? AND account_name = 'Primary Checking'", (user_id,))
        account_id = cursor.fetchone()[0]
        print(f"✅ Created account with ID: {account_id}")
        
        # Create income categories
        print("Creating income categories...")
        income_categories = ['Salary', 'Freelance', 'Investment Returns', 'Other Income']
        income_category_ids = []
        for cat_name in income_categories:
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM categories WHERE user_id = ? AND category_name = ?)
                INSERT INTO categories (user_id, category_name, category_type)
                VALUES (?, ?, 'income')
            """, (user_id, cat_name, user_id, cat_name))
            cursor.execute("SELECT category_id FROM categories WHERE user_id = ? AND category_name = ?", (user_id, cat_name))
            income_category_ids.append(cursor.fetchone()[0])
        print(f"✅ Created {len(income_categories)} income categories")
        
        # Create expense categories
        print("Creating expense categories...")
        expense_categories = [
            'Groceries', 'Dining Out', 'Transportation', 'Utilities',
            'Rent/Mortgage', 'Entertainment', 'Shopping', 'Healthcare',
            'Education', 'Travel', 'Subscriptions', 'Other'
        ]
        expense_category_ids = []
        for cat_name in expense_categories:
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM categories WHERE user_id = ? AND category_name = ?)
                INSERT INTO categories (user_id, category_name, category_type)
                VALUES (?, ?, 'expense')
            """, (user_id, cat_name, user_id, cat_name))
            cursor.execute("SELECT category_id FROM categories WHERE user_id = ? AND category_name = ?", (user_id, cat_name))
            expense_category_ids.append(cursor.fetchone()[0])
        print(f"✅ Created {len(expense_categories)} expense categories")
        
        # Generate transactions for the last 3 months
        print("Generating sample transactions...")
        today = datetime.now()
        transactions_created = 0
        
        # Income transactions (2-4 per month)
        for month_offset in range(3):
            month_start = (today - timedelta(days=30 * month_offset)).replace(day=1)
            num_income = random.randint(2, 4)
            
            for _ in range(num_income):
                trans_date = month_start + timedelta(days=random.randint(1, 28))
                amount = random.uniform(1000, 5000) if random.random() > 0.5 else random.uniform(200, 800)
                category_id = random.choice(income_category_ids)
                
                cursor.execute("""
                    INSERT INTO transactions 
                    (user_id, account_id, category_id, transaction_date, amount, transaction_type, description)
                    VALUES (?, ?, ?, ?, ?, 'income', ?)
                """, (user_id, account_id, category_id, trans_date, amount, 
                      f"Salary payment - {trans_date.strftime('%B %Y')}"))
                transactions_created += 1
        
        # Expense transactions (15-30 per month)
        expense_descriptions = [
            'Grocery shopping', 'Restaurant dinner', 'Uber ride', 'Electric bill',
            'Netflix subscription', 'Coffee shop', 'Gas station', 'Pharmacy',
            'Online purchase', 'Movie tickets', 'Gym membership', 'Phone bill'
        ]
        
        for month_offset in range(3):
            month_start = (today - timedelta(days=30 * month_offset)).replace(day=1)
            num_expenses = random.randint(15, 30)
            
            for _ in range(num_expenses):
                trans_date = month_start + timedelta(days=random.randint(1, 28))
                amount = random.uniform(5, 500)
                category_id = random.choice(expense_category_ids)
                description = random.choice(expense_descriptions)
                
                cursor.execute("""
                    INSERT INTO transactions 
                    (user_id, account_id, category_id, transaction_date, amount, transaction_type, description)
                    VALUES (?, ?, ?, ?, ?, 'expense', ?)
                """, (user_id, account_id, category_id, trans_date, amount, description))
                transactions_created += 1
        
        conn.commit()
        print(f"✅ Created {transactions_created} sample transactions")
        print(f"\n🎉 Sample data generation complete!")
        print(f"   User ID: {user_id}")
        print(f"   Account ID: {account_id}")
        print(f"   Transactions: {transactions_created}")
        print(f"\n💡 Next steps:")
        print(f"   1. Run ETL pipeline: python etl/pipeline.py")
        print(f"   2. Start API: cd backend && python main.py")
        print(f"   3. Open dashboard: frontend/index.html")
        print(f"   4. Use User ID: {user_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error generating sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Personal Finance Insight Engine - Sample Data Generator")
    print("=" * 60)
    generate_sample_data()


