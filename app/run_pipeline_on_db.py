import sqlite3
import pandas as pd
from datetime import datetime
from app.pipeline import analyze_review

def run_pipeline():
    db_path = "data/reviews.db"
    
    conn = sqlite3.connect(db_path)
    
    # 3. Read all rows from Customer_Reviews into a DataFrame
    reviews_df = pd.read_sql_query("SELECT * FROM Customer_Reviews", conn)
    total_rows = len(reviews_df)
    
    # 4. Read all existing Platform_Reference_Id values from Customer_Reviews_Analysis
    cursor = conn.cursor()
    cursor.execute("SELECT Platform_Reference_Id FROM Customer_Reviews_Analysis")
    existing_ids = {row[0] for row in cursor.fetchall()}
    
    newly_analyzed = 0
    skipped = 0
    
    # 5. Process each row
    for _, row in reviews_df.iterrows():
        ref_id = row['Platform_Reference_Id']
        
        if ref_id in existing_ids:
            skipped += 1
            continue
            
        # Convert row to dict
        row_dict = row.to_dict()
        
        # Call analyze_review
        result = analyze_review(row_dict)
        
        # Insert result into Customer_Reviews_Analysis
        # Tags from analyze_review is usually a string, if it's a list we'd need to join it.
        # Based on earlier code and usual behavior, we assume result['Tags'] is a string.
        # But let's check or handle if it's a list.
        tags = result.get('Tags', '')
        if isinstance(tags, list):
            tags = ", ".join(tags)
            
        cursor.execute('''
            INSERT INTO Customer_Reviews_Analysis 
            (Platform, Company, Product, Platform_Reference_Id, Rating, Tags, Confidence, Load_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.get('Platform', ''),
            result.get('Company', ''),
            result.get('Product', ''),
            result.get('Platform_Reference_Id', ref_id),
            result.get('Rating', ''),
            tags,
            result.get('Confidence', 100),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        newly_analyzed += 1
        
    # 6. Commit changes and close connection
    conn.commit()
    conn.close()
    
    # 7. Print summary
    print("Summary:")
    print(f"Total rows in Customer_Reviews: {total_rows}")
    print(f"Rows newly analyzed this run: {newly_analyzed}")
    print(f"Rows skipped because already analyzed: {skipped}")

if __name__ == "__main__":
    run_pipeline()
