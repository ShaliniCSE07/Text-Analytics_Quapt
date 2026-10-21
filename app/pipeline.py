import sys
from app.language_filter import is_supported
from app.preprocess import clean_text
from app.sentiment import predict_sentiment_v2
from app.topics import tag_topics


def analyze_review(review: dict) -> dict:
    """Analyze a single review dict for language support, sentiment, and topic tags.

    Takes a dict containing review metadata and a "Review" key.
    Returns the original dict updated with 'Rating', 'Tags', and 'Confidence'.
    """
    result = dict(review) if review else {}
    raw_text = result.get("Review")

    if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
        result.update({
            "Rating": "language unsupported",
            "Tags": "",
            "Confidence": 0
        })
        return result

    if not is_supported(raw_text):
        result.update({
            "Rating": "language unsupported",
            "Tags": "",
            "Confidence": 0
        })
        return result

    cleaned = clean_text(raw_text)
    sentiment = predict_sentiment_v2(cleaned)
    topics = tag_topics(cleaned)

    tags_str = "|".join(topics)

    result.update({
        "Rating": sentiment.get("label", "Neutral"),
        "Tags": tags_str,
        "Confidence": sentiment.get("confidence", 0)
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
