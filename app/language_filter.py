from langdetect import detect, LangDetectException

def detect_language(text: str) -> str:
    """Detect the language of the given text using langdetect.
    
    Returns 2-letter language code (e.g. 'en', 'fr', 'es') or 'unknown' on failure.
    """
    try:
        return detect(text)
    except Exception:
        return "unknown"

def is_supported(text: str) -> bool:
    """Check if the text language is English ('en')."""
    return detect_language(text) == "en"

if __name__ == "__main__":
    samples = [
        "This product is amazing, I love it!",
        "Ce produit est incroyable",
        "Muy bueno, lo recomiendo",
        ""
    ]
    
    for sample in samples:
        result = is_supported(sample)
        print(f"Text: '{sample}' -> English supported: {result}")
