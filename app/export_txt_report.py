import os
import sys
import pandas as pd
from app.pipeline import analyze_review


def generate_txt_report():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "data", "sample_customer_reviews.csv")
    output_path = os.path.join(base_dir, "data", "analyzed_reviews_results.txt")

    if not os.path.exists(input_path):
        input_path = "data/sample_customer_reviews.csv"
        output_path = "data/analyzed_reviews_results.txt"

    df = pd.read_csv(input_path)

    results = []
    for _, row in df.iterrows():
        row_dict = row.dropna().to_dict()
        if "Review" not in row_dict or pd.isna(row.get("Review")):
            row_dict["Review"] = ""
        analyzed = analyze_review(row_dict)
        results.append(analyzed)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CUSTOMER REVIEWS ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")

        for idx, r in enumerate(results, 1):
            f.write(f"[Review {idx}]\n")
            f.write(f"- Company             : {r.get('Company', 'N/A')}\n")
            f.write(f"- Platform            : {r.get('Platform', 'N/A')}\n")
            f.write(f"- Product             : {r.get('Product', 'N/A')}\n")
            f.write(f"- Month / Year        : {r.get('Month_Year', 'N/A')}\n")
            f.write(f"- Platform Ref ID     : {r.get('Platform_Reference_Id', 'N/A')}\n")
            f.write(f"- Load Timestamp      : {r.get('Load_timestamp', 'N/A')}\n")
            f.write(f"- Review Text         : \"{r.get('Review', '')}\"\n")
            f.write(f"- Predicted Sentiment : {r.get('Rating', 'N/A')}\n")
            f.write(f"- Confidence          : {r.get('Confidence', 0)}%\n")
            f.write(f"- Topic Tags          : {r.get('Tags', 'None')}\n")
            f.write("-" * 80 + "\n\n")

    print(f"Report successfully saved to: {output_path}\n")
    with open(output_path, "r", encoding="utf-8") as f:
        print(f.read())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    generate_txt_report()
