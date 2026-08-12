import sys
from sentence_transformers import SentenceTransformer, util

try:
    from app.topics_config import TOPICS
except ImportError:
    from topics_config import TOPICS

MODEL_NAME = "all-MiniLM-L6-v2"

# Load model once at module level
model = SentenceTransformer(MODEL_NAME)

def tag_topics(text: str, topics: dict = TOPICS, threshold: float = 0.3) -> list:
    """Tag topics for input text using cosine similarity with a dictionary of topic descriptions.
    
    Returns a list of topic names matching or exceeding the similarity threshold.
    If no topic clears threshold or text is empty/None, returns ["Uncategorised"].
    """
    if not text or not text.strip():
        return ["Uncategorised"]
    
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
        
    print("\n--- Testing Custom Topics ---")
    custom_topics = {"Fit": "sizing, fit, true to size", "Fabric": "fabric quality, material, texture"}
    custom_text = "The fabric feels cheap and the sizing runs small"
    result = tag_topics(custom_text, topics=custom_topics)
    print(f"Text   : {repr(custom_text)}")
    print(f"Result : {result}")

