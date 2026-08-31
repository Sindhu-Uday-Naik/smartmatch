# Evaluation Results

Mode: real (or mock fallback if no API key set)

| Metric | Baseline | Agent | Change |
|---|---|---|---|
| Top-3 Hit Rate | 0.9 | 1.0 | +0.1 |
| Wrong-Fit Rate (lower is better) | 0.0 | 0.0 | 0.0 |

## Per-query breakdown

| Query ID | Query | Expected Category | Baseline Result IDs | Baseline Hit | Agent Result IDs | Agent Hit |
|---|---|---|---|---|---|---|
| Q1 | I want a lehenga that looks like a designer one I saw on Instagram but I can't afford a boutique. Budget around 3000 rupees. | tailor | P002, P014, P018 | True | P001 | True |
| Q2 | Need 2 kg of flowers, ideally marigold or rose, for a festival tomorrow. Want the cheapest fair price, willing to go direct to a farm. | farmer | P006, P004, P015 | True | P015, P004, P005 | True |
| Q3 | I'm a final year engineering student and need someone affordable to help build my major project, a simple web app, I'm not confident in coding. | developer | P009, P007, P017 | True | P007, P009 | True |
| Q4 | My major project needs some machine learning component and I have a slightly higher budget, around 15000 rupees. | developer | P009, P007, P017 | True | P017, P008 | True |
| Q5 | My bike won't start, need a mechanic who does doorstep service, budget under 1000. | mechanic | P016, P011, P010 | True | P010, P011 | True |
| Q6 | Looking for a budget blouse stitched quickly, nothing fancy, just a plain blouse in 3 days. | tailor | P002, P014, P018 | True | P002 | True |
| Q7 | I need my car's tyres and battery replaced, want a specialist not a general mechanic. | mechanic | P016, P011, P010 | True | P011 | True |
| Q8 | Want a home tutor for my 8th grade daughter, maths and science, budget under 1500 a month. | tutor | P012, P013 | True | P012 | True |
| Q9 | I want a bridal outfit with heavy zari and sequin work, budget is flexible, quality matters most. | tailor | P002, P014, P018 | False | P003 | True |
| Q10 | Need someone to mentor me in Python and DSA for placement prep, I'm in college. | tutor | P012, P013 | True | P013 | True |