import json
import sys
from app.language_filter import is_supported
from app.preprocess import clean_text
from app.sentiment import predict_sentiment_v2
from app.topics import tag_topics
from app.emotion import predict_emotion

try:
    from app.learning import find_learned_label
except ImportError:
    from learning import find_learned_label


def analyze_review(review: dict) -> dict:
    """Analyze a single review dict for language support, sentiment, topic tags, emotions, and learned corrections.

    Takes a dict containing review metadata and a "Review" key.
    Returns the original dict updated with 'Rating', 'Tags', 'Confidence', 'Emotion',
    'Emotion_Confidence', 'Emotion_Scores', 'Emotion_Model', 'Label_Source', 'Model_Rating',
    'Learned_From', and 'Learned_Similarity'.
    """
    result = dict(review) if review else {}
    raw_text = result.get("Review")

    if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
        result.update({
            "Rating": "language unsupported",
            "Tags": "",
            "Confidence": 0,
            "Emotion": "language unsupported",
            "Emotion_Confidence": 0,
            "Emotion_Scores": "{}",
            "Emotion_Model": "skipped (empty text)",
            "Label_Source": "model",
            "Model_Rating": "language unsupported",
            "Learned_From": None,
            "Learned_Similarity": None
        })
        return result

    if not is_supported(raw_text):
        result.update({
            "Rating": "language unsupported",
            "Tags": "",
            "Confidence": 0,
            "Emotion": "language unsupported",
            "Emotion_Confidence": 0,
            "Emotion_Scores": "{}",
            "Emotion_Model": "skipped (language unsupported)",
            "Label_Source": "model",
            "Model_Rating": "language unsupported",
            "Learned_From": None,
            "Learned_Similarity": None
        })
        return result

    cleaned = clean_text(raw_text)
    sentiment = predict_sentiment_v2(cleaned)
    topics = tag_topics(cleaned)
    emotion_res = predict_emotion(cleaned)

    model_label = sentiment.get("label", "Neutral")
    confidence = sentiment.get("confidence", 0)

    # Check learned memory
    learned_res = find_learned_label(cleaned)
    if learned_res.get("applied") and learned_res.get("label") != model_label:
        final_rating = learned_res["label"]
        final_confidence = learned_res["similarity"]
        label_source = "learned"
        model_rating = model_label
        learned_from = learned_res.get("matched_id")
        learned_similarity = learned_res.get("similarity")
    else:
        final_rating = model_label
        final_confidence = confidence
        label_source = "model"
        model_rating = model_label
        learned_from = None
        learned_similarity = None

    tags_str = "|".join(topics)

    result.update({
        "Rating": final_rating,
        "Tags": tags_str,
        "Confidence": final_confidence,
        "Emotion": emotion_res.get("emotion", "Uncertain"),
        "Emotion_Confidence": emotion_res.get("confidence", 0),
        "Emotion_Scores": json.dumps(emotion_res.get("mapped_scores", {})),
        "Emotion_Model": emotion_res.get("model", ""),
        "Label_Source": label_source,
        "Model_Rating": model_rating,
        "Learned_From": learned_from,
        "Learned_Similarity": learned_similarity
    })

    return result


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    sample_reviews = [
        {
            "Platform": "Google",
            "Company": "Acme Insurance",
            "Product": "Acme Health Shield",
            "Review": "Cashless approval at the network hospital came through in under two hours. Really impressed with the TPA team!"
        },
        {
            "Platform": "Twitter",
            "Company": "Acme Insurance",
            "Product": "Acme Health Shield",
            "Review": "Ce produit est incroyable"
        },
        {
            "Platform": "Google",
            "Company": "Acme Insurance",
            "Product": "Acme Motor Secure",
            "Review": "Claim for my bumper damage was settled in five days. The garage network was excellent."
        }
    ]

    for sample in sample_reviews:
        res = analyze_review(sample)
        print(res)
