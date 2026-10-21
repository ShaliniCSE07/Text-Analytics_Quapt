import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from transformers import pipeline

logger = logging.getLogger(__name__)

# Model identifier
DEFAULT_EMOTION_MODEL = "SamLowe/roberta-base-go_emotions"

# Configurable thresholds
# If highest mapped emotion score is below this threshold, classify as 'Uncertain'
EMOTION_CONFIDENCE_THRESHOLD = 0.35  # 35%
AMBIGUITY_MARGIN = 0.05             # When top 2 emotions are within 5% of each other

# Target Business Emotions
BUSINESS_EMOTIONS = [
    "Anger",
    "Frustration",
    "Disappointment",
    "Anxiety",
    "Confusion",
    "Delight"
]

# Source label mapping based on ICXBee reference guide
# Source labels from GoEmotions (28 classes)
EMOTION_LABEL_MAPPING = {
    "Anger": ["anger", "disgust"],
    "Frustration": ["annoyance", "disapproval"],
    "Disappointment": ["disappointment", "sadness", "remorse"],
    "Anxiety": ["nervousness", "fear"],
    "Confusion": ["confusion"],  # 'curiosity' is selectively applied only when text context supports confusion
    "Delight": ["joy", "admiration", "gratitude", "excitement", "approval"]
}

# Context patterns indicating genuine customer confusion (vs general inquiry)
CONFUSION_INDICATORS = [
    r"\bconfus(ed|ing|ion)\b",
    r"\bunclear\b",
    r"\bnot understand\b",
    r"\bdon't understand\b",
    r"\bno explanation\b",
    r"\bmislead(ing|ed)?\b",
    r"\bhidden (charges|fees|clauses)\b",
    r"\bwhy did\b",
    r"\bwhy was\b",
    r"\bhow come\b",
    r"\bwhere did\b",
    r"\bwhat does (this|it) mean\b",
    r"\bwithout (any )?(explanation|reason)\b"
]

_emotion_pipeline = None

def get_emotion_pipeline():
    """Lazily load and reuse the RoBERTa GoEmotions classification pipeline."""
    global _emotion_pipeline
    if _emotion_pipeline is None:
        logger.info(f"Loading emotion classification model: {DEFAULT_EMOTION_MODEL}")
        _emotion_pipeline = pipeline(
            "text-classification",
            model=DEFAULT_EMOTION_MODEL,
            top_k=None  # Return scores for all 28 classes
        )
    return _emotion_pipeline


def _context_supports_confusion(text: str) -> bool:
    """Check if review text contains linguistic patterns supporting confusion."""
    text_lower = text.lower()
    for pattern in CONFUSION_INDICATORS:
        if re.search(pattern, text_lower):
            return True
    return False


def _generate_explanation(
    primary_emotion: str,
    confidence_score: float,
    mapped_scores: Dict[str, float],
    top_source_cues: List[Dict[str, Any]],
    text: str
) -> str:
    """Generate a cautious, text-grounded explanation.
    
    Does NOT claim to read actual human feelings; clarifies that scores
    reflect linguistic pattern matching from the pretrained model.
    """
    if primary_emotion in ("Uncertain", "language unsupported", "No clear emotion"):
        if mapped_scores:
            top_cand = max(mapped_scores.items(), key=lambda x: x[1])
            return (
                f"No emotion crossed the confidence threshold ({int(EMOTION_CONFIDENCE_THRESHOLD * 100)}%). "
                f"Highest detected pattern was {top_cand[0]} ({round(top_cand[1] * 100)}%), "
                "which is insufficient for a reliable classification."
            )
        return "Review text does not exhibit sufficient lexical patterns for emotion classification."

    cues_str = ", ".join([f"{c['label']} ({round(c['score'] * 100)}%)" for c in top_source_cues[:3]])
    
    explanation = (
        f"Classified as '{primary_emotion}' based on prominent source signals: {cues_str}. "
        f"Mapped confidence is {round(confidence_score * 100)}%. "
        "Scores represent statistical text associations from RoBERTa GoEmotions, not verified human sentiment."
    )
    return explanation


class OptionalNLIValidator:
    """Modular stub for optional Zero-Shot NLI validation.
    
    Allows selective second-opinion verification of ambiguous or uncertain
    predictions without altering the primary GoEmotions pipeline or
    averaging uncalibrated raw scores.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or "facebook/bart-large-mnli"
        self._nli_pipeline = None

    def is_available(self) -> bool:
        return self._nli_pipeline is not None

    def verify(self, text: str, candidate_emotions: List[str]) -> Optional[Dict[str, Any]]:
        """Optionally verify candidate emotions with zero-shot NLI.
        
        Kept separate to avoid uncalibrated score mixing.
        """
        # Modular placeholder for future NLI second opinion
        return None


def predict_emotion(text: str, nli_validator: Optional[OptionalNLIValidator] = None) -> Dict[str, Any]:
    """Predict business emotion from review text using GoEmotions RoBERTa.
    
    Returns:
        dict containing:
            - 'emotion': Primary business emotion or 'Uncertain'
            - 'confidence': 0-100 integer score
            - 'mapped_scores': Dict of {emotion_name: float_score}
            - 'source_scores': Dict of top source GoEmotions labels
            - 'is_uncertain': bool
            - 'explanation': cautious model explanation
            - 'model': model identifier
    """
    if not text or not isinstance(text, str) or not text.strip():
        return {
            "emotion": "Uncertain",
            "confidence": 0,
            "mapped_scores": {e: 0.0 for e in BUSINESS_EMOTIONS},
            "source_scores": {},
            "is_uncertain": True,
            "explanation": "Empty text provided.",
            "model": DEFAULT_EMOTION_MODEL
        }

    try:
        classifier = get_emotion_pipeline()
        raw_outputs = classifier(text)[0]  # list of {'label': str, 'score': float}
    except Exception as e:
        logger.error(f"Emotion classification failed: {e}")
        return {
            "emotion": "Uncertain",
            "confidence": 0,
            "mapped_scores": {e: 0.0 for e in BUSINESS_EMOTIONS},
            "source_scores": {},
            "is_uncertain": True,
            "explanation": f"Inference error: {str(e)}",
            "model": DEFAULT_EMOTION_MODEL
        }

    # Build lookup of raw source label scores
    source_score_dict = {item["label"].lower(): float(item["score"]) for item in raw_outputs}

    # Map to business emotions using MAX score per category (not summing)
    mapped_scores: Dict[str, float] = {}
    top_cues_per_emotion: Dict[str, List[Dict[str, Any]]] = {}

    for b_emotion, src_labels in EMOTION_LABEL_MAPPING.items():
        relevant_scores = []
        for lbl in src_labels:
            s = source_score_dict.get(lbl, 0.0)
            relevant_scores.append({"label": lbl, "score": s})

        # Special handling for Confusion + curiosity
        if b_emotion == "Confusion":
            curiosity_score = source_score_dict.get("curiosity", 0.0)
            if curiosity_score > 0 and _context_supports_confusion(text):
                relevant_scores.append({"label": "curiosity (contextual)", "score": curiosity_score})

        relevant_scores.sort(key=lambda x: x["score"], reverse=True)
        top_cues_per_emotion[b_emotion] = relevant_scores
        # MAX rule to avoid bias towards categories with more mapped labels
        max_score = relevant_scores[0]["score"] if relevant_scores else 0.0
        mapped_scores[b_emotion] = round(max_score, 4)

    # Sort mapped emotions by score
    sorted_mapped = sorted(mapped_scores.items(), key=lambda x: x[1], reverse=True)
    top_emotion, top_score = sorted_mapped[0]
    second_emotion, second_score = sorted_mapped[1]

    # Check confidence threshold
    is_uncertain = False
    primary_emotion = top_emotion

    if top_score < EMOTION_CONFIDENCE_THRESHOLD:
        primary_emotion = "Uncertain"
        is_uncertain = True
        confidence = round(top_score * 100)
    else:
        # Check for ambiguity (close tie)
        if (top_score - second_score) < AMBIGUITY_MARGIN and second_score >= EMOTION_CONFIDENCE_THRESHOLD:
            # If two emotions are tied very closely, check if NLI validator is provided
            if nli_validator and nli_validator.is_available():
                nli_res = nli_validator.verify(text, [top_emotion, second_emotion])
                if nli_res and nli_res.get("primary_emotion"):
                    primary_emotion = nli_res["primary_emotion"]
            # Confidence reflects top score
            confidence = round(top_score * 100)
        else:
            confidence = round(top_score * 100)

    # Filter top 5 source cues for explainability
    top_5_cues = sorted(
        [{"label": item["label"], "score": round(float(item["score"]), 4)} for item in raw_outputs],
        key=lambda x: x["score"],
        reverse=True
    )[:5]

    explanation = _generate_explanation(
        primary_emotion=primary_emotion,
        confidence_score=top_score,
        mapped_scores=mapped_scores,
        top_source_cues=top_5_cues,
        text=text
    )

    return {
        "emotion": primary_emotion,
        "confidence": confidence,
        "raw_confidence": top_score,
        "mapped_scores": mapped_scores,
        "source_scores": {c["label"]: c["score"] for c in top_5_cues},
        "is_uncertain": is_uncertain,
        "explanation": explanation,
        "model": DEFAULT_EMOTION_MODEL
    }
