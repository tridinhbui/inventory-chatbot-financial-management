"""
Database setup script
Initializes date dimension and creates necessary tables
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def setup_redshift():
    """Setup Redshift database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('REDSHIFT_HOST', 'localhost'),
            port=int(os.getenv('REDSHIFT_PORT', 5439)),
            database=os.getenv('REDSHIFT_DATABASE', 'dev'),
            user=os.getenv('REDSHIFT_USER', 'admin'),
            password=os.getenv('REDSHIFT_PASSWORD', 'password')
        )
        
        cursor = conn.cursor()
        
        # Read and execute schema file
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'redshift_schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema (split by GO statements if present)
        statements = [s.strip() for s in schema_sql.split('GO') if s.strip()]
        for statement in statements:
            cursor.execute(statement)
        
        conn.commit()
        
        # Initialize date dimension
        date_dim_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'init_date_dimension.sql')
        with open(date_dim_path, 'r') as f:
            date_dim_sql = f.read()
        
        cursor.execute(date_dim_sql)
        conn.commit()
        
        print("✅ Redshift database setup completed successfully!")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error setting up Redshift: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Setting up Redshift database...")
    setup_redshift()


