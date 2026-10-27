# app/run_scaling_experiment.py
import pandas as pd
import numpy as np
import os
from datasets import Dataset, load_dataset
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    Trainer, TrainingArguments
)
from sklearn.metrics import accuracy_score

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
OUTPUT_DIR = "./models/scaling_experiment"

# Label mapping for string labels
label_map = {
    "positive": 2, "neutral": 1, "negative": 0,
    "Positive": 2, "Neutral": 1, "Negative": 0
}

def prepare_dataset(df, text_col='text', label_col='label'):
    """Cleans a pandas dataframe and returns a Hugging Face Dataset."""
    df = df.dropna(subset=[text_col, label_col]).copy()
    
    # Map labels to integers if they are strings
    if df[label_col].dtype == object:
        df['label_int'] = df[label_col].str.lower().map(label_map)
    else:
        # If labels are already integers (like TweetEval: 0,1,2)
        df['label_int'] = df[label_col]
        
    df = df.dropna(subset=['label_int'])
    df['label_int'] = df['label_int'].astype(int)
    df['text'] = df[text_col].astype(str)
    
    return Dataset.from_pandas(df[['text', 'label_int']].reset_index(drop=True))

def run_experiment(dataset_name, full_dataset):
    """Runs fine-tuning for sizes [25, 50, 1000] and returns results."""
    results = {}
    
    for n in [25, 50, 1000]:
        # If dataset has fewer than n rows, use the max available
        sample_size = min(n, len(full_dataset))
        
        # Shuffle and select N samples
        subset = full_dataset.shuffle(seed=42).select(range(sample_size))
        
        # 80/20 split
        ds_split = subset.train_test_split(test_size=0.2, seed=42)
        
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        def tokenize(batch):
            return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=128)
            
        tok = ds_split.map(tokenize, batched=True)
        tok = tok.rename_column("label_int", "labels")
        tok.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
        
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)
        
        # Use 1 epoch for speed, especially for n=1000
        args = TrainingArguments(
            output_dir=f"{OUTPUT_DIR}/{dataset_name}_{sample_size}",
            learning_rate=2e-5,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            num_train_epochs=1, 
            eval_strategy="no",
            save_strategy="no",
            report_to="none",
        )
        
        trainer = Trainer(model=model, args=args, train_dataset=tok["train"], eval_dataset=tok["test"])
        trainer.train()
        
        # Evaluate
        preds = trainer.predict(tok["test"])
        acc = accuracy_score(preds.label_ids, np.argmax(preds.predictions, axis=-1))
        
        results[sample_size] = acc
        print(f"✅ {dataset_name} | n={sample_size} | Accuracy={acc:.4f}")
        
    return results

if __name__ == "__main__":
    all_results = {}

    # 1. Insurance
    if os.path.exists('data/real_datasets/insurance.csv'):
        print("\n--- Insurance ---")
        df_ins = pd.read_csv('data/real_datasets/insurance.csv')
        all_results['Insurance'] = run_experiment('insurance', prepare_dataset(df_ins))

    # 2. Banking
    if os.path.exists('data/real_datasets/banking.csv'):
        print("\n--- Banking ---")
        df_bank = pd.read_csv('data/real_datasets/banking.csv')
        all_results['Banking'] = run_experiment('banking', prepare_dataset(df_bank))

    # 3. Manufacturing
    if os.path.exists('data/real_datasets/manufacturing.csv'):
        print("\n--- Manufacturing ---")
        df_man = pd.read_csv('data/real_datasets/manufacturing.csv')
        all_results['Manufacturing'] = run_experiment('manufacturing', prepare_dataset(df_man))

    # 4. Tweets (Loaded directly from Hugging Face)
    print("\n--- Tweets (TweetEval) ---")
    tweet_ds = load_dataset("cardiffnlp/tweet_eval", "sentiment")["train"]
    tweet_df = tweet_ds.to_pandas()
    all_results['Tweets'] = run_experiment('tweets', prepare_dataset(tweet_df, text_col='text', label_col='label'))

    # Final Summary
    print("\n" + "="*40)
    print("FINAL SUMMARY: Accuracy by Dataset Size")
    print("="*40)
    for domain, res in all_results.items():
        print(f"\n{domain}:")
        for size, acc in res.items():
            print(f"  {size} samples: {acc*100:.2f}%")