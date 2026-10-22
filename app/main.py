from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app.pipeline import analyze_review
from app.summarizer import generate_summary
from app.keywords import extract_keywords, extract_distinctive_keywords
from app.topics_config import load_topics, save_topics
from app.database import init_db
from app.emotion import predict_emotion, BUSINESS_EMOTIONS, EMOTION_CONFIDENCE_THRESHOLD
from app.preprocess import clean_text
from app.language_filter import is_supported
from datetime import datetime
import csv
import json
import os
import sqlite3

app = FastAPI(title="Text Analytics Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.on_event("startup")
def startup_event():
    init_db()


class ReviewInput(BaseModel):
    Platform: str
    Company: str
    Product: str
    Review: str
    Platform_Reference_Id: str = ""

class CorrectionInput(BaseModel):
    Platform_Reference_Id: str
    Corrected_Rating: Optional[str] = None
    Corrected_Tags: Optional[str] = None
    Corrected_By: str

class ApprovalInput(BaseModel):
    approved: bool

class TopicCreate(BaseModel):
    name: str
    description: str

class TopicUpdate(BaseModel):
    description: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/analyze-review")
def analyze_review_endpoint(review_input: ReviewInput):
    review_dict = review_input.dict()
    result = analyze_review(review_dict)
    return result

@app.patch("/reviews/correct")
def correct_review(correction: CorrectionInput):
    correction_data = {
        "Platform_Reference_Id": correction.Platform_Reference_Id,
        "Corrected_Rating": correction.Corrected_Rating,
        "Corrected_Tags": correction.Corrected_Tags,
        "Corrected_By": correction.Corrected_By,
        "Corrected_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    file_path = "data/corrections_log.csv"
    os.makedirs("data", exist_ok=True)
    file_exists = os.path.exists(file_path)
    
    with open(file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=correction_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(correction_data)
        
    # Open DB with row factory for named column access
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Retrieve current analysis values
    cursor.execute(
        "SELECT Rating, Tags, Model_Rating FROM Customer_Reviews_Analysis WHERE Platform_Reference_Id = ?",
        (correction.Platform_Reference_Id,)
    )
    current_analysis = cursor.fetchone()
    current_rating = current_analysis["Rating"] if current_analysis else None
    current_tags = current_analysis["Tags"] if current_analysis else None
    current_model_rating = current_analysis["Model_Rating"] if current_analysis else None

    # Retrieve original analysis values and raw review text for logging
    # First, try to get the earliest correction record for this Platform_Reference_Id
    cursor.execute(
        "SELECT Original_Rating, Original_Tags FROM Review_Corrections WHERE Platform_Reference_Id = ? AND Original_Rating IS NOT NULL ORDER BY Correction_Id ASC LIMIT 1",
        (correction.Platform_Reference_Id,)
    )
    earliest_corr = cursor.fetchone()
    if earliest_corr:
        original_rating = earliest_corr["Original_Rating"]
        original_tags = earliest_corr["Original_Tags"]
    else:
        # Fallback to model's original prediction if no prior correction exists
        original_rating = current_model_rating if current_model_rating is not None else current_rating
        original_tags = current_tags

    # Get raw review text for storing in corrections log
    cursor.execute(
        "SELECT Review FROM Customer_Reviews WHERE Platform_Reference_Id = ?",
        (correction.Platform_Reference_Id,)
    )
    review_row = cursor.fetchone()
    review_text = review_row["Review"] if review_row else ""

    updates = []
    params = []
    
    if correction.Corrected_Rating is not None:
        updates.append("Rating = ?")
        params.append(correction.Corrected_Rating)
        
    if correction.Corrected_Tags is not None:
        updates.append("Tags = ?")
        params.append(correction.Corrected_Tags)
        
    applied = False
    correction_id = None
    if updates:
        # Ensure this update is marked as human corrected
        updates.append("Label_Source = 'human'")
        query = f"UPDATE Customer_Reviews_Analysis SET {', '.join(updates)} WHERE Platform_Reference_Id = ?"
        params.append(correction.Platform_Reference_Id)
        cursor.execute(query, params)
        if cursor.rowcount > 0:
            applied = True
        conn.commit()

        # If Corrected_Rating or Corrected_Tags was not provided, store unchanged current value so each row is a complete snapshot
        effective_rating = correction.Corrected_Rating if correction.Corrected_Rating is not None else current_rating
        effective_tags = correction.Corrected_Tags if correction.Corrected_Tags is not None else current_tags

        # Record the correction for future learning
        cursor.execute(
            """INSERT INTO Review_Corrections (
                Platform_Reference_Id, Review_Text, Original_Rating, Corrected_Rating,
                Original_Tags, Corrected_Tags, Corrected_By, Corrected_At, Approved_For_Learning
            ) VALUES (?,?,?,?,?,?,?,?,1)""",
            (
                correction.Platform_Reference_Id,
                review_text,
                original_rating,
                effective_rating,
                original_tags,
                effective_tags,
                correction.Corrected_By,
                correction_data["Corrected_At"]
            )
        )
        correction_id = cursor.lastrowid
        conn.commit()

    conn.close()
    
    response_data = dict(correction_data)
    response_data["applied_to_analysis_table"] = applied
    response_data["correction_id"] = correction_id
    
    return response_data

@app.get("/reviews")
def get_reviews(
    platform: Optional[str] = None,
    product: Optional[str] = None,
    rating: Optional[str] = None,
    tag: Optional[str] = None
):
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT r.Platform, r.Company, r.Product, r.Review, r.Month_Year, r.Platform_Reference_Id, 
               a.Rating, a.Tags, a.Confidence, a.Emotion, a.Emotion_Confidence, a.Emotion_Scores, a.Emotion_Model, a.Load_timestamp,
               a.Label_Source, a.Model_Rating, a.Learned_From, a.Learned_Similarity
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE 1=1
    """
    params = []
    
    if platform:
        query += " AND r.Platform = ?"
        params.append(platform)
    if product:
        query += " AND r.Product = ?"
        params.append(product)
    if rating:
        query += " AND a.Rating = ?"
        params.append(rating)
    if tag:
        query += " AND a.Tags LIKE ?"
        params.append(f"%{tag}%")
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.get("/reviews/summary")
def get_reviews_summary():
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT count(*) as total FROM Customer_Reviews_Analysis")
    total_reviews = cursor.fetchone()["total"]
    
    cursor.execute("SELECT Rating, count(*) as cnt FROM Customer_Reviews_Analysis GROUP BY Rating")
    rating_breakdown = {row["Rating"]: row["cnt"] for row in cursor.fetchall()}
    
    cursor.execute("SELECT Tags FROM Customer_Reviews_Analysis")
    all_tags = cursor.fetchall()
    
    topic_breakdown = {}
    uncategorised_count = 0
    
    for row in all_tags:
        tags_str = row["Tags"]
        if not tags_str:
            continue
        tags_list = [t.strip() for t in tags_str.split("|") if t.strip()]
        for t in tags_list:
            if t == "Uncategorised":
                uncategorised_count += 1
            if t not in topic_breakdown:
                topic_breakdown[t] = 0
            topic_breakdown[t] += 1
            
    conn.close()
    
    return {
        "total_reviews": total_reviews,
        "rating_breakdown": rating_breakdown,
        "topic_breakdown": topic_breakdown,
        "uncategorised_count": uncategorised_count
    }

@app.get("/reviews/trend")
def get_reviews_trend():
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT r.Month_Year, a.Rating, count(*) as cnt
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        GROUP BY r.Month_Year, a.Rating
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    trend_data = {}
    for row in rows:
        month = row["Month_Year"]
        rating = row["Rating"]
        cnt = row["cnt"]
        if month not in trend_data:
            trend_data[month] = {"month": month, "Positive": 0, "Negative": 0, "Neutral": 0, "language unsupported": 0}
        
        if rating in trend_data[month]:
            trend_data[month][rating] += cnt
            
    # Sort chronologically (parse MM-YYYY into YYYY-MM)
    def sort_key(item):
        try:
            m, y = item["month"].split("-")
            return f"{y}-{m}"
        except ValueError:
            return item["month"]
        
    sorted_trend = sorted(trend_data.values(), key=sort_key)
    return sorted_trend

@app.get("/reviews/by-product")
def get_reviews_by_product():
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT r.Product, a.Rating, count(*) as cnt
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        GROUP BY r.Product, a.Rating
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    product_data = {}
    for row in rows:
        product = row["Product"]
        rating = row["Rating"]
        cnt = row["cnt"]
        if product not in product_data:
            product_data[product] = {"product": product, "Positive": 0, "Negative": 0, "Neutral": 0, "total": 0}
            
        if rating in product_data[product]:
            product_data[product][rating] += cnt
        product_data[product]["total"] += cnt
        
    return list(product_data.values())
@app.get("/reviews/summary-text")
def get_reviews_summary_text(
    product: Optional[str] = None,
    rating: Optional[str] = None
):
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch ALL reviews for the product (unfiltered by rating) so the
    # summary engine always sees the full sentiment picture. The rating
    # filter is passed to generate_summary for narrative framing only.
    base_query = """
        SELECT r.Review, r.Product, a.Rating, a.Tags, a.Emotion, a.Confidence
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE 1=1
    """
    params = []

    if product:
        base_query += " AND r.Product = ?"
        params.append(product)

    cursor.execute(base_query, params)
    rows = cursor.fetchall()
    conn.close()

    all_reviews = [dict(row) for row in rows if row["Review"]]

    # Sentiment breakdown across all reviews for the product
    sentiment_breakdown = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for r in all_reviews:
        r_rating = r.get("Rating", "")
        if r_rating in sentiment_breakdown:
            sentiment_breakdown[r_rating] += 1

    # Count for "based_on_reviews": use filtered subset if rating filter applied
    if rating:
        filtered_reviews = [r for r in all_reviews if r.get("Rating") == rating]
        based_on = len(filtered_reviews)
    else:
        based_on = len(all_reviews)

    summary = generate_summary(
        reviews=all_reviews,
        product_name=product,
        filter_rating=rating
    )

    return {
        "summary": summary,
        "based_on_reviews": based_on,
        "total_reviews": len(all_reviews),
        "sentiment_breakdown": sentiment_breakdown,
        "filter_applied": rating or "All",
    }

@app.get("/reviews/keywords")
def get_reviews_keywords(product: Optional[str] = None):
    """
    Returns keyword extractions for:
      - overall  (all matching reviews using TF-IDF, top_n=5)
      - positive (Rating = 'Positive' vs non-positive using distinctiveness, top_n=5)
      - negative (Rating = 'Negative' vs non-negative using distinctiveness, top_n=5)

    Optional query param ?product=<name> to scope the results.
    """
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT r.Review, a.Rating
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE 1=1
    """
    params = []

    if product:
        query += " AND r.Product = ?"
        params.append(product)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    all_reviews  = [row["Review"] for row in rows if row["Review"]]
    pos_reviews  = [row["Review"] for row in rows if row["Review"] and row["Rating"] == "Positive"]
    neg_reviews  = [row["Review"] for row in rows if row["Review"] and row["Rating"] == "Negative"]
    other_pos    = [row["Review"] for row in rows if row["Review"] and row["Rating"] != "Positive"]
    other_neg    = [row["Review"] for row in rows if row["Review"] and row["Rating"] != "Negative"]

    return {
        "overall":  extract_keywords(all_reviews, top_n=5),
        "positive": extract_distinctive_keywords(pos_reviews, other_pos, top_n=5),
        "negative": extract_distinctive_keywords(neg_reviews, other_neg, top_n=5),
    }


@app.get("/reviews/low-confidence")
def get_low_confidence_reviews(threshold: int = 60):
    """
    Returns reviews with Confidence score below the specified threshold,
    excluding 'language unsupported' entries.
    """
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT r.Platform, r.Product, r.Review, a.Rating, a.Tags, a.Confidence, r.Platform_Reference_Id
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE a.Confidence < ? AND a.Rating != 'language unsupported'
        ORDER BY a.Confidence ASC
    """

    cursor.execute(query, (threshold,))
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/reviews/spike-check")
def get_reviews_spike_check():
    """
    Splits reviews per product into older and newer halves by Load_timestamp
    and checks for a spike (>15% increase) in Negative review percentage.
    """
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT Product FROM Customer_Reviews_Analysis WHERE Product IS NOT NULL AND Product != ''")
    products = [row["Product"] for row in cursor.fetchall()]

    results = []
    for prod in products:
        cursor.execute("""
            SELECT Rating, Load_timestamp
            FROM Customer_Reviews_Analysis
            WHERE Product = ?
            ORDER BY Load_timestamp ASC
        """, (prod,))
        rows = cursor.fetchall()

        if len(rows) < 4:
            continue

        mid = len(rows) // 2
        older_half = rows[:mid]
        newer_half = rows[mid:]

        older_neg = sum(1 for r in older_half if r["Rating"] == "Negative")
        newer_neg = sum(1 for r in newer_half if r["Rating"] == "Negative")

        older_pct = round((older_neg / len(older_half)) * 100, 2)
        newer_pct = round((newer_neg / len(newer_half)) * 100, 2)

        change = round(newer_pct - older_pct, 2)
        is_spike = bool(change > 15)

        results.append({
            "product": prod,
            "older_negative_pct": older_pct,
            "newer_negative_pct": newer_pct,
            "change": change,
            "is_spike": is_spike
        })

    conn.close()
    return results


# ---------------------------------------------------------------------------
# PART 1 — Admin: topic management
# ---------------------------------------------------------------------------

@app.get("/admin/topics")
def get_topics():
    """Return the current topic dictionary."""
    return load_topics()


@app.post("/admin/topics")
def create_topic(body: TopicCreate):
    """Add a new topic. Returns the full updated topics dict."""
    topics = load_topics()
    if body.name in topics:
        raise HTTPException(status_code=409, detail=f"Topic '{body.name}' already exists.")
    topics[body.name] = body.description
    save_topics(topics)
    return topics


@app.put("/admin/topics/{name}")
def update_topic(name: str, body: TopicUpdate):
    """Update an existing topic's description. Returns updated topics dict."""
    topics = load_topics()
    if name not in topics:
        raise HTTPException(status_code=404, detail=f"Topic '{name}' not found.")
    topics[name] = body.description
    save_topics(topics)
    return topics


@app.delete("/admin/topics/{name}")
def delete_topic(name: str):
    """Delete a topic by name. Returns updated topics dict."""
    topics = load_topics()
    if name not in topics:
        raise HTTPException(status_code=404, detail=f"Topic '{name}' not found.")
    del topics[name]
    save_topics(topics)
    return topics


# ---------------------------------------------------------------------------
# Admin: corrections management
# ---------------------------------------------------------------------------

@app.get("/admin/corrections")
def get_corrections():
    """List all rows of Review_Corrections, newest first."""
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Review_Corrections ORDER BY Correction_Id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


@app.patch("/admin/corrections/{correction_id}/approval")
def update_correction_approval(correction_id: int, body: ApprovalInput):
    """Set Approved_For_Learning for a given correction, return updated row."""
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Review_Corrections WHERE Correction_Id = ?", (correction_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Correction not found")

    val = 1 if body.approved else 0
    cursor.execute(
        "UPDATE Review_Corrections SET Approved_For_Learning = ? WHERE Correction_Id = ?",
        (val, correction_id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM Review_Corrections WHERE Correction_Id = ?", (correction_id,))
    updated_row = dict(cursor.fetchone())
    conn.close()
    return updated_row


# ---------------------------------------------------------------------------
# Emotion Analysis Endpoints
# ---------------------------------------------------------------------------

class AnalyzeEmotionsRequest(BaseModel):
    force: bool = False


@app.get("/reviews/emotions")
def get_reviews_emotions(
    emotion: Optional[str] = None,
    product: Optional[str] = None,
    platform: Optional[str] = None,
    min_confidence: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Return paginated review-level emotion analysis records with filters."""
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    where_clauses = ["1=1"]
    params = []

    if emotion:
        where_clauses.append("a.Emotion = ?")
        params.append(emotion)
    if product:
        where_clauses.append("r.Product = ?")
        params.append(product)
    if platform:
        where_clauses.append("r.Platform = ?")
        params.append(platform)
    if min_confidence is not None:
        where_clauses.append("a.Emotion_Confidence >= ?")
        params.append(min_confidence)
    if search:
        where_clauses.append("r.Review LIKE ?")
        params.append(f"%{search}%")

    where_str = " AND ".join(where_clauses)

    count_query = f"""
        SELECT count(*) as total
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE {where_str}
    """
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()["total"]

    query = f"""
        SELECT r.Platform, r.Company, r.Product, r.Review, r.Month_Year, r.Platform_Reference_Id,
               a.Rating, a.Tags, a.Confidence,
               a.Emotion, a.Emotion_Confidence, a.Emotion_Scores, a.Emotion_Model, a.Load_timestamp
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE {where_str}
        ORDER BY r.Platform_Reference_Id ASC
        LIMIT ? OFFSET ?
    """
    cursor.execute(query, params + [limit, offset])
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        item = dict(row)
        scores_json = item.get("Emotion_Scores")
        if scores_json and isinstance(scores_json, str):
            try:
                item["Emotion_Scores_Dict"] = json.loads(scores_json)
            except Exception:
                item["Emotion_Scores_Dict"] = {}
        else:
            item["Emotion_Scores_Dict"] = {}
        results.append(item)

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "reviews": results
    }


@app.get("/reviews/emotions/summary")
def get_reviews_emotions_summary():
    """Return counts, percentages, and metadata for business emotions and uncertain predictions."""
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) as total FROM Customer_Reviews_Analysis")
    total_records = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT Emotion, count(*) as cnt 
        FROM Customer_Reviews_Analysis 
        GROUP BY Emotion
    """)
    raw_counts = {row["Emotion"]: row["cnt"] for row in cursor.fetchall()}
    conn.close()

    emotion_counts = {}
    for emo in BUSINESS_EMOTIONS:
        emotion_counts[emo] = raw_counts.get(emo, 0)

    uncertain_count = raw_counts.get("Uncertain", 0)
    unsupported_count = raw_counts.get("language unsupported", 0)
    unanalyzed_count = raw_counts.get(None, 0) + raw_counts.get("", 0)

    # Denominator: all eligible analyzed reviews (6 business emotions + uncertain)
    eligible_analyzed_total = sum(emotion_counts.values()) + uncertain_count

    emotion_percentages = {}
    for emo, count in emotion_counts.items():
        emotion_percentages[emo] = round((count / eligible_analyzed_total * 100), 1) if eligible_analyzed_total > 0 else 0.0

    uncertain_percentage = round((uncertain_count / eligible_analyzed_total * 100), 1) if eligible_analyzed_total > 0 else 0.0

    return {
        "total_reviews": total_records,
        "analyzed_reviews": eligible_analyzed_total,
        "unanalyzed_reviews": unanalyzed_count,
        "unsupported_reviews": unsupported_count,
        "denominator_description": f"Percentages based on {eligible_analyzed_total} eligible analyzed reviews (excluding language unsupported).",
        "emotion_counts": emotion_counts,
        "emotion_percentages": emotion_percentages,
        "uncertain_count": uncertain_count,
        "uncertain_percentage": uncertain_percentage
    }


@app.get("/reviews/emotions/trend")
def get_reviews_emotions_trend():
    """Return emotion counts across months, handling missing dates gracefully."""
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT r.Month_Year, a.Emotion, count(*) as cnt
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE a.Emotion IS NOT NULL AND a.Emotion != '' AND a.Emotion != 'language unsupported'
        GROUP BY r.Month_Year, a.Emotion
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    trend_data = {}
    for row in rows:
        raw_month = row["Month_Year"] or "Unknown"
        emo = row["Emotion"]
        cnt = row["cnt"]

        if raw_month not in trend_data:
            trend_data[raw_month] = {
                "month": raw_month,
                "Anger": 0,
                "Frustration": 0,
                "Disappointment": 0,
                "Anxiety": 0,
                "Confusion": 0,
                "Delight": 0,
                "Uncertain": 0,
                "total": 0
            }

        if emo in trend_data[raw_month]:
            trend_data[raw_month][emo] += cnt
        trend_data[raw_month]["total"] += cnt

    def sort_key(item):
        m_str = item["month"]
        if not m_str or m_str == "Unknown":
            return "9999-99"
        try:
            m, y = m_str.split("-")
            return f"{y}-{m.zfill(2)}"
        except ValueError:
            return m_str

    sorted_trend = sorted(trend_data.values(), key=sort_key)
    return sorted_trend


@app.post("/analyze-emotions")
def analyze_emotions_endpoint(req: Optional[AnalyzeEmotionsRequest] = None):
    """Analyze reviews that do not yet have emotion results or reanalyze on request."""
    force = req.force if req else False
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if force:
        cursor.execute("""
            SELECT r.Platform_Reference_Id, r.Review
            FROM Customer_Reviews r
            JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        """)
    else:
        cursor.execute("""
            SELECT r.Platform_Reference_Id, r.Review
            FROM Customer_Reviews r
            JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
            WHERE a.Emotion IS NULL OR a.Emotion = ''
        """)

    reviews_to_analyze = cursor.fetchall()

    analyzed_count = 0
    skipped_count = 0

    for row in reviews_to_analyze:
        ref_id = row["Platform_Reference_Id"]
        raw_text = row["Review"]

        if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
            cursor.execute("""
                UPDATE Customer_Reviews_Analysis
                SET Emotion = 'language unsupported',
                    Emotion_Confidence = 0,
                    Emotion_Scores = '{}',
                    Emotion_Model = 'skipped (empty text)'
                WHERE Platform_Reference_Id = ?
            """, (ref_id,))
            skipped_count += 1
            continue

        if not is_supported(raw_text):
            cursor.execute("""
                UPDATE Customer_Reviews_Analysis
                SET Emotion = 'language unsupported',
                    Emotion_Confidence = 0,
                    Emotion_Scores = '{}',
                    Emotion_Model = 'skipped (language unsupported)'
                WHERE Platform_Reference_Id = ?
            """, (ref_id,))
            skipped_count += 1
            continue

        cleaned = clean_text(raw_text)
        emotion_res = predict_emotion(cleaned)

        cursor.execute("""
            UPDATE Customer_Reviews_Analysis
            SET Emotion = ?,
                Emotion_Confidence = ?,
                Emotion_Scores = ?,
                Emotion_Model = ?
            WHERE Platform_Reference_Id = ?
        """, (
            emotion_res.get("emotion", "Uncertain"),
            emotion_res.get("confidence", 0),
            json.dumps(emotion_res.get("mapped_scores", {})),
            emotion_res.get("model", ""),
            ref_id
        ))
        analyzed_count += 1

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "total_processed": len(reviews_to_analyze),
        "analyzed": analyzed_count,
        "skipped_unsupported": skipped_count
    }


# ---------------------------------------------------------------------------
# Review detail with correction history
# ---------------------------------------------------------------------------

CORRECTIONS_PATH = "data/corrections_log.csv"


@app.get("/reviews/{platform_reference_id}")
def get_review_detail(platform_reference_id: str):
    """Return full review + analysis data and correction history for a given ID."""
    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.Platform,
            r.Company,
            r.Product,
            r.Review,
            r.Month_Year,
            r.Platform_Reference_Id,
            r.Load_timestamp         AS Review_Load_timestamp,
            a.Rating,
            a.Tags,
            a.Confidence,
            a.Emotion,
            a.Emotion_Confidence,
            a.Emotion_Scores,
            a.Emotion_Model,
            a.Load_timestamp         AS Analysis_Load_timestamp,
            a.Label_Source,
            a.Model_Rating,
            a.Learned_From,
            a.Learned_Similarity
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a
            ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE r.Platform_Reference_Id = ?
    """, (platform_reference_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No review found with Platform_Reference_Id '{platform_reference_id}'."
        )

    review_data = dict(row)
    if review_data.get("Emotion_Scores"):
        try:
            review_data["Emotion_Scores_Dict"] = json.loads(review_data["Emotion_Scores"])
        except Exception:
            review_data["Emotion_Scores_Dict"] = {}
    else:
        review_data["Emotion_Scores_Dict"] = {}

    # Read correction history from CSV
    correction_history = []
    if os.path.exists(CORRECTIONS_PATH):
        with open(CORRECTIONS_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for record in reader:
                if record.get("Platform_Reference_Id") == platform_reference_id:
                    correction_history.append(record)
        # Most recent first
        correction_history.reverse()

    return {
        "review": review_data,
        "correction_history": correction_history,
        "Label_Source": review_data.get("Label_Source"),
        "Model_Rating": review_data.get("Model_Rating"),
        "Learned_From": review_data.get("Learned_From"),
        "Learned_Similarity": review_data.get("Learned_Similarity")
    }


