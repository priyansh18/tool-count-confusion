# Methodology

## Question

Does an LLM's accuracy at picking the right tool for a request fall as the number of
available tools grows, and how much of that fall is genuine reasoning confusion versus
simple chance dilution (more wrong options to pick from)?

## Design

- **20 scenarios**, each a one-line natural-language request with exactly one correct
  target tool from a fixed 50-tool bank (`generate_bank.py`). Tools span 15 everyday-
  assistant domains (email, messaging, calendar, reminders, weather, currency,
  translation, maps, unit conversion, search, files, contacts, notes, music, smart
  home, timezone, shopping, spreadsheets, misc).
- Each scenario also names 2-4 **near-neighbor decoys**: tools from the bank that are
  genuinely plausible for the same request (e.g. `send_sms` vs `send_whatsapp_message`
  vs `send_slack_message` for "text Rohan"), matching ToolChoiceConfusion's own
  definition of the failure mode (arXiv 2606.06284): tools that are "plausible but not
  appropriate."
- **Four tool-menu sizes tested: 5, 10, 25, 50.** For each (scenario, size) pair, the
  menu always contains the correct target tool and that scenario's own near-neighbors
  first, then is filled with randomly sampled remaining tools up to the target size
  (seed fixed per condition, `run_experiment.py`'s `SEED` constant, reproducible). This
  means even the 5-tool condition contains real confusion risk from the start, not just
  an easy target plus random padding — isolating the effect of genuine tool-selection
  ambiguity from pure dilution was the point of this design choice.
- Menu order is shuffled per call so tool position cannot leak the answer.

## Model and call

- `gemini-3.5-flash-lite`, Google's Generative Language API, REST `generateContent`
  endpoint, `functionDeclarations` tool schema, `toolConfig.functionCallingConfig.mode
  = "ANY"` (forces a function call rather than a text reply), `temperature = 0`.
- Temperature 0 was a deliberate design choice for a single-trial-per-cell design: the
  question here is whether the menu itself changes the outcome, not run-to-run
  variance at fixed temperature. One trial per (scenario, tool-count) pair, 80 calls
  total, not a repeated-trial stochastic design.
- **Real environment constraint hit and documented, not hidden:** the first full run
  attempt used `gemini-3.6-flash` and hit that model's free-tier daily quota (20
  requests/day, confirmed via the API's own `429 RESOURCE_EXHAUSTED` response body,
  which named the exact quota ID and a ~2h51m reset window) before a single tool-count
  condition finished. Switched to `gemini-3.5-flash-lite`, a different model with its
  own separate quota bucket, for the full 80-call run reported here. See
  `configs/run.json` for the full note.

## Scoring

- **Correct** = the model's returned `functionCall.name` exactly matches the
  scenario's target tool. Argument correctness was not scored (every correct-tool call
  in this run also had sane arguments on manual inspection, but that was not the
  measured variable).
- **Raw accuracy** = correct / 20 per tool-count condition.
- **Chance baseline** = 1 / tool_count (pure random selection from the menu).
- **Accuracy-over-chance** = raw accuracy / chance baseline. This is the metric that
  separates "the model got worse at reasoning" from "there were simply more wrong
  options available" — the same distinction the Bits-over-Random metric in "How Many
  Tools Should an LLM Agent See? A Chance-Corrected Answer" (arXiv 2605.24660) is built
  to make, applied here with a simpler ratio rather than their full RL-trained metric.
- **Failure mode classification**: each incorrect call was classified as
  (a) *near-neighbor* — the wrongly-called tool was one of the scenario's declared
  plausible decoys, (b) *unrelated-tool* — the wrongly-called tool was neither the
  target nor a declared near-neighbor, or (c) *no-call* — the model returned no
  function call at all. (c) never occurred in this run.

## Known limitations, stated plainly

- **n=20 scenarios is a toy sample, not a publishable benchmark.** Percentages here
  (e.g. "11/20, 55%") are reported with their denominators throughout for exactly this
  reason — a single flipped scenario moves the headline number by 5 points.
- **Three scenarios (4, 6, 9) were answered incorrectly at every tool-count condition,
  including the 5-tool floor.** These are scenario-design artifacts (genuine ambiguity
  in that specific request's wording against its near-neighbor tools), not evidence
  that menu size drove those particular failures — `summarize.py` flags these
  explicitly rather than folding them silently into the "tool count caused this"
  narrative. The article's headline finding rests on the scenarios that were answered
  correctly at low tool counts and became wrong specifically as the menu grew (5 of
  the 20), which is the actually isolated tool-count effect.
- Single-trial, temperature-0 design means these are the model's single modal
  responses to this exact menu ordering and wording, not an average over stochastic
  variation. A production-grade version of this experiment would repeat each cell at
  temperature > 0 across multiple trials; that was out of scope for a $0, single-session
  toy harness.
- 50 tools is still well short of the 100+ tool counts the cited papers test at; this
  experiment stops at 50 because that is close to where real products already draw a
  line: Cursor enforces a hard 40-tool cap, and an independent measurement (Piotr
  Hajdas, DEV.to, January 2026) put Claude Code's own quality-degradation onset around
  50+ tools. Neither number is this experiment's own finding; both are cited for
  context on why 50 was chosen as the ceiling, not asserted as fact beyond their
  original source.
