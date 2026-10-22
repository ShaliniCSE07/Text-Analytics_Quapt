import sqlite3
import os
import csv

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
            Load_timestamp TEXT,
            Emotion TEXT,
            Emotion_Confidence INTEGER,
            Emotion_Scores TEXT,
            Emotion_Model TEXT
        )
    ''')

    # Create Review_Corrections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Review_Corrections (
            Correction_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Platform_Reference_Id TEXT,
            Review_Text TEXT,
            Original_Rating TEXT,
            Corrected_Rating TEXT,
            Original_Tags TEXT,
            Corrected_Tags TEXT,
            Corrected_By TEXT,
            Corrected_At TEXT,
            Approved_For_Learning INTEGER DEFAULT 1
        )
    ''')
    
    # Backward-compatible migration: add emotion and learning columns if missing
    cursor.execute("PRAGMA table_info(Customer_Reviews_Analysis)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    new_cols = [
        ("Emotion", "TEXT"),
        ("Emotion_Confidence", "INTEGER"),
        ("Emotion_Scores", "TEXT"),
        ("Emotion_Model", "TEXT"),
        ("Label_Source", "TEXT DEFAULT 'model'"),
        ("Model_Rating", "TEXT"),
        ("Learned_From", "TEXT"),
        ("Learned_Similarity", "INTEGER")
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE Customer_Reviews_Analysis ADD COLUMN {col_name} {col_type}")
            
    conn.commit()

    # Ensure existing rows have Label_Source defaulted
    cursor.execute("UPDATE Customer_Reviews_Analysis SET Label_Source = 'model' WHERE Label_Source IS NULL")

    # Backfill Model_Rating:
    # For Label_Source='model' rows copy Rating
    cursor.execute("""
        UPDATE Customer_Reviews_Analysis 
        SET Model_Rating = Rating 
        WHERE Label_Source = 'model' AND (Model_Rating IS NULL OR Model_Rating = '')
    """)

    # For 'human' rows use Original_Rating from the earliest Review_Corrections row (NULL if unknown)
    cursor.execute("""
        UPDATE Customer_Reviews_Analysis 
        SET Model_Rating = (
            SELECT Original_Rating FROM Review_Corrections 
            WHERE Review_Corrections.Platform_Reference_Id = Customer_Reviews_Analysis.Platform_Reference_Id 
              AND Original_Rating IS NOT NULL 
            ORDER BY Correction_Id ASC LIMIT 1
        ) 
        WHERE Label_Source = 'human' AND (Model_Rating IS NULL OR Model_Rating = '')
    """)

    # Backfill from corrections_log.csv if present
    log_path = os.path.join(os.path.dirname(DB_PATH), "corrections_log.csv")
    if os.path.exists(log_path):
        with open(log_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                pid = row.get('Platform_Reference_Id')
                if pid:
                    cursor.execute(
                        "UPDATE Customer_Reviews_Analysis SET Label_Source = 'human' WHERE Platform_Reference_Id = ?",
                        (pid,)
                    )
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
