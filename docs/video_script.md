# Solution Video Script (Target: 4:30–5:00)

Record your screen (terminal + code editor) while reading this. Timestamps
are guidance, not strict — prioritize sounding natural over hitting exact
seconds.

## Before you hit record

Run these in your terminal first (not shown on camera — set up before
recording starts):

```powershell
$env:GROQ_API_KEY="your-key-here"
$env:AGENT_MODEL="openai/gpt-oss-120b"
```

---

## 0:00–0:50 — The problem and the baseline (≈50 sec)

*(Talking head or slide, then cut to terminal)*

"Middle-class consumers often have a specific need a local producer could
meet well — a custom dress from a local tailor instead of a boutique,
flowers bought direct from a farmer instead of at festival-inflated
prices, a college project built by a fellow student instead of an
agency. The producers exist. The problem is discovery — finding the
*right* one for your specific need and budget.

A basic listings search — what most apps do today — can only filter by
category. Let me show you the baseline."

*(Switch to terminal)*

```bash
python baseline/keyword_matcher.py "I want a lehenga that looks like a designer one, budget 3000"
```

"It correctly finds 'tailor' as the category, but it just sorts by
cheapest price. It has no idea I said 'designer' or that I have a budget —
watch what happens when I ask for something premium instead."

```bash
python baseline/keyword_matcher.py "I want a bridal outfit with heavy zari and sequin work, quality matters most"
```

"Same thing — it's still recommending the cheapest tailor, even though I
explicitly said quality matters more than price. That's the gap."

## 0:50–2:30 — One realistic execution of the agent, start to finish (≈100 sec)

*(Terminal)*

"Now the SmartMatch agent. Same second query — bridal, heavy embroidery,
quality over price."

```bash
python agent/smart_match_agent.py "I want a bridal outfit with heavy zari and sequin work, quality matters most"
```

*(While it runs, narrate the steps out loud, pointing at the printed
output as each part appears)*

"First it parses my request into structured requirements — category,
budget, and a quality tier it infers from words like 'heavy' and 'quality
matters most'. Then it retrieves the real candidate tailors from the
database — it can't see or invent anyone outside this list. Then it
reasons about which of those actually fit — and this time it correctly
picks the premium bridal specialist instead of the cheapest option.

And here's the important part — verification." *(open the trajectory
file using the viewer script)*

```bash
python eval/view_trajectory.py trajectories/trajectory_<newest_bridal_filename>.json
```

"Every producer ID the reasoning step returns gets checked against the
real retrieved candidates before it's shown to me. If the model ever
referenced a producer that wasn't actually in the retrieved set, it would
be dropped here, not silently shown. That's the difference between an
LLM that sounds confident and an agent that's actually grounded in real
data."

## 2:30–3:40 — Final baseline vs. agent comparison (≈70 sec)

*(Terminal)*

"Here's the full picture — baseline and agent run on the same 10 test
queries with known correct answers."

```bash
python eval/evaluate.py
```

*(Let the table print, then point at it)*

"Top-3 Hit Rate — did the correct producer show up in the top 3 results —
baseline gets 90%, the agent gets 100%. But it's worth being honest about
how I got here: the agent's *first* version actually scored 80% — worse
than the baseline — and I'll show you exactly why in the changelog,
because that regression taught me more than a clean win would have."

## 3:40–4:20 — Changelog walkthrough (≈40 sec)

*(Show CHANGELOG.md on screen, scroll through the table)*

"The changelog traces how this evolved: baseline first at 90%, then the
first real version of the agent — which actually dropped to 80%, missing
two queries it hadn't missed before. Instead of just accepting that
number, I opened the actual trajectory log for one of the failures and
found the real cause: I'd asked a consumer for 'a specialist, not a
general mechanic,' and the agent recommended the general mechanic anyway
— its ranking prompt only knew how to weigh budget and quality, not a
specific named requirement like that. I rewrote the prompt to prioritize
exact requirement matches over generic category fit, reran the
evaluation, and it jumped to 100% — fixing not just that query but
another one with the same root cause. That regression-then-fix is the
most important part of this whole changelog."

## 4:20–5:00 — Failure mode and hot take (≈40 sec)

*(Talking head or slide)*

"The main failure mode: my requirement parser only has one slot for
consumer intent beyond category and budget — a quality tier, budget or
premium — inferred from tone. When a request names something specific,
like a type of specialist, that requirement doesn't get its own field —
it's buried inside a free-text summary, where the model can easily
under-weight it. My prompt fix patched this for the specific 'specialist'
case, but a more robust fix would give that kind of specific requirement
its own structured field at the parsing step, not just at ranking.

My hot take: the most valuable moment building this wasn't the clean 100%
score, it was the regression. If I'd only looked at the aggregate hit-rate
number, I could have shipped a worse system while assuming agentic
reasoning was automatically better than the baseline. It wasn't, until I
actually read one real failure's trajectory end to end. The lesson I'd
carry into any agent I build next: never trust an aggregate score without
reading at least one real failure's full trajectory — the aggregate tells
you *that* something's wrong, only the trajectory tells you *what*."

*(End)*

---

## Recording checklist

- [ ] Set `GROQ_API_KEY` and `AGENT_MODEL` in your terminal before recording.
- [ ] Increase terminal font size before recording.
- [ ] Do one full dry run of all commands beforehand so there are no
      surprises on camera — especially the `view_trajectory.py` filename,
      which changes every run.
- [ ] Keep total runtime under 5:00 — trim the intro rather than the
      comparison/changelog sections if you're running long.