import os
import sys
import pandas as pd
from app.pipeline import analyze_review


def run_pipeline_on_file():
    # Determine base directory of the project
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "data", "sample_customer_reviews.csv")
    output_path = os.path.join(base_dir, "data", "analyzed_reviews_output.csv")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 1. Load data/sample_customer_reviews.csv using pandas
    df = pd.read_csv(input_path)

    # 2. Convert each row to a dict and call analyze_review()
    results = []
    for _, row in df.iterrows():
        row_dict = row.dropna().to_dict()
        if "Review" not in row_dict or pd.isna(row.get("Review")):
            row_dict["Review"] = ""
        analyzed_dict = analyze_review(row_dict)
        results.append(analyzed_dict)

    # 3. Collect all results into a new pandas DataFrame
    output_df = pd.DataFrame(results)

    # 4. Save that DataFrame to data/analyzed_reviews_output.csv
    output_df.to_csv(output_path, index=False)

    # 5. Calculate Summary Statistics
    total_rows = len(output_df)
    rating_counts = output_df["Rating"].value_counts().to_dict()
    uncategorised_count = (output_df["Tags"] == "Uncategorised").sum()

    # Print Summary
    print("=" * 60)
    print("PIPELINE PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total rows processed: {total_rows}")
    print("\nRating Counts:")
    rating_categories = ["Positive", "Negative", "Neutral", "language unsupported"]
    for category in rating_categories:
        count = rating_counts.get(category, 0)
        print(f"  - {category}: {count}")

    # Display any unexpected rating values if any exist
    for category, count in rating_counts.items():
        if category not in rating_categories:
            print(f"  - {category}: {count}")

    print(f"\nRows tagged as 'Uncategorised': {uncategorised_count}")
    print("=" * 60)

    # Print first 5 rows of output DataFrame
    print("\nFirst 5 rows of the output DataFrame:")
    print(output_df.head().to_string())
    print("\n" + "=" * 60)

    return output_df


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    run_pipeline_on_file()
