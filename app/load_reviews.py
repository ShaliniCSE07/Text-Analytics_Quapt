import sqlite3
import pandas as pd
import os

def load_reviews():
    csv_path = "data/raw_reviews_dataset.csv"
    db_path = "data/reviews.db"
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    df = pd.read_csv(csv_path)
    # Handle NaNs which pandas might introduce for empty strings
    df = df.fillna('')
    
    total_rows = len(df)
    inserted = 0
    skipped = 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO Customer_Reviews 
                (Platform, Company, Product, Review, Month_Year, Platform_Reference_Id, Load_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['Platform'],
                row['Company'],
                row['Product'],
                row['Review'],
                row['Month_Year'],
                row['Platform_Reference_Id'],
                row['Load_timestamp']
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
            
    conn.commit()
    conn.close()
    
    print("Summary:")
    print(f"Total rows in file: {total_rows}")
    print(f"Rows successfully inserted: {inserted}")
    print(f"Rows skipped as duplicates: {skipped}")

if __name__ == "__main__":
    load_reviews()
