import os
import sys

# Ensure project root directory is in sys.path for direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from app.sentiment import predict_sentiment_v2


def evaluate_sentiment_model():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "data", "labeled_validation_set.csv")

    if not os.path.exists(input_path):
        input_path = "data/labeled_validation_set.csv"

    # 1. Load data/labeled_validation_set.csv using pandas
    df = pd.read_csv(input_path)

    predicted_labels = []
    confidences = []

    # 2. Run predict_sentiment_v2 on each Review
    for review in df["Review"]:
        text = str(review) if pd.notna(review) else ""
        result = predict_sentiment_v2(text)
        predicted_labels.append(result.get("label", "Neutral"))
        confidences.append(result.get("confidence", 0))

    df["Predicted_Label"] = predicted_labels
    df["Confidence"] = confidences

    true_labels = df["True_Label"].tolist()

    # 3 & 4. Compute metrics using sklearn.metrics
    accuracy = accuracy_score(true_labels, predicted_labels)
    acc_percentage = accuracy * 100

    labels = sorted(list(set(true_labels) | set(predicted_labels)))
    report = classification_report(true_labels, predicted_labels, labels=labels, zero_division=0)
    cm = confusion_matrix(true_labels, predicted_labels, labels=labels)
    cm_df = pd.DataFrame(cm, index=[f"True: {l}" for l in labels], columns=[f"Pred: {l}" for l in labels])

    # 5. Mismatched rows table
    mismatch_df = df[df["True_Label"] != df["Predicted_Label"]][
        ["Review", "True_Label", "Predicted_Label", "Confidence"]
    ]

    # Print Summary
    print("=" * 70)
    print("SENTIMENT ANALYSIS EVALUATION REPORT")
    print("=" * 70)
    print(f"\nOverall Accuracy: {acc_percentage:.2f}%\n")

    print("-" * 70)
    print("CLASSIFICATION REPORT")
    print("-" * 70)
    print(report)

    print("-" * 70)
    print("CONFUSION MATRIX")
    print("-" * 70)
    print(cm_df.to_string())

    print("\n" + "-" * 70)
    print(f"MISMATCHED PREDICTIONS ({len(mismatch_df)} row(s)):")
    print("-" * 70)
    if not mismatch_df.empty:
        print(mismatch_df.to_string(index=False))
    else:
        print("No mismatches found!")

    print("=" * 70)

    return df


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    evaluate_sentiment_model()
