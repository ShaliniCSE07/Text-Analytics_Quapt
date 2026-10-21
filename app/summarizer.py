from collections import Counter
import re
from typing import Optional, List, Tuple

# ---------------------------------------------------------------------------
# Topic Aspect Mapping  (internal DB tag -> natural-language phrase)
# ---------------------------------------------------------------------------

TOPIC_ASPECT_MAP = {
    "Claims - Settlement Speed":            "prompt claim settlement and payout speed",
    "Claims - Rejection and Disputes":      "unexpected claim rejections and disputed settlements",
    "Claims - Documentation":               "cumbersome documentation and paperwork requirements",
    "Claims - Intimation and Tracking":     "claim registration and status tracking",
    "Claims - Cashless and Network Providers": "network hospital and garage cashless facilities",
    "Claims - Reimbursement":               "reimbursement claim processing and medical bill settlements",
    "Claims - Surveyor and Damage Assessment": "surveyor damage inspections and repair estimates",
    "Onboarding - Digital Purchase and KYC": "the online purchase flow and KYC verification",
    "Onboarding - Underwriting and Medical Tests": "pre-policy medical underwriting checkups",
    "Onboarding - Mis-selling and Transparency": "transparency during policy sales and clear disclosures",
    "Onboarding - Quotes and Plan Selection": "plan options and premium quotations",
    "Premium - Affordability and Value":    "competitive premium pricing and value for money",
    "Premium - Renewal Hike":               "steep renewal premium price increases",
    "Premium - Payment and Auto-debit":     "auto-debit errors and payment gateway issues",
    "Premium - Refunds and Cancellation":   "policy cancellations and refund timelines",
    "Servicing - Policy Renewal":           "seamless policy renewal continuity",
    "Servicing - Endorsements and Changes": "policy endorsements and profile update requests",
    "Servicing - Policy Documents":         "quick access to policy certificates and documents",
    "Service - Agent and Advisor Conduct":  "advisor courtesy and relationship manager assistance",
    "Service - Call Centre and Support":    "customer support responsiveness and helpline assistance",
    "Service - Grievance and Escalation":   "formal grievance handling and escalation resolution",
    "Service - Branch Experience":          "in-person branch office service",
    "Digital - App and Login":              "mobile application usability and navigation",
    "Digital - Website and Portal":         "website portal access and self-service features",
    "Digital - Notifications and Communication": "communication alerts and notification frequency",
    "Coverage - Clarity and Exclusions":    "clarity around policy exclusions and limits",
    "Coverage - Waiting Periods and Pre-existing": "waiting periods for pre-existing illnesses",
    "Coverage - Benefits and Add-ons":      "valuable add-on riders and coverage benefits",
    "Life - Maturity and Surrender":        "maturity benefit returns and policy surrender",
    "Travel - Trip Disruption and Assistance": "trip disruption compensation and travel assistance",
    "Home - Property Damage and Repairs":   "property damage claims and repair settlements",
}

# ---------------------------------------------------------------------------
# Keyword-based theme extraction (fallback when DB tags are sparse/absent)
# Tuple: (theme_label, is_positive_signal, [keywords_to_match_in_text])
# ---------------------------------------------------------------------------

_KEYWORD_THEMES = [
    ("prompt claim settlement",     True,  ["settled quickly", "fast claim", "quick settlement",
                                             "claim approved fast", "speedy settlement", "instant claim",
                                             "payout quickly", "settled fast", "rapid settlement"]),
    ("helpful customer support",    True,  ["supportive team", "helpful staff", "polite agent",
                                             "excellent service", "great support", "responsive team",
                                             "amazing customer care", "quick response", "cooperative",
                                             "friendly staff", "good service", "best service", "courteous"]),
    ("easy digital experience",     True,  ["easy app", "smooth process", "user friendly", "simple process",
                                             "seamless", "convenient", "easy to use", "quick process",
                                             "app works well", "website easy", "hassle free"]),
    ("affordable premium",          True,  ["affordable", "reasonable premium", "value for money",
                                             "cost effective", "good value", "pocket friendly",
                                             "competitive price", "cheap premium", "fair pricing"]),
    ("good coverage and benefits",  True,  ["good coverage", "comprehensive coverage", "wide coverage",
                                             "excellent benefits", "good plan", "extensive coverage",
                                             "solid cover", "strong benefits", "broad coverage"]),
    ("smooth renewal process",      True,  ["renewal smooth", "easy renewal", "renewed easily",
                                             "renewal process simple", "seamless renewal"]),
    ("transparent and honest",      True,  ["transparent", "clear terms", "no hidden charges",
                                             "clear policy", "honest", "upfront", "no hidden fees",
                                             "clear communication", "straightforward"]),
    ("delayed claim settlement",    False, ["claim delayed", "waiting for claim", "long delay",
                                             "claim taking too long", "delayed settlement", "no response on claim",
                                             "months for claim", "pending claim", "claim not settled",
                                             "settlement delayed", "claim still pending"]),
    ("claim rejection issues",      False, ["claim rejected", "claim denied", "unfairly rejected",
                                             "claim repudiated", "rejection without reason",
                                             "claim not approved", "spurious rejection"]),
    ("poor customer support",       False, ["rude staff", "no response", "not helpful", "bad service",
                                             "poor support", "worst service", "support pathetic",
                                             "helpline useless", "no one responds", "customer care bad",
                                             "unprofessional", "ignored", "not reachable", "no callback"]),
    ("high or rising premium cost", False, ["expensive", "premium too high", "costly premium", "overpriced",
                                             "exorbitant premium", "steep price", "premium increased",
                                             "renewal hike", "premium hiked", "very costly", "premium raised"]),
    ("documentation burden",        False, ["too many documents", "repeated documents", "unnecessary paperwork",
                                             "asking for documents again", "documentation hassle",
                                             "excessive paperwork"]),
    ("app and portal issues",       False, ["app crash", "website not working", "portal error", "login issue",
                                             "app glitch", "portal down", "website slow", "technical issue",
                                             "app not working", "portal not loading"]),
    ("coverage exclusion concerns", False, ["not covered", "exclusion", "treatment not covered",
                                             "co-payment issue", "room rent limit", "sub-limit",
                                             "hidden exclusion", "waiting period too long"]),
    ("mis-selling and false promises", False, ["mis-sold", "false promise", "agent lied", "misled",
                                               "cheated", "wrong information given", "not told about",
                                               "hidden terms", "deceived by agent"]),
]


def _extract_keyword_themes(reviews: list):
    """Scan raw review text for known keyword clusters.
    Returns (pos_theme_counter, neg_theme_counter).
    """
    pos_kw: Counter = Counter()
    neg_kw: Counter = Counter()
    for r in reviews:
        text = (r.get("Review", "") if isinstance(r, dict) else str(r)).lower()
        if not text.strip():
            continue
        for theme_label, is_pos, keywords in _KEYWORD_THEMES:
            if any(kw in text for kw in keywords):
                if is_pos:
                    pos_kw[theme_label] += 1
                else:
                    neg_kw[theme_label] += 1
    return pos_kw, neg_kw


def clean_topic_name(tag: str) -> str:
    """Map topic tag to human-readable phrase, or normalize hierarchy."""
    if tag in TOPIC_ASPECT_MAP:
        return TOPIC_ASPECT_MAP[tag]
    if " - " in tag:
        return tag.split(" - ", 1)[1].lower()
    return tag.lower().strip()


def format_aspect_list(aspects: List[str]) -> str:
    """Format a list of strings into natural English (A, B, and C)."""
    aspects = [a for a in aspects if a]
    if not aspects:
        return "general product features"
    if len(aspects) == 1:
        return aspects[0]
    if len(aspects) == 2:
        return f"{aspects[0]} and {aspects[1]}"
    return ", ".join(aspects[:-1]) + ", and " + aspects[-1]


def extract_collective_themes(reviews: list) -> dict:
    """
    Parses and aggregates all reviews collectively to discover:
    - Sentiment distribution (Positive, Negative, Neutral)
    - Dominant positive themes
    - Dominant negative themes
    - Conflicting themes (significant presence in both positive and negative camps)
    - Secondary notable complaints

    Evidence comes from two sources:
    1. Structured topic Tags from the DB pipeline (weighted 2x, higher confidence).
    2. Keyword scanning of raw review text (weighted 1x, fallback for untagged reviews).
    This ensures every review contributes to the summary regardless of whether it
    has DB tags assigned.
    """
    pos_reviews = []
    neg_reviews = []
    neu_reviews = []

    pos_tag_topics: Counter = Counter()
    neg_tag_topics: Counter = Counter()
    all_tag_topics: Counter = Counter()
    tagged_count = 0

    for r in reviews:
        if isinstance(r, dict):
            text = r.get("Review", "").strip()
            rating = r.get("Rating", "")
            tags_str = r.get("Tags", "")
        else:
            text = str(r).strip()
            rating = ""
            tags_str = ""

        if not text:
            continue

        tags = [
            t.strip()
            for t in tags_str.split("|")
            if t.strip() and t.strip().lower() not in ("uncategorised", "")
        ] if tags_str else []

        if tags:
            tagged_count += 1
            for t in tags:
                all_tag_topics[t] += 1

        # Infer rating direction if Rating field is missing/empty
        if not rating:
            text_lower = text.lower()
            if any(w in text_lower for w in ["great", "excellent", "loved", "smooth", "happy",
                                              "fast", "best", "quick", "amazing", "perfect",
                                              "fantastic", "outstanding", "superb"]):
                rating = "Positive"
            elif any(w in text_lower for w in ["terrible", "bad", "worst", "delay", "rejected",
                                                "failed", "rude", "poor", "horrible", "useless",
                                                "pathetic", "disgusting", "awful"]):
                rating = "Negative"
            else:
                rating = "Neutral"

        r_dict = r if isinstance(r, dict) else {"Review": text}

        if rating == "Positive":
            pos_reviews.append(r_dict)
            for t in tags:
                pos_tag_topics[t] += 1
        elif rating == "Negative":
            neg_reviews.append(r_dict)
            for t in tags:
                neg_tag_topics[t] += 1
        else:
            neu_reviews.append(r_dict)

    # Keyword-based evidence (enriches or back-fills where tags are sparse)
    all_for_kw = reviews if (reviews and isinstance(reviews[0], dict)) else [{"Review": str(r)} for r in reviews]
    pos_kw, neg_kw = _extract_keyword_themes(all_for_kw)

    # Merge: tag hits weighted 2x, keyword hits weighted 1x
    pos_merged: Counter = Counter()
    neg_merged: Counter = Counter()
    all_merged: Counter = Counter()

    for t, cnt in pos_tag_topics.items():
        pos_merged[clean_topic_name(t)] += cnt * 2
    for t, cnt in neg_tag_topics.items():
        neg_merged[clean_topic_name(t)] += cnt * 2
    for theme, cnt in pos_kw.items():
        pos_merged[theme] += cnt
    for theme, cnt in neg_kw.items():
        neg_merged[theme] += cnt
    for t, cnt in all_tag_topics.items():
        all_merged[clean_topic_name(t)] += cnt * 2
    for theme, cnt in {**pos_kw, **neg_kw}.items():
        all_merged[theme] += 1

    # Conflicting aspects: significant positive AND negative presence
    conflicting = []
    for theme, p_cnt in pos_merged.items():
        n_cnt = neg_merged.get(theme, 0)
        if p_cnt >= 3 and n_cnt >= 3:
            conflicting.append(theme)

    total_valid = len(pos_reviews) + len(neg_reviews) + len(neu_reviews)

    return {
        "pos_count":             len(pos_reviews),
        "neg_count":             len(neg_reviews),
        "neu_count":             len(neu_reviews),
        "total_valid":           total_valid,
        "top_pos_aspects":       [t for t, _ in pos_merged.most_common(4)],
        "top_neg_aspects":       [t for t, _ in neg_merged.most_common(4)],
        "secondary_neg_aspects": [t for t, _ in neg_merged.most_common(6)[4:6]],
        "conflicting_aspects":   conflicting,
        "all_top_aspects":       [t for t, _ in all_merged.most_common(4)],
        "has_tags":              tagged_count > 0,
    }


def synthesize_thematic_narrative(
    themes: dict,
    product_name: Optional[str] = None,
    filter_rating: Optional[str] = None
) -> str:
    """
    Synthesizes collective themes into one coherent natural-language paragraph
    of approximately 3-6 sentences, rigorously grounded in actual review data.
    """
    total = themes["total_valid"]
    if total < 2:
        return "The available feedback is insufficient for a reliable conclusion."

    prod_label    = product_name if product_name else "the reviewed products"
    top_pos       = themes["top_pos_aspects"]
    top_neg       = themes["top_neg_aspects"]
    conflicting   = themes["conflicting_aspects"]
    secondary_neg = themes["secondary_neg_aspects"]
    pos_count     = themes["pos_count"]
    neg_count     = themes["neg_count"]
    neu_count     = themes["neu_count"]

    sentences = []

    # Scenario A: Filtered by Positive Rating
    if filter_rating == "Positive":
        if not top_pos:
            return (f"Positive reviews for {prod_label} are favorable overall, "
                    "though specific recurring themes could not be identified from the available data.")
        pos_aspects = format_aspect_list(top_pos[:2])
        sentences.append(
            f"Customers who rated {prod_label} positively most frequently commend {pos_aspects}."
        )
        if len(top_pos) >= 3:
            sentences.append(f"Reviewers also frequently highlight positive experiences with {top_pos[2]}.")
        sentences.append(
            f"Across {pos_count} positive reviews, the feedback consistently emphasises "
            "reliable service execution and high satisfaction with core product functionality."
        )

    # Scenario B: Filtered by Negative Rating
    elif filter_rating == "Negative":
        if not top_neg:
            return (f"Negative reviews for {prod_label} reflect dissatisfaction overall, "
                    "though specific recurring complaints could not be identified from the available data.")
        neg_aspects = format_aspect_list(top_neg[:2])
        sentences.append(
            f"Across {neg_count} negative reviews, customers of {prod_label} predominantly cite "
            f"recurring dissatisfaction with {neg_aspects}."
        )
        if len(top_neg) >= 3:
            sentences.append(f"Complaints also frequently extend to {top_neg[2]}.")
        if secondary_neg:
            sentences.append(
                f"Additional grievances mention {format_aspect_list(secondary_neg[:2])}."
            )
        sentences.append(
            "Overall, the negative feedback suggests that operational friction and unresolved "
            "service gaps remain the primary drivers of customer dissatisfaction."
        )

    # Scenario C: Filtered by Neutral Rating
    elif filter_rating == "Neutral":
        neutral_aspects = format_aspect_list(themes["all_top_aspects"][:2]) \
                          if themes["all_top_aspects"] else "routine policy interactions"
        sentences.append(
            f"Neutral reviews for {prod_label} reflect measured experiences without pronounced "
            "praise or serious complaints."
        )
        sentences.append(
            f"Reviewers typically discuss everyday interactions around {neutral_aspects}, "
            "indicating acceptable but unremarkable service delivery."
        )
        sentences.append(
            "Overall, neutral feedback suggests meaningful opportunities to strengthen the "
            "customer experience and convert indifferent customers into advocates."
        )

    # Scenario D: Unfiltered -- cross-rating collective feedback
    else:
        pos_ratio = pos_count / total
        neg_ratio = neg_count / total

        # Opening with count context
        neu_part = f", and {neu_count} neutral" if neu_count > 0 else ""
        count_context = f"Based on {total} reviews -- {pos_count} positive, {neg_count} negative{neu_part} --"

        # Predominantly positive (>=65%)
        if pos_ratio >= 0.65:
            pos_aspects = format_aspect_list(top_pos[:2]) if top_pos else "overall product performance"
            sentences.append(
                f"{count_context} customer sentiment for {prod_label} is predominantly positive, "
                f"with recurring appreciation for {pos_aspects}."
            )
            if len(top_pos) >= 3:
                sentences.append(f"Policyholders also frequently praise {top_pos[2]}.")
            if top_neg:
                neg_aspects = format_aspect_list(top_neg[:2])
                sentences.append(
                    f"Despite the largely positive reception, a minority of customers raise "
                    f"concerns about {neg_aspects}."
                )
            sentences.append(
                "Overall, customer feedback is strongly favorable regarding product functionality "
                "and service quality, with only isolated criticism."
            )

        # Predominantly negative (>=65%)
        elif neg_ratio >= 0.65:
            neg_aspects = format_aspect_list(top_neg[:2]) if top_neg else "core service issues"
            sentences.append(
                f"{count_context} customer sentiment for {prod_label} is predominantly critical, "
                f"with widespread and recurring dissatisfaction regarding {neg_aspects}."
            )
            if len(top_neg) >= 3:
                sentences.append(f"Complaints frequently extend to {top_neg[2]} as well.")
            if secondary_neg:
                sentences.append(
                    f"Additional grievances include {format_aspect_list(secondary_neg[:2])}."
                )
            if top_pos:
                pos_aspects = format_aspect_list(top_pos[:2])
                sentences.append(
                    f"Despite these concerns, a subset of customers do report satisfactory "
                    f"experiences with {pos_aspects}."
                )
            sentences.append(
                "Overall, substantial improvements in service reliability and responsiveness are "
                "required to address the persistent customer dissatisfaction evident in the data."
            )

        # Mixed / divided sentiment
        else:
            sentences.append(
                f"{count_context} customer feedback for {prod_label} reflects a divided picture "
                "across key service dimensions."
            )
            if top_pos:
                pos_aspects = format_aspect_list(top_pos[:2])
                sentences.append(f"On the positive side, customers frequently commend {pos_aspects}.")
            if top_neg:
                neg_aspects = format_aspect_list(top_neg[:2])
                sentences.append(f"Conversely, prominent sources of dissatisfaction centre on {neg_aspects}.")
            if conflicting:
                conf = conflicting[0]
                sentences.append(
                    f"Customer experiences with {conf} are notably divided, with some reporting "
                    "prompt resolution while others describe persistent frustration."
                )
            elif secondary_neg:
                sentences.append(
                    f"Secondary concerns also highlight {format_aspect_list(secondary_neg[:2])}."
                )
            if top_pos and top_neg:
                p_core = top_pos[0]
                n_core = top_neg[0]
                sentences.append(
                    f"Overall, while {prod_label} earns consistent recognition for {p_core}, "
                    f"{n_core} emerges as the most critical area requiring focused improvement."
                )
            else:
                sentences.append(
                    "Overall, the feedback reflects a mixed customer experience with both "
                    "strengths and meaningful opportunities for improvement."
                )

    return " ".join(sentences)


def generate_summary(
    reviews: list,
    max_reviews: int = 2000,
    product_name: Optional[str] = None,
    filter_rating: Optional[str] = None
) -> str:
    """
    Generates a genuine, insight-based summary synthesizing overall customer feedback.

    Pipeline:
    1. All relevant reviews are used (up to max_reviews) -- never a random subset.
    2. extract_collective_themes() aggregates tag-based evidence (weighted 2x) and
       keyword-based evidence (weighted 1x) across ALL reviews to identify dominant
       positive/negative themes and conflicting opinions.
    3. synthesize_thematic_narrative() converts those findings into a coherent 3-6
       sentence paragraph fully grounded in actual review data.

    Note: BART abstractive refinement has been intentionally removed. Running BART
    over an already-synthesized paragraph adds no grounding value and routinely
    degrades the specificity and accuracy of the output. The thematic synthesis
    already produces proper natural-language prose directly from the evidence.
    """
    if not reviews or len(reviews) < 2:
        return "The available feedback is insufficient for a reliable conclusion."

    selected_reviews = reviews[:max_reviews]
    themes = extract_collective_themes(selected_reviews)

    if themes["total_valid"] < 2:
        return "The available feedback is insufficient for a reliable conclusion."

    return synthesize_thematic_narrative(
        themes=themes,
        product_name=product_name,
        filter_rating=filter_rating,
    )
