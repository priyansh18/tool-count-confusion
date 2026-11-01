#!/usr/bin/env python3
"""Recomputes every headline number from raw_results.jsonl directly -- never trust a
cached/remembered number, always recompute from the raw file."""
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(__file__)
TOOL_COUNTS = [5, 10, 25, 50]


def main():
    records = [json.loads(l) for l in open(os.path.join(HERE, "raw_results.jsonl"))]
    assert len(records) == 80, f"expected 80 records, got {len(records)}"

    by_n = defaultdict(list)
    for r in records:
        by_n[r["tool_count"]].append(r)

    print("tool_count, correct, total, raw_accuracy, chance_baseline, accuracy_over_chance")
    summary = {}
    for n in TOOL_COUNTS:
        recs = by_n[n]
        correct = sum(1 for r in recs if r["correct"])
        total = len(recs)
        raw_acc = correct / total
        chance = 1 / n
        over_chance = raw_acc / chance
        summary[n] = {
            "correct": correct, "total": total, "raw_accuracy": raw_acc,
            "chance_baseline": chance, "accuracy_over_chance": over_chance,
        }
        print(f"{n}, {correct}, {total}, {raw_acc:.2f}, {chance:.3f}, {over_chance:.1f}x")

    # Failure mode breakdown: wrong tool called that's a near-neighbor decoy vs. a
    # random/unrelated tool vs. no function call returned at all.
    scenarios = json.load(open(os.path.join(HERE, "scenarios.json")))
    near_neighbors_by_target = {s["target"]: set(s["near_neighbors"]) for s in scenarios}

    print("\nFailure breakdown per tool_count (of the incorrect calls):")
    attractor_counter = Counter()
    for n in TOOL_COUNTS:
        wrong = [r for r in by_n[n] if not r["correct"]]
        near_neighbor_fails = 0
        random_fails = 0
        no_call_fails = 0
        for r in wrong:
            if r["called_tool"] is None:
                no_call_fails += 1
            elif r["called_tool"] in near_neighbors_by_target.get(r["target"], set()):
                near_neighbor_fails += 1
            else:
                random_fails += 1
                attractor_counter[r["called_tool"]] += 1
        print(f"  n={n}: {len(wrong)} wrong -- {near_neighbor_fails} near-neighbor, "
              f"{random_fails} unrelated-tool, {no_call_fails} no-call")

    print("\nMost common 'unrelated tool' wrongly called across all conditions (attractor check):")
    for tool, count in attractor_counter.most_common(5):
        print(f"  {tool}: {count}")

    # Scenario 4 (send_sms) consistency check -- is any single scenario failing at
    # every tool count regardless of n, i.e. a pure near-neighbor ambiguity unrelated
    # to menu size?
    print("\nScenarios wrong at EVERY tool count (menu-size-independent failures):")
    by_scenario = defaultdict(list)
    for r in records:
        by_scenario[r["scenario_id"]].append(r["correct"])
    for sid, outcomes in sorted(by_scenario.items()):
        if not any(outcomes):
            print(f"  scenario {sid}: wrong at all 4 tool counts")

    with open(os.path.join(HERE, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("\nWrote summary.json")


if __name__ == "__main__":
    main()
