"""
Evaluation Harness
===================
Runs the baseline keyword matcher and the SmartMatch agent on the same
10 evaluation queries (data/eval_queries.json) and scores both against
hand-labeled ground truth.

Primary metric: Top-3 Hit Rate
  - Did at least one of the "expected_producer_ids" appear in the system's
    top-3 results? This reflects what the consumer actually experiences:
    would they find someone genuinely right for their need.

Secondary metric: Wrong-Fit Rate
  - Fraction of returned results that are OUTSIDE the correct category
    OR clearly violate a stated budget (price_min > 2x budget_max).
    This penalizes systems that return technically-in-category but
    badly-mismatched producers (e.g. recommending a Rs. 8000 bridal
    tailor for a Rs. 3000 budget request).

Usage:
  python eval/evaluate.py            # real mode if ANTHROPIC_API_KEY set, else mock
  python eval/evaluate.py --mock     # force mock mode (no API calls, free, offline)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from baseline.keyword_matcher import match as baseline_match
from agent.smart_match_agent import match as agent_match

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_queries():
    with open(DATA_DIR / "eval_queries.json") as f:
        return json.load(f)


def load_producers_by_id():
    with open(DATA_DIR / "producers.json") as f:
        producers = json.load(f)
    return {p["id"]: p for p in producers}


def score_system(name, run_fn, queries, producers_by_id, **run_kwargs):
    rows = []
    hits = 0
    wrong_fit_count = 0
    total_results = 0

    for q in queries:
        out = run_fn(q["query"], **run_kwargs) if run_kwargs else run_fn(q["query"])
        result_ids = [r["id"] for r in out.get("results", [])]

        hit = any(pid in result_ids for pid in q["expected_producer_ids"])
        hits += int(hit)

        wrong_fit = 0
        budget_max = q.get("budget_max")
        for pid in result_ids:
            total_results += 1
            producer = producers_by_id.get(pid)
            if producer is None:
                wrong_fit += 1
                continue
            if producer["category"] != q["expected_category"]:
                wrong_fit += 1
                continue
            # A result is a "wrong fit" if the producer's cheapest offering is still
            # more than double the consumer's stated budget - i.e. obviously unaffordable.
            if budget_max and producer["price_min"] > budget_max * 2:
                wrong_fit += 1
                continue
        wrong_fit_count += wrong_fit

        rows.append({
            "query_id": q["id"],
            "query": q["query"],
            "expected_category": q["expected_category"],
            "expected_ids": q["expected_producer_ids"],
            "returned_ids": result_ids,
            "hit": hit,
        })

    top3_hit_rate = hits / len(queries) if queries else 0
    wrong_fit_rate = wrong_fit_count / total_results if total_results else 0

    return {
        "system": name,
        "top3_hit_rate": round(top3_hit_rate, 3),
        "wrong_fit_rate": round(wrong_fit_rate, 3),
        "n_queries": len(queries),
        "rows": rows,
    }


def main():
    mock = "--mock" in sys.argv
    queries = load_queries()
    producers_by_id = load_producers_by_id()

    baseline_scores = score_system("Baseline (keyword matcher)", baseline_match, queries, producers_by_id)
    agent_scores = score_system("SmartMatch Agent", agent_match, queries, producers_by_id, mock=mock)

    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / "results.json", "w") as f:
        json.dump({"baseline": baseline_scores, "agent": agent_scores}, f, indent=2)

    print("\n=== SmartMatch Evaluation Results ===\n")
    print(f"{'Metric':<28}{'Baseline':<15}{'Agent':<15}{'Change'}")
    print("-" * 70)

    b_hit, a_hit = baseline_scores["top3_hit_rate"], agent_scores["top3_hit_rate"]
    b_wf, a_wf = baseline_scores["wrong_fit_rate"], agent_scores["wrong_fit_rate"]

    print(f"{'Top-3 Hit Rate':<28}{b_hit:<15}{a_hit:<15}{'+' if a_hit >= b_hit else ''}{round(a_hit - b_hit, 3)}")
    print(f"{'Wrong-Fit Rate (lower=better)':<28}{b_wf:<15}{a_wf:<15}{round(a_wf - b_wf, 3)}")

    print("\nPer-query breakdown:\n")
    print(f"{'Query':<6}{'Baseline Hit':<15}{'Agent Hit'}")
    for b_row, a_row in zip(baseline_scores["rows"], agent_scores["rows"]):
        print(f"{b_row['query_id']:<6}{str(b_row['hit']):<15}{str(a_row['hit'])}")

    # write a markdown summary too, ready to paste into the changelog/README
    md_lines = [
        "# Evaluation Results\n",
        f"Mode: {'mock' if mock else 'real (or mock fallback if no API key set)'}\n",
        "| Metric | Baseline | Agent | Change |",
        "|---|---|---|---|",
        f"| Top-3 Hit Rate | {b_hit} | {a_hit} | {'+' if a_hit >= b_hit else ''}{round(a_hit - b_hit, 3)} |",
        f"| Wrong-Fit Rate (lower is better) | {b_wf} | {a_wf} | {round(a_wf - b_wf, 3)} |",
        "",
        "## Per-query breakdown",
        "",
        "| Query ID | Query | Expected Category | Baseline Result IDs | Baseline Hit | Agent Result IDs | Agent Hit |",
        "|---|---|---|---|---|---|---|",
    ]
    for b_row, a_row in zip(baseline_scores["rows"], agent_scores["rows"]):
        md_lines.append(
            f"| {b_row['query_id']} | {b_row['query']} | {b_row['expected_category']} | "
            f"{', '.join(b_row['returned_ids'])} | {b_row['hit']} | "
            f"{', '.join(a_row['returned_ids'])} | {a_row['hit']} |"
        )
    with open(RESULTS_DIR / "results.md", "w") as f:
        f.write("\n".join(md_lines))

    print(f"\nSaved: {RESULTS_DIR / 'results.json'} and {RESULTS_DIR / 'results.md'}")


if __name__ == "__main__":
    main()
