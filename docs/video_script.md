# Solution Video Script (Target: 4:30–5:00)

Record your screen (terminal + code editor) while reading this. Timestamps
are guidance, not strict — prioritize sounding natural over hitting exact
seconds.

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
python3 baseline/keyword_matcher.py "I want a lehenga that looks like a designer one, budget 3000"
```

"It correctly finds 'tailor' as the category, but it just sorts by
cheapest price. It has no idea I said 'designer' or that I have a budget —
watch what happens when I ask for something premium instead."

```bash
python3 baseline/keyword_matcher.py "I want a bridal outfit with heavy zari and sequin work, quality matters most"
```

"Same thing — it's still recommending the cheapest tailor, even though I
explicitly said quality matters more than price. That's the gap."

## 0:50–2:30 — One realistic execution of the agent, start to finish (≈100 sec)

*(Terminal)*

"Now the SmartMatch agent. Same second query — bridal, heavy embroidery,
quality over price."

```bash
python3 agent/smart_match_agent.py "I want a bridal outfit with heavy zari and sequin work, quality matters most"
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
file)*

```bash
cat trajectories/trajectory_*bridal*.json
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
python3 eval/evaluate.py
```

*(Let the table print, then point at it)*

"Top-3 Hit Rate — did the correct producer show up in the top 3 results —
baseline gets 90%, the agent gets 100%. The one query the baseline
misses is exactly the bridal case I just showed you: it can't tell
'cheapest' from 'best fit'. Wrong-Fit Rate — how often a result is
outside the right category or budget tier — both are at zero on this
test set, which is honest to report; that metric needs a harder test
case than I've included so far to really stress it, and I call that out
directly in the changelog."

## 3:40–4:20 — Changelog walkthrough (≈40 sec)

*(Show CHANGELOG.md on screen, scroll through the table)*

"The changelog traces how this evolved: baseline first, then the
parse-and-rank agent, then I added the verification step as a safety net
against hallucinated matches, then I realized my original wrong-fit metric
only checked category — not budget — so I tightened it. The change that
contributed the most was the reasoning-based ranking step itself — that's
what closed the gap on the bridal query. The thing I removed was a
price-based tiebreak in the mock-mode fallback that made offline testing
look too similar to the baseline to be useful."

## 4:20–5:00 — Failure mode and hot take (≈40 sec)

*(Talking head or slide)*

"The main failure mode: when a consumer doesn't state a number, the agent
has to infer budget and quality from tone alone, and a wrong guess there
skews everything downstream — verification catches hallucinated
producers, but it can't catch a correctly-grounded match that was simply
the wrong tier.

My hot take: for a matching system like this, raw ranking accuracy isn't
the real bottleneck — trust is. A matcher that's occasionally wrong but
never shows you a result it can't justify from real data is more useful
than one that's marginally more accurate but ungrounded. That's the
design principle I'd carry into any agent that's making recommendations
a real person acts on."

*(End)*

---

## Recording checklist

- [ ] Run everything in **real mode** (API key set) before recording —
      mock-mode output should not be what's shown as your main result.
- [ ] Increase terminal font size before recording.
- [ ] Do one full dry run of all commands beforehand so there are no
      surprises on camera.
- [ ] Keep total runtime under 5:00 — trim the intro rather than the
      comparison/changelog sections if you're running long.
