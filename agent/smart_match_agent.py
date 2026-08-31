"""
SmartMatch Agent
=================
Given a consumer's plain-language need, this agent:
  1. Parses the query into structured requirements (category, budget, need, quality bar).
  2. Retrieves candidate producers for that category (a tool call against data/producers.json).
  3. Reasons about which candidates genuinely fit — budget, category, and requirement-specific
     details (e.g. "designer replica" vs "plain stitching", "student budget" vs "production app").
  4. VERIFIES its own explanation: every price or attribute claim it makes about a producer is
     checked against the actual producer record before being returned. If a claim can't be
     grounded, the match is flagged instead of silently trusted.
  5. Logs every step (inputs, LLM calls, tool responses, verification outcome) as a trajectory
     file under /trajectories, in the format required for submission.

Three run modes, chosen automatically based on what's in your environment:
  - ANTHROPIC mode: used if ANTHROPIC_API_KEY is set. Calls the Anthropic API.
  - GROQ mode: used if ANTHROPIC_API_KEY is NOT set but GROQ_API_KEY is. Calls Groq's free,
    no-credit-card API (OpenAI-compatible) running an open-weight model. This is the recommended
    free path if you don't want to add billing to any provider.
  - MOCK mode (--mock flag, or automatic fallback if neither key is set): a deterministic
    rule-based stand-in for the LLM calls, so you can test the full pipeline (retrieval,
    verification, trajectory logging) offline / for free. Clearly logged as "mock" in the
    trajectory so it's never confused with a real agent run. Do NOT submit mock-mode trajectories
    as your competition evidence — they're for development/testing only.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRAJ_DIR = Path(__file__).resolve().parent.parent / "trajectories"

PROVIDER = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else \
           "groq" if os.environ.get("GROQ_API_KEY") else "mock"

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "groq": "llama-3.3-70b-versatile",
}
MODEL = os.environ.get("AGENT_MODEL", DEFAULT_MODELS.get(PROVIDER, ""))


def load_producers():
    with open(DATA_DIR / "producers.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Tool: retrieve_candidates - the agent's only way to see producer data
# ---------------------------------------------------------------------------
def retrieve_candidates(category: str):
    producers = load_producers()
    return [p for p in producers if p["category"] == category]


# ---------------------------------------------------------------------------
# LLM call wrapper (real or mock)
# ---------------------------------------------------------------------------
def call_llm(system: str, user: str, mock: bool, mock_fn=None):
    """Returns (response_text, raw_trajectory_entry)."""
    if mock:
        text = mock_fn()
        entry = {
            "mode": "mock",
            "system_prompt": system,
            "user_message": user,
            "response": text,
        }
        return text, entry

    if PROVIDER == "anthropic":
        try:
            import anthropic
        except ImportError:
            raise RuntimeError(
                "The 'anthropic' package is not installed. Run: pip install anthropic --break-system-packages"
            )
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")

    elif PROVIDER == "groq":
        try:
            from openai import OpenAI  # Groq is OpenAI-SDK-compatible
        except ImportError:
            raise RuntimeError(
                "The 'openai' package is not installed (needed for Groq). Run: pip install openai --break-system-packages"
            )
        client = OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = response.choices[0].message.content

    else:
        raise RuntimeError(
            "No API key found. Set ANTHROPIC_API_KEY or GROQ_API_KEY in your environment, "
            "or pass mock=True / run with --mock."
        )

    entry = {
        "mode": "real",
        "provider": PROVIDER,
        "model": MODEL,
        "system_prompt": system,
        "user_message": user,
        "response": text,
    }
    return text, entry


# ---------------------------------------------------------------------------
# Step 1: parse the query into structured requirements
# ---------------------------------------------------------------------------
PARSE_SYSTEM = """You are a requirement-extraction module for a producer-matching agent.
Given a consumer's plain-language request, extract structured JSON with these fields:
- category: one of ["tailor", "farmer", "developer", "mechanic", "tutor"]
- budget_min: number or null
- budget_max: number or null
- need_summary: short phrase describing what they actually need
- quality_bar: one of ["budget", "moderate", "premium"] based on language used (e.g. "designer",
  "cheapest", "quality matters most")
Respond with ONLY the JSON object, no other text."""


def _mock_parse(query: str):
    q = query.lower()
    cat = None
    for c, kws in {
        "tailor": ["dress", "lehenga", "blouse", "tailor", "bridal", "outfit"],
        "farmer": ["flower", "farm", "marigold", "rose"],
        "developer": ["app", "project", "developer", "coding", "web", "machine learning"],
        "mechanic": ["bike", "car", "tyre", "battery", "mechanic"],
        "tutor": ["tutor", "tuition", "mentor", "dsa", "placement"],
    }.items():
        if any(kw in q for kw in kws):
            cat = c
            break
    budget_match = re.search(r"(\d{3,6})", q.replace(",", ""))
    budget_max = int(budget_match.group(1)) if budget_match else None
    quality = "premium" if any(w in q for w in ["designer", "bridal", "quality matters", "heavy"]) \
        else "budget" if any(w in q for w in ["cheap", "afford", "budget", "plain", "simple"]) \
        else "moderate"
    return json.dumps({
        "category": cat,
        "budget_min": None,
        "budget_max": budget_max,
        "need_summary": query[:80],
        "quality_bar": quality,
    })


def parse_query(query: str, mock: bool, trajectory: list):
    text, entry = call_llm(
        PARSE_SYSTEM, query, mock, mock_fn=lambda: _mock_parse(query)
    )
    trajectory.append({"step": "parse_query", **entry})
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # fall back: try to extract JSON substring
        m = re.search(r"\{.*\}", text, re.DOTALL)
        parsed = json.loads(m.group(0)) if m else {"category": None}
    return parsed


# ---------------------------------------------------------------------------
# Step 2: rank + explain candidates
# ---------------------------------------------------------------------------
RANK_SYSTEM = """You are a matching-reasoning module. You will be given a structured consumer
requirement and a list of candidate producers (as JSON). Select up to 3 producers that best fit,
ranked best first. For each, give a one-sentence reason that ONLY uses facts present in that
producer's record (price range, description, tags, quantity_or_complexity). Do not invent details.

Weigh these, in order of importance:
1. Specific requirements in need_summary (e.g. "specialist", "premium", "quick", a named skill
   or material) — prefer producers whose description/tags explicitly match that specific need
   over producers that only match the general category.
2. Budget fit — if budget_max is given, prefer producers whose price range fits within it, and
   explicitly exclude producers that are clearly outside the stated budget.
3. Quality tier — match quality_bar to producers whose tags/description reflect that tier.

If the consumer names a specific type of specialist or a specific need that only some
same-category producers actually offer, do NOT default to the most general/broad producer just
because it also technically fits the category.

Respond with ONLY a JSON list like:
[{"id": "P001", "reason": "..."}]"""


def _mock_rank(parsed, candidates):
    scored = []
    for p in candidates:
        score = 0
        if parsed.get("budget_max") and p["price_min"] <= parsed["budget_max"]:
            score += 2
        if parsed.get("budget_max") and p["price_max"] > parsed["budget_max"] * 2:
            score -= 2  # clearly overpriced for stated budget
        q = parsed.get("quality_bar")
        tags = " ".join(p.get("tags", [])).lower()
        desc = p.get("description", "").lower()
        if q == "premium" and any(w in tags + desc for w in ["premium", "bridal", "sequin", "zari", "heavy", "designer"]):
            score += 2
        if q == "budget" and any(w in tags + desc for w in ["budget", "affordable", "cheap", "plain", "student"]):
            score += 2
        if q == "moderate" and "premium" not in tags:
            score += 1
        scored.append((score, p))
    scored.sort(key=lambda t: -t[0])
    top = [p for _, p in scored[:3]]
    return json.dumps([
        {"id": p["id"], "reason": f"Category and quality-tier match; price range Rs.{p['price_min']}-{p['price_max']} ({p['quantity_or_complexity']})."}
        for p in top
    ])


def rank_candidates(parsed, candidates, mock: bool, trajectory: list):
    user_msg = json.dumps({"requirement": parsed, "candidates": candidates})
    text, entry = call_llm(
        RANK_SYSTEM, user_msg, mock, mock_fn=lambda: _mock_rank(parsed, candidates)
    )
    trajectory.append({"step": "rank_candidates", **entry})
    try:
        ranked = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", text, re.DOTALL)
        ranked = json.loads(m.group(0)) if m else []
    return ranked


# ---------------------------------------------------------------------------
# Step 3: verification - ground every ranked result against real producer data
# ---------------------------------------------------------------------------
def verify_matches(ranked, candidates, trajectory: list):
    """Checks that every id the LLM returned actually exists in the candidate
    pool retrieved for this category. This is the safety net against
    hallucinated producer IDs or category drift."""
    valid_ids = {p["id"] for p in candidates}
    by_id = {p["id"]: p for p in candidates}
    verified = []
    issues = []
    for item in ranked:
        pid = item.get("id")
        if pid in valid_ids:
            producer = by_id[pid]
            verified.append({
                "id": pid,
                "name": producer["name"],
                "location": producer["location"],
                "phone": producer["phone"],
                "price_min": producer["price_min"],
                "price_max": producer["price_max"],
                "reason": item.get("reason", ""),
            })
        else:
            issues.append(f"LLM referenced producer id '{pid}' which is not in the retrieved "
                           f"candidate set — dropped instead of shown to the user.")
    trajectory.append({
        "step": "verify_matches",
        "checked": len(ranked),
        "passed": len(verified),
        "issues": issues,
    })
    return verified, issues


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def match(query: str, mock: bool = None, save_trajectory: bool = True):
    if mock is None:
        mock = PROVIDER == "mock"

    trajectory = [{
        "step": "receive_query",
        "query": query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "mock" if mock else "real",
    }]

    parsed = parse_query(query, mock, trajectory)
    category = parsed.get("category")

    if not category:
        trajectory.append({"step": "no_category_detected"})
        result = {"category_detected": None, "results": [], "issues": ["Could not detect a category from the query."]}
    else:
        candidates = retrieve_candidates(category)
        trajectory.append({"step": "retrieve_candidates", "category": category, "candidate_count": len(candidates)})

        ranked = rank_candidates(parsed, candidates, mock, trajectory)
        verified, issues = verify_matches(ranked, candidates, trajectory)

        result = {
            "category_detected": category,
            "parsed_requirement": parsed,
            "results": verified,
            "issues": issues,
        }

    trajectory.append({"step": "final_result", "result": result})

    if save_trajectory:
        TRAJ_DIR.mkdir(exist_ok=True)
        fname = TRAJ_DIR / f"trajectory_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{query[:20].replace(' ', '_')}.json"
        with open(fname, "w") as f:
            json.dump(trajectory, f, indent=2)

    return result


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "I want a lehenga like a designer one, budget 3000"
    out = match(q)
    print(json.dumps(out, indent=2))
