# Reproduction Guide

Written for someone starting from a clean environment.

## 1. Requirements

- Python 3.9+
- pip
- (For real-mode agent runs) either:
  - an Anthropic API key — https://console.anthropic.com (requires billing after the initial
    trial credit), or
  - a **Groq API key** (recommended free option, no credit card required) —
    https://console.groq.com/keys

Approximate cost/runtime for real mode: 10 evaluation queries x 2 LLM calls
each (parse + rank) = ~20 short API calls, using small prompts (~200-500
tokens each). This is a small fraction of a dollar on current API pricing
and takes well under a minute of wall-clock time (network latency
dominates). Mock mode is free and instant.

## 2. Setup

```bash
# from the project root (the folder containing README.md)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt --break-system-packages
```

Set **one** of the following for real-mode agent runs (recommended for your
actual submission evidence). The agent checks for Anthropic's key first,
then Groq's, then falls back to mock mode if neither is set.

```bash
# Option A: Anthropic (billed after trial credit runs out)
export ANTHROPIC_API_KEY="your-key-here"     # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key-here"

# Option B: Groq (free, no credit card)
export GROQ_API_KEY="your-key-here"          # Windows PowerShell: $env:GROQ_API_KEY="your-key-here"
```

If neither is set, the agent automatically falls back to mock mode
(rule-based, no API calls) so you can still test the full pipeline.

## 3. Run the baseline alone

```bash
python3 baseline/keyword_matcher.py "I need a tailor for a party dress under 3000"
```

Expected: a JSON object with `category_detected` and up to 3 producers
sorted by lowest starting price, each with a generic "matched by category
keyword" reason.

## 4. Run the agent alone

```bash
# real mode (needs ANTHROPIC_API_KEY or GROQ_API_KEY set)
python3 agent/smart_match_agent.py "I want a lehenga like a designer one, budget 3000"

# explicit mock mode (no API key needed)
python3 -c "from agent.smart_match_agent import match; import json; print(json.dumps(match('I want a lehenga like a designer one, budget 3000', mock=True), indent=2))"
```

Expected: a JSON object with the parsed requirement, verified results (each
with a grounded reason referencing real producer fields), and any
verification issues. A trajectory file is written to `trajectories/`.

## 5. Run the full evaluation (baseline vs agent, both on the same 10 queries)

```bash
python3 eval/evaluate.py            # real mode if ANTHROPIC_API_KEY or GROQ_API_KEY is set, else mock
python3 eval/evaluate.py --mock     # force mock mode
```

Expected output: a printed comparison table (Top-3 Hit Rate, Wrong-Fit
Rate) plus a per-query breakdown, and two files written to
`eval/results/`: `results.json` (full detail) and `results.md`
(paste-ready markdown table).

## 6. What "good" output looks like

- Baseline: correctly detects category, but sorts purely by price and
  cannot distinguish "cheapest" from "best fit" — e.g. it may recommend
  a plain-stitching tailor for a request that specifically asked for
  designer-replica work.
- Agent: detects category **and** budget/quality tier, explicitly reasons
  about fit, and every returned producer is grounded in the retrieved
  candidate data (check `trajectories/*.json`, step `verify_matches`, to
  confirm `issues` is empty or explains any dropped result).

## 7. Data

All data is synthetic, created for this project — 18 producer listings
(`data/producers.json`) across 5 categories (tailor, farmer, developer,
mechanic, tutor) and 10 hand-written evaluation queries with ground-truth
expected matches (`data/eval_queries.json`). No real personal data, API
keys, or credentials are included in this submission.

## 8. Versions used during development

- Python 3.12
- `anthropic` Python SDK (see `requirements.txt` for pinned version)
- Model: `claude-sonnet-5` (Anthropic) or `openai/gpt-oss-120b` (Groq) — whichever
  provider your API key is for is chosen automatically; override with the `AGENT_MODEL`
  environment variable if needed