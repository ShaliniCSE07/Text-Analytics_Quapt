import os
import re
import sqlite3
from typing import List, Dict, Optional, Tuple, Any
from sentence_transformers import util

try:
    from app.embeddings import get_embedder
except ImportError:
    from embeddings import get_embedder

LEARNING_SIMILARITY_THRESHOLD = 0.85
DB_PATH = "data/reviews.db"

# Words that alter sentiment or contrast
NEGATION_WORDS = {
    "not", "no", "never", "none", "nobody", "nothing", "hardly", "barely",
    "without", "cannot", "cant", "wont", "dont", "doesnt", "didnt", "isnt",
    "wasnt", "couldnt", "wouldnt"
}

CONTRAST_WORDS = {"but", "however", "though", "yet"}

# In-memory caches for load_memory()
_memory_cache: Optional[List[Dict[str, Any]]] = None
_last_db_signature: Optional[Tuple[int, int, int]] = None
_embedding_cache: Dict[int, Any] = {}


def _signature(text: str) -> Tuple[bool, bool]:
    """Return (has_negation, has_contrast) for the given text.

    Lowercase the text and remove apostrophes first before checking.
    """
    if not text:
        return (False, False)

    # Lowercase and remove single quotes / apostrophes
    t = text.lower().replace("'", "").replace("’", "")
    words = set(re.findall(r"\b[a-z]+\b", t))

    has_negation = bool(words & NEGATION_WORDS)
    has_contrast = bool(words & CONTRAST_WORDS)

    return (has_negation, has_contrast)


def load_memory() -> List[Dict[str, Any]]:
    """Load latest approved human corrections from Review_Corrections.

    Takes, for each Platform_Reference_Id, the row with the highest
    Correction_Id among rows with Approved_For_Learning = 1.
    Skips rows whose Review_Text is NULL/empty or whose Corrected_Rating
    isn't Positive, Negative, or Neutral.
    Embeddings are cached by Correction_Id, and memory is automatically
    rebuilt when Review_Corrections count, max id, or sum of approval changes.
    """
    global _memory_cache, _last_db_signature, _embedding_cache

    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check db state signature
    cursor.execute("""
        SELECT COUNT(*), MAX(Correction_Id), SUM(Approved_For_Learning)
        FROM Review_Corrections
    """)
    sig_row = cursor.fetchone()
    count = sig_row[0] or 0
    max_id = sig_row[1] or 0
    sum_approved = sig_row[2] or 0
    current_sig = (count, max_id, sum_approved)

    if _memory_cache is not None and current_sig == _last_db_signature:
        conn.close()
        return _memory_cache

    # Query latest approved correction per Platform_Reference_Id
    cursor.execute("""
        SELECT rc.Correction_Id, rc.Platform_Reference_Id, rc.Review_Text, rc.Corrected_Rating
        FROM Review_Corrections rc
        JOIN (
            SELECT Platform_Reference_Id, MAX(Correction_Id) as max_id
            FROM Review_Corrections
            WHERE Approved_For_Learning = 1
            GROUP BY Platform_Reference_Id
        ) latest ON rc.Correction_Id = latest.max_id
        WHERE rc.Review_Text IS NOT NULL 
          AND trim(rc.Review_Text) != ''
          AND rc.Corrected_Rating IN ('Positive', 'Negative', 'Neutral')
    """)
    rows = cursor.fetchall()
    conn.close()

    embedder = get_embedder()
    new_memory = []

    for r in rows:
        cid = r["Correction_Id"]
        review_text = r["Review_Text"]
        corrected_rating = r["Corrected_Rating"]
        pid = r["Platform_Reference_Id"]

        if cid in _embedding_cache:
            emb = _embedding_cache[cid]
        else:
            emb = embedder.encode(review_text, convert_to_tensor=True)
            _embedding_cache[cid] = emb

        new_memory.append({
            "id": pid,
            "text": review_text,
            "label": corrected_rating,
            "embedding": emb,
            "correction_id": cid
        })

    _memory_cache = new_memory
    _last_db_signature = current_sig

    return _memory_cache


def find_learned_label(
    text: str,
    memory: Optional[List[Dict[str, Any]]] = None,
    threshold: float = LEARNING_SIMILARITY_THRESHOLD
) -> Dict[str, Any]:
    """Find learned label for new text based on memory of approved corrections.

    Returns dict with keys:
      applied (bool)
      label (str or None)
      similarity (int, 0-100)
      matched_id (str or None)
      reason (str: 'match', 'below_threshold', 'signature_mismatch', 'conflict', 'empty_text', 'empty_memory')
    """
    if not text or not isinstance(text, str) or not text.strip():
        return {
            "applied": False,
            "label": None,
            "similarity": 0,
            "matched_id": None,
            "reason": "empty_text"
        }

    mem_entries = memory if memory is not None else load_memory()
    if not mem_entries:
        return {
            "applied": False,
            "label": None,
            "similarity": 0,
            "matched_id": None,
            "reason": "empty_memory"
        }

    embedder = get_embedder()
    text_embedding = embedder.encode(text, convert_to_tensor=True)
    text_sig = _signature(text)

    # Compute similarity and signature for all memory entries
    scored_entries = []
    for entry in mem_entries:
        emb = entry.get("embedding")
        if emb is None:
            emb = embedder.encode(entry["text"], convert_to_tensor=True)

        sim_score = float(util.cos_sim(text_embedding, emb)[0][0])
        entry_sig = _signature(entry["text"])

        scored_entries.append({
            "id": entry.get("id"),
            "text": entry["text"],
            "label": entry["label"],
            "similarity": sim_score,
            "signature_matches": (entry_sig == text_sig)
        })

    # Find candidates meeting both similarity threshold and signature match
    candidates = [
        e for e in scored_entries
        if e["similarity"] >= threshold and e["signature_matches"]
    ]

    max_overall_sim = max((e["similarity"] for e in scored_entries), default=0.0)
    max_overall_sim_int = round(max_overall_sim * 100)

    if not candidates:
        # Check if excluded by signature mismatch:
        # 1) Any entry with similarity >= threshold failed signature match, OR
        # 2) The top overall matching entry (with significant similarity >= 0.70) had a signature mismatch
        high_sim_mismatches = [
            e for e in scored_entries
            if e["similarity"] >= threshold and not e["signature_matches"]
        ]
        top_overall = max(scored_entries, key=lambda e: e["similarity"]) if scored_entries else None

        if high_sim_mismatches:
            top_mismatch = max(high_sim_mismatches, key=lambda e: e["similarity"])
            return {
                "applied": False,
                "label": None,
                "similarity": round(top_mismatch["similarity"] * 100),
                "matched_id": None,
                "reason": "signature_mismatch"
            }
        elif top_overall and not top_overall["signature_matches"] and top_overall["similarity"] >= 0.70:
            return {
                "applied": False,
                "label": None,
                "similarity": round(top_overall["similarity"] * 100),
                "matched_id": None,
                "reason": "signature_mismatch"
            }
        else:
            return {
                "applied": False,
                "label": None,
                "similarity": max_overall_sim_int,
                "matched_id": None,
                "reason": "below_threshold"
            }

    # Candidates exist: check if they have conflicting labels
    distinct_labels = {c["label"] for c in candidates}
    top_candidate = max(candidates, key=lambda e: e["similarity"])
    top_sim_int = round(top_candidate["similarity"] * 100)

    if len(distinct_labels) > 1:
        return {
            "applied": False,
            "label": None,
            "similarity": top_sim_int,
            "matched_id": None,
            "reason": "conflict"
        }

    return {
        "applied": True,
        "label": top_candidate["label"],
        "similarity": top_sim_int,
        "matched_id": top_candidate["id"],
        "reason": "match"
    }
