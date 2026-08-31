import json
import sys

with open(sys.argv[1]) as f:
    traj = json.load(f)

for step in traj:
    name = step.get("step")
    if name == "receive_query":
        print(f"QUERY: {step['query']}\n")
    elif name == "retrieve_candidates":
        print(f"Retrieved {step['candidate_count']} candidates in category '{step['category']}'\n")
    elif name == "final_result":
        result = step["result"]
        print("PARSED REQUIREMENT:", json.dumps(result.get("parsed_requirement"), indent=2))
        print("\nFINAL RESULTS:")
        for r in result.get("results", []):
            print(f"  - {r['name']} (Rs.{r['price_min']}-{r['price_max']}): {r['reason']}")