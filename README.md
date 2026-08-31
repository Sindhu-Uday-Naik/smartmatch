# SmartMatch — An Agentic Matcher for Local Producers and Budget-Conscious Consumers

**micro1 Agentic Workflows Hackathon — Submission by Sindhu Uday Naik**

## Who has this problem?

Middle-class consumers regularly need something a small, local producer could
provide well and affordably — a custom dress stitched by a local tailor
instead of a boutique, flowers bought direct from a farmer instead of a
festival-inflated retail price, a college major project built by a fellow
student instead of a professional agency. The producers exist and would
welcome the business. The problem is **discovery**: the consumer has no
reliable way to find the *right* producer for their specific need, budget,
and quality bar.

## What bottleneck makes it worth solving?

A plain listings/search approach (what most classifieds and marketplace
apps do today) can only filter by category and keyword. It can tell a
consumer "here are all tailors" but not "here are the tailors whose price
range and specialty actually match what you're asking for and what you can
afford." That distinction matters: recommending a ₹8,000 bridal designer
to someone with a ₹3,000 budget, or a production-grade freelance developer
to a student looking for an affordable major-project partner, wastes
everyone's time and erodes trust in the platform.

## Does the agent solve it well?

**SmartMatch** takes a consumer's plain-language request and:

1. **Parses** it into structured requirements — category, budget, and a
   quality bar inferred from language cues ("designer", "cheapest",
   "quality matters most").
2. **Retrieves** only the real candidate producers for that category (a
   tool call against the producer database — the agent never invents
   producers).
3. **Reasons** about which candidates genuinely fit the requirement, not
   just the category — explicitly excluding producers that are clearly
   outside the stated budget or quality tier.
4. **Verifies** every result before it's shown: any producer ID the
   reasoning step returns is checked against the actual retrieved
   candidate set. If it references something that isn't there, that
   result is dropped rather than shown to the user.
5. **Logs a full trajectory** of every step — the query, the parsed
   requirement, the retrieved candidates, the reasoning call, and the
   verification outcome — for transparency and reproducibility.

## Can another person reproduce the result?

Yes — see `REPRODUCE.md`. The dataset is synthetic (18 producers across
5 categories, described in `data/producers.json`), the evaluation set is
10 hand-labeled consumer queries with ground-truth expected matches
(`data/eval_queries.json`), and `eval/evaluate.py` runs both the baseline
and the agent on identical queries and produces the same comparison table
every time.

## Architecture

data/producers.json 18 synthetic producer listings (tailor, farmer,
developer, mechanic, tutor)
data/eval_queries.json 10 evaluation queries with ground-truth matches

baseline/keyword_matcher.py Simple category-keyword filter, sorted by
lowest price — the "basic way to handle the
task today"

agent/smart_match_agent.py The SmartMatch agent: parse -> retrieve ->
rank & explain -> verify -> log trajectory

eval/evaluate.py Runs both systems on the same 10 queries,
scores Top-3 Hit Rate and Wrong-Fit Rate,
writes eval/results/results.json + .md

trajectories/ Per-query agent trajectory logs (JSON)


## How agents help here (per the four capability areas)

- **Better context / tools**: the agent's only source of truth is the
  `retrieve_candidates` tool call against the real producer data — it
  cannot answer from memory or invent a producer.
- **Verification**: every ranked result is checked against the retrieved
  candidate set before being shown; unverifiable results are dropped and
  logged as an issue, not silently trusted.
- **Skill-like reasoning**: the requirement-parsing step is a focused,
  single-purpose extraction skill, separate from the ranking/reasoning
  step, so each part of the pipeline can be evaluated and improved
  independently.

## Run modes

The agent supports two real providers plus an offline mock mode:

- **Real mode**: uses the Anthropic API if `ANTHROPIC_API_KEY` is set, otherwise
  the Groq API (free, no credit card) if `GROQ_API_KEY` is set. This is the
  mode used for the actual submission trajectories, evaluation results, and
  demo video — this project's real results were produced via Groq
  (`openai/gpt-oss-120b`).
- **Mock mode** (`--mock`, or automatic fallback with no API key set): a
  deterministic rule-based stand-in for the LLM calls, used only for early
  offline development before an API key was set up. Not used for any
  submitted evidence.

## Real result

On the 10-query evaluation set (`data/eval_queries.json`), run for real
against Groq:

| Metric | Baseline | Agent |
|---|---|---|
| Top-3 Hit Rate | 0.90 | **1.00** |
| Wrong-Fit Rate | 0.00 | 0.00 |

The full story of how the agent went from an initial 0.80 (a regression
below baseline) up to 1.00 — by reading a real failed trajectory and fixing
a specific gap in the ranking prompt — is in `CHANGELOG.md`.

See `CHANGELOG.md` for how the solution evolved and `REPRODUCE.md` for
exact setup and run commands.

## Main failure mode & hot take

The agent's requirement parser has only one slot for consumer intent beyond
category and budget — a quality tier (budget/moderate/premium) inferred
from tone. When a request names something *specific* (a type of specialist,
a material, a turnaround time) rather than a general quality signal, that
detail isn't captured as its own field — it only reaches the ranking step
buried inside free text, where it's easy to under-weight. This was caught
for real during development: the agent initially recommended a general
mechanic over an actual tyre/battery specialist for a query that explicitly
asked for "a specialist, not a general mechanic" — full story and fix in
`CHANGELOG.md`.

**Hot take**: the most valuable moment in building this wasn't the final
100% score, it was catching a real regression (the agent's first version
scored *worse* than the baseline) by reading one actual failed trajectory
instead of trusting the aggregate number. An aggregate score tells you
*that* something's wrong; only the trajectory tells you *what*. That's the
habit worth carrying into any agent whose recommendations a real person
acts on.