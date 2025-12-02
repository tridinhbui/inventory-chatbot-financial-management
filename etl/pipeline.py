"""
ETL Pipeline for transferring data from RDS MSSQL to Redshift
Handles incremental data loads and dimension table updates
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import pyodbc
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """ETL Pipeline for RDS MSSQL to Redshift"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.rds_conn = None
        self.redshift_conn = None
        
    def connect_rds(self):
        """Establish connection to RDS MSSQL"""
        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.config['rds']['host']};"
                f"DATABASE={self.config['rds']['database']};"
                f"UID={self.config['rds']['user']};"
                f"PWD={self.config['rds']['password']}"
            )
            self.rds_conn = pyodbc.connect(conn_str)
            logger.info("Connected to RDS MSSQL")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RDS: {e}")
            return False
    
    def connect_redshift(self):
        """Establish connection to Redshift"""
        try:
            self.redshift_conn = psycopg2.connect(
                host=self.config['redshift']['host'],
                port=self.config['redshift']['port'],
                database=self.config['redshift']['database'],
                user=self.config['redshift']['user'],
                password=self.config['redshift']['password']
            )
            logger.info("Connected to Redshift")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redshift: {e}")
            return False
    
    def extract_transactions(self, last_sync_date: Optional[datetime] = None) -> pd.DataFrame:
        """Extract transactions from RDS MSSQL"""
        query = """
        SELECT 
            t.transaction_id,
            t.user_id,
            t.account_id,
            t.category_id,
            t.transaction_date,
            t.amount,
            t.transaction_type,
            t.description,
            t.merchant_name,
            t.payment_method,
            t.created_at
        FROM transactions t
        """
        
        if last_sync_date:
            query += f" WHERE t.created_at >= '{last_sync_date}' OR t.updated_at >= '{last_sync_date}'"
        
        query += " ORDER BY t.transaction_id"
        
        try:
            df = pd.read_sql(query, self.rds_conn)
            logger.info(f"Extracted {len(df)} transactions")
            return df
        except Exception as e:
            logger.error(f"Error extracting transactions: {e}")
            return pd.DataFrame()
    
    def extract_dimensions(self) -> Dict[str, pd.DataFrame]:
        """Extract dimension tables from RDS"""
        dimensions = {}
        
        try:
            dimensions['users'] = pd.read_sql("SELECT * FROM users", self.rds_conn)
            dimensions['accounts'] = pd.read_sql("SELECT * FROM accounts", self.rds_conn)
            dimensions['categories'] = pd.read_sql("SELECT * FROM categories", self.rds_conn)
            logger.info("Extracted dimension tables")
        except Exception as e:
            logger.error(f"Error extracting dimensions: {e}")
        
        return dimensions
    
    def transform_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform transaction data for Redshift"""
        if df.empty:
            return df
        
        # Add date_key
        df['date_key'] = df['transaction_date'].apply(
            lambda x: int(x.strftime('%Y%m%d')) if pd.notna(x) else None
        )
        
        # Ensure data types
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['transaction_id'] = df['transaction_id'].astype('int64')
        df['user_id'] = df['user_id'].astype('int32')
        
        # Fill nulls
        df = df.fillna({
            'description': '',
            'merchant_name': '',
            'payment_method': ''
        })
        
        return df
    
    def load_to_redshift(self, df: pd.DataFrame, table_name: str, mode: str = 'append'):
        """Load data to Redshift using COPY command or INSERT"""
        if df.empty:
            logger.warning(f"No data to load to {table_name}")
            return
        
        cursor = self.redshift_conn.cursor()
        
        try:
            if mode == 'replace':
                cursor.execute(f"TRUNCATE TABLE {table_name}")
            
            # Prepare data for insertion
            columns = list(df.columns)
            values = [tuple(row) for row in df[columns].values]
            
            # Use execute_values for efficient bulk insert
            insert_query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES %s
            """
            
            execute_values(cursor, insert_query, values)
            self.redshift_conn.commit()
            logger.info(f"Loaded {len(df)} rows to {table_name}")
            
        except Exception as e:
            self.redshift_conn.rollback()
            logger.error(f"Error loading to {table_name}: {e}")
            raise
        finally:
            cursor.close()
    
    def update_dimensions(self, dimensions: Dict[str, pd.DataFrame]):
        """Update dimension tables in Redshift"""
        for table_name, df in dimensions.items():
            if df.empty:
                continue
            
            redshift_table = f"dim_{table_name}" if table_name != 'users' else "dim_user"
            
            # Map column names if needed
            if table_name == 'users':
                df_redshift = df.rename(columns={
                    'user_id': 'user_id',
                    'username': 'username',
                    'email': 'email',
                    'created_at': 'created_at'
                })
            elif table_name == 'accounts':
                df_redshift = df.rename(columns={
                    'account_id': 'account_id',
                    'user_id': 'user_id',
                    'account_name': 'account_name',
                    'account_type': 'account_type',
                    'currency': 'currency'
                })
            elif table_name == 'categories':
                df_redshift = df.rename(columns={
                    'category_id': 'category_id',
                    'user_id': 'user_id',
                    'category_name': 'category_name',
                    'category_type': 'category_type',
                    'parent_category_id': 'parent_category_id'
                })
            else:
                df_redshift = df
            
            self.load_to_redshift(df_redshift, redshift_table, mode='replace')
    
    def update_monthly_summary(self):
        """Update monthly summary aggregations"""
        cursor = self.redshift_conn.cursor()
        
        try:
            # Delete existing summaries for recent months
            delete_query = """
            DELETE FROM fact_monthly_summary
            WHERE date_key >= (
                SELECT date_key FROM dim_date 
                WHERE date_value >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '3 months')
            )
            """
            cursor.execute(delete_query)
            
            # Insert new summaries
            insert_query = """
            INSERT INTO fact_monthly_summary (
                user_id, year, month, date_key,
                total_income, total_expenses, net_cashflow,
                transaction_count, avg_transaction_amount
            )
            SELECT 
                ft.user_id,
                dd.year,
                dd.month,
                dd.date_key,
                SUM(CASE WHEN ft.transaction_type = 'income' THEN ft.amount ELSE 0 END) as total_income,
                SUM(CASE WHEN ft.transaction_type = 'expense' THEN ft.amount ELSE 0 END) as total_expenses,
                SUM(CASE WHEN ft.transaction_type = 'income' THEN ft.amount ELSE -ft.amount END) as net_cashflow,
                COUNT(*) as transaction_count,
                AVG(ft.amount) as avg_transaction_amount
            FROM fact_transactions ft
            JOIN dim_date dd ON ft.date_key = dd.date_key
            WHERE dd.date_value >= DATEADD(month, -3, DATE_TRUNC('month', CURRENT_DATE)::DATE)
            GROUP BY ft.user_id, dd.year, dd.month, dd.date_key
            ON CONFLICT (user_id, year, month) 
            DO UPDATE SET
                total_income = EXCLUDED.total_income,
                total_expenses = EXCLUDED.total_expenses,
                net_cashflow = EXCLUDED.net_cashflow,
                transaction_count = EXCLUDED.transaction_count,
                avg_transaction_amount = EXCLUDED.avg_transaction_amount,
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(insert_query)
            self.redshift_conn.commit()
            logger.info("Updated monthly summary")
            
        except Exception as e:
            self.redshift_conn.rollback()
            logger.error(f"Error updating monthly summary: {e}")
            raise
        finally:
            cursor.close()
    
    def run_full_load(self):
        """Run full ETL pipeline"""
        logger.info("Starting full ETL pipeline")
        
        if not self.connect_rds():
            return False
        if not self.connect_redshift():
            return False
        
        try:
            # Extract dimensions
            dimensions = self.extract_dimensions()
            self.update_dimensions(dimensions)
            
            # Extract and load transactions
            transactions_df = self.extract_transactions()
            if not transactions_df.empty:
                transformed_df = self.transform_transactions(transactions_df)
                self.load_to_redshift(transformed_df, 'fact_transactions', mode='append')
            
            # Update aggregations
            self.update_monthly_summary()
            
            logger.info("ETL pipeline completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            return False
        finally:
            if self.rds_conn:
                self.rds_conn.close()
            if self.redshift_conn:
                self.redshift_conn.close()
    
    def run_incremental_load(self, last_sync_date: datetime):
        """Run incremental ETL pipeline"""
        logger.info(f"Starting incremental ETL pipeline from {last_sync_date}")
        
        if not self.connect_rds():
            return False
        if not self.connect_redshift():
            return False
        
        try:
            # Extract new/updated transactions
            transactions_df = self.extract_transactions(last_sync_date)
            if not transactions_df.empty:
                transformed_df = self.transform_transactions(transactions_df)
                self.load_to_redshift(transformed_df, 'fact_transactions', mode='append')
            
            # Update aggregations
            self.update_monthly_summary()
            
            logger.info("Incremental ETL pipeline completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Incremental ETL pipeline failed: {e}")
            return False
        finally:
            if self.rds_conn:
                self.rds_conn.close()
            if self.redshift_conn:
                self.redshift_conn.close()


if __name__ == "__main__":
    # Example configuration
    config = {
        'rds': {
            'host': os.getenv('RDS_HOST', 'localhost'),
            'database': os.getenv('RDS_DATABASE', 'finance_db'),
            'user': os.getenv('RDS_USER', 'admin'),
            'password': os.getenv('RDS_PASSWORD', 'password')
        },
        'redshift': {
            'host': os.getenv('REDSHIFT_HOST', 'localhost'),
            'port': int(os.getenv('REDSHIFT_PORT', 5439)),
            'database': os.getenv('REDSHIFT_DATABASE', 'dev'),
            'user': os.getenv('REDSHIFT_USER', 'admin'),
            'password': os.getenv('REDSHIFT_PASSWORD', 'password')
        }
    }
    
    pipeline = ETLPipeline(config)
    pipeline.run_full_load()

