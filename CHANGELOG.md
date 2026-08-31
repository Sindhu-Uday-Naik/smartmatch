# Improvement Changelog — SmartMatch

Evidence below is from real agent runs via the Groq API (`openai/gpt-oss-120b`),
not mock mode — see `eval/results/results.md` for the full per-query detail
backing these numbers.

| Stage | What was tried and why | Evidence (real, Groq) | Decision / Learning |
|---|---|---|---|
| **Baseline** | Plain category-keyword filter, results sorted by lowest starting price — the way a basic listings search works today | Top-3 Hit Rate: **0.90** (10 queries) | Established the starting point. Its one miss (Q9, a bridal/premium request) shows the structural limit: it has no concept of "budget" or "quality," only category and raw price. |
| **Iteration 1** | Built the agent's requirement-parsing step (category, budget, quality-bar extraction) and a reasoning-based ranking step, first version, run for real against Groq | Top-3 Hit Rate: **0.80** — *worse* than the baseline. It correctly fixed Q9 (bridal case) but newly failed Q7 and Q8 | **Not kept as-is — investigated.** A clean win would have hidden a real problem; a regression forced us to actually look at the trajectory logs instead of trusting the aggregate number. |
| **Root-cause investigation** | Read the Q7 trajectory (`trajectories/trajectory_*_I_need_my_car's_tyre.json`) directly | Query explicitly said *"want a specialist not a general mechanic"*; the agent recommended the general mechanic (Venu Auto Works) over the actual tyre/battery specialist (Iqbal Tyre & Battery) that was in the same candidate pool | Diagnosed the cause: the ranking prompt only told the model to weigh budget and quality tier — it had no instruction to weigh a *specific named requirement* ("specialist") against generic category overlap. This was a schema/prompt gap, not a one-off model mistake. |
| **Iteration 2** | Rewrote `RANK_SYSTEM` to explicitly rank specific-requirement matches (named specialization, e.g. "specialist") above generic category fit, ahead of budget and quality tier | Top-3 Hit Rate: **1.00** — Q7 now correctly returns Iqbal Tyre & Battery first, with reasoning that explicitly cites "tyre replacement and battery service" against the general mechanic's "general car maintenance." Q8 also fixed as a side effect of the same prompt change. | **Kept.** This is the single change that contributed the most — see Hot Take below. |
| **Final** | Parse → retrieve → rank & explain (with the corrected prompt) → verify → log trajectory | Baseline **0.90** → Agent **1.00** (+0.10) on Top-3 Hit Rate. Wrong-Fit Rate: 0.00 for both (see note below on this metric's current limits). | Net result: the agent beats the baseline specifically on the cases that require understanding *why* a request calls for a particular producer, not just which category it falls in. |

## Experiment removed

The first ranking prompt asked the model to weigh "budget or quality level"
as the only differentiators beyond category. This was removed/replaced in
Iteration 2 because it turned out to be an incomplete list — real consumer
requests (like "want a specialist, not a general mechanic") carry requirements
that are neither about budget nor about quality tier, and a prompt that only
checks for those two dimensions will silently ignore anything else the
consumer explicitly asked for.

## Known metric limitation

Wrong-Fit Rate (results outside the correct category, or more than double
the stated budget) reads 0.00 for both systems on the current 10-query set —
this is an honest result, not a bug, but it also means this particular test
set doesn't yet contain a query severe enough to exercise that metric. A
harder budget-violation test case would make it more meaningful; noted here
rather than quietly left unexplained.

## Main failure mode

The requirement parser has only one slot for consumer intent beyond category
and budget — `quality_bar` (budget/moderate/premium) — inferred from tone.
When a request carries a *specific, named* requirement (a specialization, a
material, a turnaround time) rather than a general quality signal, that
requirement isn't captured as its own structured field; it only reaches the
ranking step indirectly, inside `need_summary`, where it's easy for the
model to under-weight it in favor of the fields it was explicitly told to
optimize for. Iteration 2 patched this at the prompt level for the
"specialist" case specifically. A more robust fix would add a proper
structured field for named specific-requirements at the parsing step,
rather than relying on the ranking step to notice them buried in free text.

## Hot take

The most valuable moment in building this wasn't the clean 1.00 score — it
was the *regression* at Iteration 1 (0.90 → 0.80). If I'd only looked at the
aggregate hit-rate number, I could have quietly shipped a worse system while
believing agentic reasoning was strictly better than the baseline by
default. It wasn't, until the actual trajectory log was read and the
specific miss was traced back to a concrete, fixable gap in the ranking
prompt. **The practical lesson for building reliable agents: never trust an
aggregate score without reading at least one real failure's full
trajectory** — the aggregate tells you *that* something is wrong, only the
trajectory tells you *what*.