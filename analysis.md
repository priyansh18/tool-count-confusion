# Analysis

Recomputed directly from `raw_results.jsonl` via `summarize.py`, not retyped by hand.

## 1. Raw accuracy falls, but not smoothly

| Tools | Correct | Accuracy |
|---|---|---|
| 5  | 16/20 | 80% |
| 10 | 16/20 | 80% |
| 25 | 15/20 | 75% |
| 50 | 11/20 | 55% |

The drop from 5 to 25 tools is mild (80% to 75%, one extra wrong answer). The real
cliff is specifically between 25 and 50 tools: a 20-point fall in one step. This
matches the shape reported elsewhere (GitHub's own offline MCP evaluation names
confusable tool pairs as a precision/recall problem, not a smooth decay curve) more
than it matches a story where every added tool contributes an equal amount of
confusion.

## 2. Chance-corrected, the story reverses

Pure-chance accuracy at 50 tools is 2% (1 in 50). The model got 55%, 27.5x better than
random guessing. At 5 tools, chance is 20%, and the model's 80% is "only" 4x better
than random. **The model's accuracy relative to chance improves as tool count grows,
even while its raw accuracy falls.** Both numbers are computed from the same 80 calls;
neither is wrong. They answer different questions: raw accuracy answers "will my agent
call the right tool," which is what a production engineer cares about. Accuracy-over-
chance answers "is the model's underlying selection ability actually degrading," which
is closer to what "How Many Tools Should an LLM Agent See?" (arXiv 2605.24660) is
built to measure. A piece that reports only the raw 80%-to-55% drop and calls it "the
model got dumber" is telling half the story.

## 3. The failures change shape, not just frequency

| Tools | Wrong | Near-neighbor | Unrelated tool | No call |
|---|---|---|---|---|
| 5  | 4 | 3 | 1 | 0 |
| 10 | 4 | 2 | 2 | 0 |
| 25 | 5 | 2 | 3 | 0 |
| 50 | 9 | 1 | 8 | 0 |

At 5 tools, most wrong answers are genuine near-neighbor confusions (`send_sms` vs.
`send_whatsapp_message`, exactly the plausible-but-wrong pattern ToolChoiceConfusion
names). At 50 tools, the opposite is true: 8 of 9 wrong answers call a tool with no
real connection to the request at all.

## 4. One tool absorbs most of the unrelated-tool failures: `find_contact`

Of the 14 "unrelated tool" wrong calls across all four conditions, `find_contact` was
the wrongly-called tool 9 times (64%). The clearest example: scenario 1 asks to
"Email Priya the Q3 numbers" with `send_email` present and correctly named in the
50-tool menu. The model calls `find_contact(name="Priya")` instead, apparently reacting
to the named person in the request rather than completing the actual instruction. See
`failure_examples/attractor_find_contact.json` for the full transcript. This did not
happen at 5, 10, or 25 tools for the same scenario, request, and temperature -- only at
50. This is this experiment's own finding, not something taken from the cited papers:
a single generically-plausible tool can become a disproportionate failure sink once the
menu is large enough, rather than errors spreading evenly across all available
distractors.

## 5. Not every failure is a tool-count effect, and pretending otherwise would be
cherry-picking

Three scenarios (4, 6, 9) were answered wrong at every tool count tested, including
the 5-tool floor:

- Scenario 4: "Text Rohan that I'm running 10 minutes late" -> model consistently
  prefers `send_whatsapp_message` over the intended `send_sms`, at every menu size.
- Scenario 6: "Book a 30-minute call with Priya next Tuesday at 3pm" -> confused with
  contact/availability tools at every menu size.
- Scenario 9: "Am I free Thursday afternoon between 2 and 5?" -> consistently answered
  with `get_current_time` instead of `check_calendar_availability`, at every menu size.

These are scenario-design artifacts, not evidence that a larger menu caused those
specific failures -- they were already wrong when there were only 5 tools to choose
from. Folding them into "tool count broke this" would overstate the finding.

The actually isolated tool-count effect is the set of scenarios that were answered
**correctly at low tool counts and became wrong specifically as the menu grew**:
scenarios 1, 3, 7, 8, and 10 -- 5 of the 20 scenarios (25%) flipped from right to
wrong purely as a function of how many tools were in the menu, with the request,
model, and temperature held constant. That is the real, isolated signal this
experiment set out to measure.

## Takeaway

More tools did not make this model worse at reasoning in any absolute sense -- its
accuracy-over-chance kept climbing. It did make a real, practical failure mode more
likely: exactly the right tool can sit in the menu, correctly named, and still lose to
a generically-plausible tool that the model defaults to once there's enough noise
around it. For a quarter of this experiment's scenarios, that happened purely because
the menu grew, with nothing else changing.
