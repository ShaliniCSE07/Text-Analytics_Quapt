import re
import sys

def clean_text(text: str) -> str:
    """Clean input text by removing URLs, HTML tags, and extra whitespace while preserving casing, punctuation, and emojis.
    
    Handles empty string or None input gracefully.
    """
    if not text:
        return ""
    
    # Remove URLs (http:// or https://)
    text = re.sub(r'https?://\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Collapse multiple whitespace characters into a single space and trim
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    samples = [
        "This product is amazing!! 😍 Check it out at https://example.com/product",
        "Terrible experience...   would <br> not recommend <p>at all</p>",
        "   Extra   spaces    everywhere   ",
        "",
        None
    ]
    
    for sample in samples:
        cleaned = clean_text(sample)
        print(f"Original: {repr(sample)}\nCleaned : {repr(cleaned)}\n" + "-"*50)
