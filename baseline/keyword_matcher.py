"""
Baseline: Simple Keyword Matcher
=================================
This represents the "simple basic way to handle the task before using the
agent solution" — a plain keyword/category search, the way a basic listings
site or manual browsing would work today. No reasoning, no budget
understanding, no disambiguation between similar producers.

Logic:
1. Detect category by looking for a known category word in the query.
2. Return every producer in that category, sorted by price_min ascending.
   (This is what a naive "cheapest first" filter would do — it does NOT
   understand budget constraints, quality needs, or specific requirements.)
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CATEGORY_KEYWORDS = {
    "tailor": ["tailor", "dress", "lehenga", "blouse", "stitch", "outfit", "bridal", "designer"],
    "farmer": ["flower", "flowers", "farm", "vegetable", "marigold", "rose"],
    "developer": ["developer", "app", "project", "web", "coding", "ml", "machine learning", "software"],
    "mechanic": ["mechanic", "bike", "car", "tyre", "battery", "repair", "vehicle"],
    "tutor": ["tutor", "tuition", "mentor", "teach", "learn", "dsa", "placement"],
}


def load_producers():
    with open(DATA_DIR / "producers.json") as f:
        return json.load(f)


def detect_category(query: str):
    query_lower = query.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                scores[cat] += 1
    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        return None
    return best_cat


def match(query: str, top_k: int = 3):
    producers = load_producers()
    category = detect_category(query)
    if category is None:
        return {"category_detected": None, "results": []}

    candidates = [p for p in producers if p["category"] == category]
    candidates.sort(key=lambda p: p["price_min"])  # naive: cheapest first, ignores fit

    results = [
        {
            "id": p["id"],
            "name": p["name"],
            "price_min": p["price_min"],
            "price_max": p["price_max"],
            "reason": "Matched by category keyword only; sorted by lowest starting price. No budget, quality, or requirement check.",
        }
        for p in candidates[:top_k]
    ]
    return {"category_detected": category, "results": results}


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "I need a tailor for a party dress"
    print(json.dumps(match(q), indent=2))
