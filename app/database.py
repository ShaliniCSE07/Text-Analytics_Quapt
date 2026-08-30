import sqlite3
import os

DB_PATH = "data/reviews.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Customer_Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Customer_Reviews (
            Platform TEXT,
            Company TEXT,
            Product TEXT,
            Review TEXT,
            Month_Year TEXT,
            Platform_Reference_Id TEXT PRIMARY KEY,
            Load_timestamp TEXT
        )
    ''')
    
    # Create Customer_Reviews_Analysis table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Customer_Reviews_Analysis (
            Platform TEXT,
            Company TEXT,
            Product TEXT,
            Platform_Reference_Id TEXT PRIMARY KEY,
            Rating TEXT,
            Tags TEXT,
            Confidence INTEGER,
            Load_timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    
    # Verify tables
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables in the database:")
    for table in tables:
        print(f"- {table[0]}")
        
    conn.close()
