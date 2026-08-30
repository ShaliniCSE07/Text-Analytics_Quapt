import json
import os

# Path to the JSON config file (relative to project root when running uvicorn)
_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "topics_config.json")

# Hardcoded fallback (used if JSON file is missing on first run)
_FALLBACK_TOPICS = {
    "Battery": "battery life, charging, power drain",
    "Camera": "camera quality, photos, video recording",
    "Delivery": "shipping, delivery time, packaging",
    "Customer Support": "customer service, support response, returns",
    "Price": "price, value for money, cost",
}

# Keep TOPICS as module-level constant for any legacy imports
TOPICS = _FALLBACK_TOPICS.copy()


def load_topics() -> dict:
    """Read topics from data/topics_config.json.

    If the file is missing, falls back to the hardcoded dict and
    immediately creates the JSON file from it so future reads succeed.
    """
    path = os.path.normpath(_JSON_PATH)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # File missing — seed it from the fallback and return fallback
        save_topics(_FALLBACK_TOPICS)
        return _FALLBACK_TOPICS.copy()
    except json.JSONDecodeError:
        # Corrupt file — return fallback without overwriting
        return _FALLBACK_TOPICS.copy()


def save_topics(topics_dict: dict) -> None:
    """Write the given topics dict to data/topics_config.json."""
    path = os.path.normpath(_JSON_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(topics_dict, f, indent=2, ensure_ascii=False)
