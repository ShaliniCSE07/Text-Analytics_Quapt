from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import numpy as np

WEAK_STANDALONE_WORDS = {"lot", "took", "bit", "kind", "way", "got", "went", "thing", "things", "stuff"}



def extract_keywords(reviews: list, top_n: int = 5) -> list:
    """
    Extract top keywords/phrases from a list of review strings using TF-IDF.

    TF-IDF naturally downweights terms that appear in almost every review
    (high document frequency → low IDF), so generic words like "phone" or
    "product" surface with low aggregate scores even without an explicit
    blocklist beyond the built-in English stop-words.

    Args:
        reviews: List of review text strings.
        top_n:   Number of top-scoring terms to return (default 5).

    Returns:
        List of {"word": str, "score": float} dicts sorted descending by score,
        or an empty list when there are fewer than 2 reviews.
    """
    if not reviews or len(reviews) < 2:
        return []

    vectorizer = TfidfVectorizer(
        stop_words='english',   # removes basic grammatical filler
        ngram_range=(1, 2),     # single words + two-word phrases
        max_features=100,
        max_df=0.85,            # drop any term present in >85% of docs
    )

    X = vectorizer.fit_transform(reviews)

    # Sum TF-IDF scores across all reviews for each term
    scores = np.asarray(X.sum(axis=0)).flatten()
    vocab = vectorizer.get_feature_names_out()

    # Sort descending and take top_n
    ranked = sorted(
        zip(vocab, scores.tolist()),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        {"word": w, "score": round(s, 2)}
        for w, s in ranked[:top_n]
    ]


def extract_distinctive_keywords(group_reviews: list, other_reviews: list, top_n: int = 5) -> list:
    """
    Extract distinctive keywords for group_reviews compared against other_reviews.

    Args:
        group_reviews: List of review text strings for the target group.
        other_reviews: List of review text strings for the comparison group.
        top_n:         Number of top-scoring distinctive terms to return (default 5).

    Returns:
        List of {"word": str, "score": float} dicts sorted descending by score.
    """
    if not group_reviews or not other_reviews or (len(group_reviews) + len(other_reviews)) < 2:
        return []

    combined = group_reviews + other_reviews
    vectorizer = CountVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        max_features=200
    )

    try:
        vectorizer.fit(combined)
    except ValueError:
        return []

    vocab = vectorizer.get_feature_names_out()
    if len(vocab) == 0:
        return []

    X_group = vectorizer.transform(group_reviews)
    X_other = vectorizer.transform(other_reviews)

    group_word_counts = np.asarray(X_group.sum(axis=0)).flatten()
    other_word_counts = np.asarray(X_other.sum(axis=0)).flatten()

    group_total = group_word_counts.sum()
    other_total = other_word_counts.sum()

    if group_total == 0 or other_total == 0:
        return []

    group_rel_freq = group_word_counts / group_total
    other_rel_freq = other_word_counts / other_total

    distinctiveness = (group_rel_freq + 0.001) / (other_rel_freq + 0.001)

    items = []
    for idx in range(len(vocab)):
        word = vocab[idx]
        count = group_word_counts[idx]
        score = float(distinctiveness[idx])

        min_count = 1 if ' ' in word else 2
        if count >= min_count and score > 3.0:
            if ' ' not in word and word.lower() in WEAK_STANDALONE_WORDS:
                continue
            if ' ' in word:
                score *= 1.5
            items.append((word, score))

    items.sort(key=lambda x: x[1], reverse=True)

    return [
        {"word": w, "score": round(s, 2)}
        for w, s in items[:top_n]
    ]


# ---------------------------------------------------------------------------
# Test block — run with: python -m app.keywords  (from project root)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    group_a = [
        "This phone is great, battery lasts all day.",
        "Phone works well, camera quality is excellent.",
        "Great phone, very happy with the purchase."
    ]
    group_b = [
        "This phone broke within a week, terrible quality.",
        "Phone support was unhelpful and slow to respond.",
        "Disappointed with this phone, poor build quality."
    ]

    res_a = extract_distinctive_keywords(group_a, group_b, top_n=5)
    res_b = extract_distinctive_keywords(group_b, group_a, top_n=5)

    print("Group A distinctive keywords (Positive context):")
    print(res_a)
    print("\nGroup B distinctive keywords (Negative context):")
    print(res_b)

    words_a = [item["word"] for item in res_a]
    words_b = [item["word"] for item in res_b]

    print("\nSanity Check:")
    print(f"'phone' in Group A top 5: {'phone' in words_a}")
    print(f"'phone' in Group B top 5: {'phone' in words_b}")
