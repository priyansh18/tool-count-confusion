#!/usr/bin/env python3
"""Tool-count scaling experiment: does tool-selection accuracy fall as the
number of available tools grows, and how much of that fall is genuine
reasoning confusion versus pure chance dilution?

For each of 20 scenarios x 4 tool-count conditions (5, 10, 25, 50), builds a
tool menu containing the scenario's correct target tool, its real
near-neighbor decoys (plausible-but-wrong per ToolChoiceConfusion's own
definition), and enough additional random decoys to reach the condition's
count. Calls Gemini's free tier with real function-calling (not a scripted
keyword match) and records whether it picked the correct tool.

Usage:
    python3 run_experiment.py --model gemini-3.6-flash --out raw_results.jsonl
"""
import argparse
import json
import os
import random
import sys
import time

import requests

HERE = os.path.dirname(__file__)
ENV_SECRET = os.path.join(HERE, "..", "..", "..", "..", "..", ".env.secret")
TOOL_COUNTS = [5, 10, 25, 50]
SEED = 20261101  # fixed seed, reused every run for reproducibility


def load_key(name):
    key = os.environ.get(name)
    if not key and os.path.exists(ENV_SECRET):
        with open(ENV_SECRET) as fh:
            for line in fh:
                if line.startswith(f"{name}="):
                    key = line.strip().split("=", 1)[1]
                    break
    return key


def build_menu(scenario, all_tools_by_name, tool_count, rng):
    """Correct tool + near-neighbors first, then random fill to tool_count."""
    target = scenario["target"]
    chosen = [target] + [n for n in scenario["near_neighbors"] if n != target]
    remaining = [name for name in all_tools_by_name if name not in chosen]
    rng.shuffle(remaining)
    while len(chosen) < tool_count and remaining:
        chosen.append(remaining.pop())
    chosen = chosen[:tool_count]
    rng.shuffle(chosen)  # position in the menu must not leak the answer
    return [all_tools_by_name[name] for name in chosen]


def call_gemini(model, key, request_text, menu):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": request_text}]}],
        "tools": [{"functionDeclarations": menu}],
        "toolConfig": {"functionCallingConfig": {"mode": "ANY"}},
        "generationConfig": {"temperature": 0},
    }
    r = requests.post(url, json=body, timeout=60)
    r.raise_for_status()
    return r.json()


def extract_call(response_json):
    try:
        parts = response_json["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError):
        return None, None
    for part in parts:
        fc = part.get("functionCall")
        if fc:
            return fc.get("name"), fc.get("args")
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-3.5-flash-lite")
    ap.add_argument("--out", default=os.path.join(HERE, "raw_results.jsonl"))
    ap.add_argument("--sleep", type=float, default=3.0, help="seconds between calls, free-tier rate-limit safety")
    args = ap.parse_args()

    key = load_key("GEMINI_API_KEY")
    if not key:
        print("ERROR: GEMINI_API_KEY not found in .env.secret or environment.", file=sys.stderr)
        sys.exit(1)

    tools = json.load(open(os.path.join(HERE, "tools_bank.json")))
    tools_by_name = {t["name"]: t for t in tools}
    scenarios = json.load(open(os.path.join(HERE, "scenarios.json")))

    results = []
    total = len(scenarios) * len(TOOL_COUNTS)
    done = 0
    for tool_count in TOOL_COUNTS:
        rng = random.Random(SEED + tool_count)  # deterministic per condition
        for scenario in scenarios:
            menu = build_menu(scenario, tools_by_name, tool_count, rng)
            menu_names = [t["name"] for t in menu]
            attempt = 0
            response_json = None
            last_err = None
            while attempt < 3:
                try:
                    response_json = call_gemini(args.model, key, scenario["request"], menu)
                    break
                except requests.exceptions.HTTPError as e:
                    last_err = str(e)
                    body = e.response.text if e.response is not None else ""
                    if e.response is not None and e.response.status_code == 429 and "per day" in body.lower():
                        print(f"DAILY QUOTA EXHAUSTED for {args.model}: {body[:300]}", file=sys.stderr)
                        print(f"Writing {len(results)} completed records so far and stopping.", file=sys.stderr)
                        with open(args.out, "w") as f:
                            for r in results:
                                f.write(json.dumps(r) + "\n")
                        sys.exit(2)
                    attempt += 1
                    time.sleep(15)
                except Exception as e:
                    last_err = str(e)
                    attempt += 1
                    time.sleep(5)
            done += 1
            if response_json is None:
                record = {
                    "scenario_id": scenario["id"], "tool_count": tool_count,
                    "request": scenario["request"], "target": scenario["target"],
                    "menu": menu_names, "called_tool": None, "called_args": None,
                    "correct": False, "error": last_err,
                }
            else:
                called_tool, called_args = extract_call(response_json)
                record = {
                    "scenario_id": scenario["id"], "tool_count": tool_count,
                    "request": scenario["request"], "target": scenario["target"],
                    "menu": menu_names, "called_tool": called_tool, "called_args": called_args,
                    "correct": called_tool == scenario["target"], "error": None,
                }
            results.append(record)
            print(f"[{done}/{total}] n={tool_count} scenario={scenario['id']} "
                  f"target={scenario['target']} called={record['called_tool']} correct={record['correct']}",
                  file=sys.stderr)
            time.sleep(args.sleep)

    with open(args.out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(results)} records to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
