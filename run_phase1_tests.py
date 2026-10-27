import json
import sqlite3
import urllib.request
from app.learning import find_learned_label
from app.pipeline import analyze_review

def run_t1():
    print("=" * 80)
    print("TEST T1: UNIT TEST OF find_learned_label (INJECTED MEMORY)")
    print("=" * 80)

    memory = [
        {"id": "M1", "text": "Claim settlement was very slow and I kept waiting.", "label": "Negative"},
        {"id": "M2", "text": "Policy renewal was quick and easy online.", "label": "Positive"},
        {"id": "M3", "text": "Agent explained the policy terms clearly.", "label": "Positive"},
        {"id": "M4", "text": "Agent explained the policy terms clearly to me.", "label": "Negative"}
    ]

    queries = [
        (1, "Claim settlement was extremely slow and I had to keep waiting."),
        (2, "Claim settlement was not slow and I did not have to wait."),
        (3, "Claim settlement was very slow, but the agent was polite."),
        (4, "Renewing my policy online was quick and easy."),
        (5, "The mobile app keeps crashing on login."),
        (6, "The agent explained the policy terms clearly.")
    ]

    for idx, q in queries:
        res = find_learned_label(q, memory=memory)
        print(f"Query {idx}: \"{q}\"")
        print(f"  similarity={res['similarity']}, applied={res['applied']}, label={res['label']}, reason={res['reason']}")
    print()

def run_t2():
    print("=" * 80)
    print("TEST T2: REGRESSION CHECK ON UP TO 50 DATABASE REVIEWS")
    print("=" * 80)

    conn = sqlite3.connect("data/reviews.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.Platform, r.Company, r.Product, r.Review, r.Month_Year, r.Platform_Reference_Id,
               a.Rating, a.Label_Source
        FROM Customer_Reviews r
        JOIN Customer_Reviews_Analysis a ON r.Platform_Reference_Id = a.Platform_Reference_Id
        WHERE a.Label_Source = 'model'
        LIMIT 50
    """)
    rows = cursor.fetchall()
    conn.close()

    total_tested = len(rows)
    differ_count = 0
    diff_details = []

    for r in rows:
        row_dict = dict(r)
        result = analyze_review(row_dict)
        stored_rating = row_dict["Rating"]
        computed_rating = result["Rating"]
        if computed_rating != stored_rating:
            differ_count += 1
            diff_details.append({
                "id": row_dict["Platform_Reference_Id"],
                "stored": stored_rating,
                "computed": computed_rating,
                "text": row_dict["Review"][:50]
            })

    print(f"Total reviews tested: {total_tested}")
    print(f"Differ count: {differ_count}")
    if differ_count > 0:
        print("Differences found:")
        for d in diff_details:
            print(f"  {d}")
    else:
        print("All computed Ratings match stored Ratings for Label_Source='model' (0 differ).")
    print()

def run_t3():
    print("=" * 80)
    print("TEST T3: API ENDPOINT VERIFICATION")
    print("=" * 80)

    # 1. POST /analyze-review
    sample_payload = {
        "Platform": "Google",
        "Company": "Acme Insurance",
        "Product": "Acme Health Shield",
        "Review": "Claim settlement was very fast and seamless. Very happy with the service!"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/analyze-review",
        data=json.dumps(sample_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        post_res = json.loads(resp.read().decode("utf-8"))

    print("POST /analyze-review response:")
    print(json.dumps(post_res, indent=2))
    print(f"Verified new keys in POST response:")
    print(f"  Label_Source      : {post_res.get('Label_Source')}")
    print(f"  Model_Rating      : {post_res.get('Model_Rating')}")
    print(f"  Learned_From      : {post_res.get('Learned_From')}")
    print(f"  Learned_Similarity: {post_res.get('Learned_Similarity')}")
    print()

    # 2. GET /reviews
    req_get = urllib.request.Request("http://127.0.0.1:8000/reviews")
    with urllib.request.urlopen(req_get) as resp:
        reviews_res = json.loads(resp.read().decode("utf-8"))

    sample_row = reviews_res[0] if reviews_res else {}
    print("GET /reviews sample row (first item):")
    print(json.dumps(sample_row, indent=2))
    print(f"Verified new keys in GET /reviews:")
    print(f"  Label_Source      : {sample_row.get('Label_Source')}")
    print(f"  Model_Rating      : {sample_row.get('Model_Rating')}")
    print(f"  Learned_From      : {sample_row.get('Learned_From')}")
    print(f"  Learned_Similarity: {sample_row.get('Learned_Similarity')}")
    print()

if __name__ == "__main__":
    run_t1()
    run_t2()
    run_t3()
