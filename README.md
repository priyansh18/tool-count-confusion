# tool-count-confusion

Does tool-selection accuracy fall as the number of available tools grows, and how much
of that fall is real reasoning confusion versus pure chance dilution? A $0 toy
experiment: 20 scenarios x 4 tool-menu sizes (5, 10, 25, 50), real function-calling
against Gemini's free tier, scored by hand-verified exact match.

Full write-up: see the linked Medium article (added after publish).

## Headline result

| Tools available | Correct | Raw accuracy | Chance baseline (1/n) | Accuracy over chance |
|---|---|---|---|---|
| 5  | 16/20 | 80% | 20.0% | 4.0x |
| 10 | 16/20 | 80% | 10.0% | 8.0x |
| 25 | 15/20 | 75% | 4.0%  | 18.8x |
| 50 | 11/20 | 55% | 2.0%  | 27.5x |

Raw accuracy falls 25 points from 5 to 50 tools. The model's accuracy *relative to pure
chance* actually keeps climbing the whole time -- both are true, and `methodology.md`
and `analysis.md` explain why they don't contradict each other.

## Reproduce

```bash
python3 -m venv venv && source venv/bin/activate
pip install requests pillow

# Rebuild the fixed 50-tool bank and 20 scenarios (deterministic, no randomness)
python3 generate_bank.py

# Run the experiment (needs GEMINI_API_KEY; ~80 calls, a few minutes with rate-limit pacing)
python3 run_experiment.py --model gemini-3.5-flash-lite --out raw_results.jsonl

# Recompute every number from the raw file
python3 summarize.py

# Rebuild the hero chart
python3 make_chart.py
```

## Files

- `generate_bank.py` -- builds `tools_bank.json` (50 tools) and `scenarios.json` (20
  scenarios with target + near-neighbor decoys).
- `run_experiment.py` -- calls the model for all 80 (scenario, tool-count) pairs,
  writes `raw_results.jsonl`.
- `summarize.py` -- recomputes raw accuracy, chance baseline, accuracy-over-chance, and
  a failure-mode breakdown (near-neighbor vs. unrelated-tool vs. no-call) directly from
  `raw_results.jsonl`. Writes `summary.json`.
- `make_chart.py` -- builds `charts/hero-tool-count-accuracy.png` from `summary.json`.
- `methodology.md` -- full design rationale, scoring rules, and stated limitations.
- `analysis.md` -- the actual findings, including the `find_contact` attractor pattern
  and the 3 scenarios that failed at every tool count regardless of menu size.
- `failure_examples/` -- two real transcripts: a near-neighbor confusion
  (`send_sms` vs `send_whatsapp_message`, present even at 5 tools) and an attractor
  failure (`send_email` with `send_email` itself in the 50-tool menu, model picks
  `find_contact` instead).
- `configs/run.json` -- exact model, temperature, seed, and a note on the mid-run model
  switch forced by a free-tier daily quota limit.

## License

MIT, see `LICENSE`.
