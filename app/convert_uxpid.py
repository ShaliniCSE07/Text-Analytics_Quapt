import json
import os
import pandas as pd

JSON_DIR = "data/UXPID/jsons"
OUTPUT_CSV = "data/real_datasets/manufacturing.csv"

data = []

# Loop through all JSON files in the folder
for filename in os.listdir(JSON_DIR):
    if filename.endswith(".json"):
        filepath = os.path.join(JSON_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                record = json.load(f)
            
            # Get the sentiment for the branch
            sentiment = record.get("analysis", {}).get("overall_branch_sentiment", "").lower()
            
            # Only keep positive, negative, neutral
            if sentiment not in ["positive", "negative", "neutral"]:
                continue
                
            # Loop through comments and extract text
            for comment in record.get("content", []):
                text = comment.get("comment_body", "").strip()
                if text:
                    data.append({"text": text, "label": sentiment})
                    
        except Exception as e:
            print(f"Error reading {filename}: {e}")

# Save to CSV
df = pd.DataFrame(data)
df.to_csv(OUTPUT_CSV, index=False)
print(f"Extracted {len(df)} comments and saved to {OUTPUT_CSV}")
print(df['label'].value_counts())