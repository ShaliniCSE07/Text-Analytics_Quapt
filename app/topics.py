import sys
from sentence_transformers import SentenceTransformer, util

try:
    from app.topics_config import load_topics
except ImportError:
    from topics_config import load_topics

MODEL_NAME = "all-MiniLM-L6-v2"

# Load model once at module level (expensive — keep at top)
model = SentenceTransformer(MODEL_NAME)


def tag_topics(text: str, threshold: float = 0.3) -> list:
    """Tag topics for input text using cosine similarity.

    Reads the live topics dict from disk each call so admin edits
    take effect immediately without restarting the server.

    Returns a list of topic names matching or exceeding the similarity
    threshold. Returns ["Uncategorised"] if nothing matches or text
    is empty.
    """
    if not text or not text.strip():
        return ["Uncategorised"]

    # Fresh load every call — picks up any runtime admin changes
    topics = load_topics()

    try:
        topic_names = list(topics.keys())
        topic_descriptions = list(topics.values())

        text_embedding = model.encode(text, convert_to_tensor=True)
        topic_embeddings = model.encode(topic_descriptions, convert_to_tensor=True)

        cosine_scores = util.cos_sim(text_embedding, topic_embeddings)[0]

        matched_topics = [
            name for name, score in zip(topic_names, cosine_scores)
            if float(score) >= threshold
        ]

        return matched_topics if matched_topics else ["Uncategorised"]
    except Exception:
        return ["Uncategorised"]


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    samples = [
        "Battery drains too fast, very disappointed.",
        "Battery drains way too fast, but the camera is amazing!",
        "Delivery was quick and packaging was solid.",
        "It's fine I guess, does the job.",
        ""
    ]

    for sample in samples:
        results = tag_topics(sample)
        print(f"Text   : {repr(sample)}")
        print(f"Topics : {results}")
        print("-" * 50)

    print("\n--- Live topics loaded from JSON ---")
    print(load_topics())
