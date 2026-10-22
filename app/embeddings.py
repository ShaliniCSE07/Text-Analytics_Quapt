import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
_embedder = None

def get_embedder() -> SentenceTransformer:
    """Lazily load and return the shared SentenceTransformer model instance."""
    global _embedder
    if _embedder is None:
        logger.info(f"Loading shared SentenceTransformer model: {MODEL_NAME}")
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder
