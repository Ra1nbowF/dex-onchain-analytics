"""
Script to create all tables in Railway PostgreSQL database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Database connection parameters
DATABASE_URL = "postgresql://postgres:kPviLOMOWTUlSEruerigidRXQYQYROWp@metro.proxy.rlwy.net:54031/railway"

def create_all_tables():
    """
    Execute the complete table creation script
    """
    # Read the SQL file
    with open('create_all_tables_for_railway.sql', 'r', encoding='utf-8') as file:
        sql_script = file.read()
    
    # Connect to the database
    try:
        print("Connecting to Railway database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Executing table creation script...")
        # Execute the script
        cur.execute(sql_script)
        
        # Commit the changes
        conn.commit()
        
        print("All tables created successfully!")
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    create_all_tables()