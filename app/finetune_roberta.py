# app/finetune_roberta.py
import pandas as pd
import numpy as np
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
CSV_PATH = "data/labeled_validation_set.csv"
OUTPUT_DIR = "./models/finetuned-insurance-roberta"

def load_insurance_data():
    df = pd.read_csv(CSV_PATH)
    
    text_col = 'Review'
    label_col = 'True_Label'
    
    # Map string labels to integers (matching baseline script)
    label_map = {
        "Positive": 2, "Neutral": 1, "Negative": 0,
        "positive": 2, "neutral": 1, "negative": 0
    }
    
    df['label'] = df[label_col].map(label_map)
    df = df.dropna(subset=['label', text_col])
    df['label'] = df['label'].astype(int)
    
    print(f"Loaded {len(df)} rows. Class counts: {df['label'].value_counts().to_dict()}")
    
    df = df.rename(columns={text_col: 'text'})
    return Dataset.from_pandas(df[['text', 'label']].reset_index(drop=True))

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='macro', zero_division=0
    )
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "precision": precision, "recall": recall, "f1": f1}

def main():
    ds = load_insurance_data()
    
    # 80/20 train/test split
    ds = ds.train_test_split(test_size=0.2, seed=42)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    def tokenize(batch):
        return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=128)

    tok = ds.map(tokenize, batched=True)
    tok = tok.rename_column("label", "labels")
    tok.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)

    # Small dataset (60 rows), so we use small batch size and few epochs to prevent overfitting
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        learning_rate=2e-5,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        num_train_epochs=3,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        logging_steps=5,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tok["train"],
        eval_dataset=tok["test"],
        compute_metrics=compute_metrics,
    )

    print("\nStarting fine-tuning...")
    trainer.train()
    
    print("\n--- FINE-TUNED METRICS ---")
    results = trainer.evaluate()
    print(f"Accuracy:  {results['eval_accuracy']:.4f}")
    print(f"Precision: {results['eval_precision']:.4f}")
    print(f"Recall:    {results['eval_recall']:.4f}")
    print(f"F1-Score:  {results['eval_f1']:.4f}")
    
    # Save model
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\nModel saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()