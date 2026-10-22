# app/evaluate_baseline.py
import pandas as pd
from transformers import pipeline
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

CSV_PATH = "data/labeled_validation_set.csv"
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

print("Loading pretrained model (Baseline)...")
nlp = pipeline("sentiment-analysis", model=MODEL_NAME)

df = pd.read_csv(CSV_PATH)
texts = df['Review'].tolist()
true_labels = df['True_Label'].tolist()

print("Running predictions...")
predictions = nlp(texts, truncation=True, max_length=128)

# The model outputs 'positive', 'negative', 'neutral'. We need to map these to 0, 1, 2
label_map = {"negative": 0, "neutral": 1, "positive": 2}
pred_labels = [label_map[p['label'].lower()] for p in predictions]
true_labels_int = [label_map[t.lower()] for t in true_labels]

# Calculate metrics
precision, recall, f1, _ = precision_recall_fscore_support(true_labels_int, pred_labels, average='macro', zero_division=0)
acc = accuracy_score(true_labels_int, pred_labels)

print("\n--- BASELINE METRICS (Pretrained RoBERTa) ---")
print(f"Accuracy:  {acc:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-Score:  {f1:.4f}")