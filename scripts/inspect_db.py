import sqlite3
import pandas as pd
import os

db_path = 'data/winner_data.sqlite'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit()

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    for table in tables:
        table_name = table[0]
        print(f"\n--- Table: {table_name} ---")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        print(f"Columns: {col_names}")
        
        # Try to select the first 5 rows to see data samples
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
        print(df.to_string())
        
        if 'league' in col_names:
            print("\nDistinct Leagues:")
            distinct_leagues = pd.read_sql_query(f"SELECT DISTINCT league FROM {table_name}", conn)
            print(distinct_leagues.to_string())
            
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn: conn.close()
