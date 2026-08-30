from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app.pipeline import analyze_review
from app.summarizer import generate_summary
from app.keywords import extract_keywords, extract_distinctive_keywords
from app.topics_config import load_topics, save_topics
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
        
    conn = sqlite3.connect("data/reviews.db")
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if correction.Corrected_Rating is not None:
        updates.append("Rating = ?")
        params.append(correction.Corrected_Rating)
        
    if correction.Corrected_Tags is not None:
        updates.append("Tags = ?")
        params.append(correction.Corrected_Tags)
        
    applied = False
    if updates:
        query = f"UPDATE Customer_Reviews_Analysis SET {', '.join(updates)} WHERE Platform_Reference_Id = ?"
        params.append(correction.Platform_Reference_Id)
        cursor.execute(query, params)
        if cursor.rowcount > 0:
            applied = True
        conn.commit()
        
    conn.close()
    
    response_data = dict(correction_data)
    response_data["applied_to_analysis_table"] = applied
    
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
        SELECT r.Platform, r.Company, r.Product, r.Review, r.Platform_Reference_Id, 
               a.Rating, a.Tags, a.Load_timestamp
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
    
    query = """
        SELECT r.Review
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE 1=1
    """
    params = []
    
    if product:
        query += " AND r.Product = ?"
        params.append(product)
    if rating:
        query += " AND a.Rating = ?"
        params.append(rating)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    reviews_list = [row["Review"] for row in rows if row["Review"]]
    
    summary = generate_summary(reviews_list)
    
    return {
        "summary": summary,
        "based_on_reviews": len(reviews_list)
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
# PART 2 — Review detail with correction history
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
            a.Load_timestamp         AS Analysis_Load_timestamp
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
        "correction_history": correction_history
    }
