import re
import sys
from transformers import pipeline

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Load model once at module level
sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL_NAME)

LOW_CONFIDENCE_THRESHOLD = 55

LABEL_MAP = {
    "positive": "Positive",
    "neutral": "Neutral",
    "negative": "Negative"
}

def predict_sentiment(text: str) -> dict:
    """Predict sentiment of the input text using twitter-roberta-base-sentiment-latest.
    
    Returns a dict with 'label' ('Positive', 'Neutral', or 'Negative') and 'confidence' (0-100 integer).
    Handles empty string or None input gracefully.
    """
    if not text or not text.strip():
        return {"label": "Neutral", "confidence": 0}
    
    try:
        raw_output = sentiment_pipeline(text)[0]
        raw_label = raw_output.get("label", "").lower()
        score = raw_output.get("score", 0.0)
        
        mapped_label = LABEL_MAP.get(raw_label, "Neutral")
        confidence = round(score * 100)
        
        return {
            "label": mapped_label,
            "confidence": confidence
        }
    except Exception:
        return {"label": "Neutral", "confidence": 0}

def predict_sentiment_v2(text: str) -> dict:
    """Predict sentiment considering contrast words (but, however, though, yet).
    
    If contrast words are found, splits text at the first occurrence, analyzes each part,
    and resolves mixed sentiment based on confidence score comparison.
    If no contrast words are present, overrides label to 'Neutral' if confidence is below LOW_CONFIDENCE_THRESHOLD.
    """
    if not text or not text.strip():
        return {"label": "Neutral", "confidence": 0}
    
    match = re.search(r'\b(but|however|though|yet)\b', text, flags=re.IGNORECASE)
    if not match:
        res = predict_sentiment(text)
        if res["confidence"] < LOW_CONFIDENCE_THRESHOLD:
            res["label"] = "Neutral"
        return res
    
    part1 = text[:match.start()].strip()
    part2 = text[match.end():].strip()
    
    res1 = predict_sentiment(part1)
    res2 = predict_sentiment(part2)
    
    conf1 = res1["confidence"]
    conf2 = res2["confidence"]
    
    if abs(conf1 - conf2) < 10:
        return {"label": "Neutral", "confidence": min(conf1, conf2)}
    elif conf1 > conf2:
        return res1
    else:
        return res2

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    samples = [
        "Absolutely fantastic, best purchase ever!",
        "Battery drains way too fast, but the camera is amazing!",
        "It's okay, but not great, though it does the job fine.",
        "Great price, but delivery was very slow and support was rude.",
        "Price is a bit high for what you get, average phone overall.",
        "Works okay for the price, nothing special."
    ]
    
    for sample in samples:
        result = predict_sentiment_v2(sample)
        print(f"Text  : {repr(sample)}\nResult: {result}\n" + "-"*50)

