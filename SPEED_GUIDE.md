# Speed guide: getting the most tokens/sec from Kimi K3.1 Pro on Cerebras

_Findings from an overnight Thermite hill climb (21–22 Nov 2026). Every claim points at a measurement._

## How speed is scored

- Per model call: `completion_tokens / completion_time`, from the `usage` and `time_info` that
  Cerebras sends at the end of every stream. Server-side decode time only: queueing, prefill,
  network and tool time don't count.
- The official Speed Bounty readout is the **mean of per-call rates** over a session (p90 too).
  Reasoning tokens count as output.

## Baseline facts (measured Sat 21 Nov)

- Identical requests decode at ~270–560 tok/s depending on shared load, so single samples can't
  rank settings. Take medians over several runs.
- Our shopper's starting configuration: 2 calls per task (one search call, one answer call),
  ~450 mean tok/s over 9 judged runs.
- Single-sample sweeps showed no clear effect from output length (60–4,000 tokens), reasoning
  effort (low vs high) or temperature (0 vs 1).
- Same model elsewhere (client-side, 600 tokens): Moonshot AI's own API 35 tok/s; median
  OpenRouter host ~110; fastest hosts 300–400.

## What the hill climb tested

Each verdict below is Thermite's judge comparing the candidate against the champion on
paired runs (n = 9 per side, random gift briefs), with a 95% interval on the change in mean
tok/s. "Inconclusive" means the interval still includes zero.

| Idea | Why it might help | Verdict | Evidence |
| --- | --- | --- | --- |
| Reasoning effort `high` vs `low` | Longer reasoning per call spreads any fixed per-call cost | **No effect** | −0.9% [−9.9%, +9.1%] |
| Longer, templated search call (10 queries, one fixed pattern) | The short tool-call turn is half the calls in the mean; making it longer and predictable lifts it | **Faster: adopted** | Judged twice: +9.2% [−0.8%, +20.1%] (420 vs 398 tok/s) and +6.3% [−3.4%, +16.9%] (435 vs 401). Pooled over 18 paired runs: **+7.7% [+0.4%, +15.0%]**, every run still 5 real links |
| Pin to exactly 2 calls (no `web_fetch`) | Fewer short, slow calls in the mean | **Inconclusive, then invalid** | +6.2% [−3.5%, +16.8%] first time; on re-judge it invented a link (not in any search result), which the judge rejects |
| Copy 8–10 candidates into a template while reasoning | Copied text is easy for a draft model to predict | **Invalid** | The answer listed 10 links and most weren't product pages |
| Temperature 0 | Speculative decoding accepts more drafted tokens when greedy | **Likely slower** | −9.0% [−17.2%, +0.2%]: keep the default temperature 1.0 |
| Reasoning off (`thinking: off`) | No reasoning prose to decode | **Rejected** | Not a setting Kimi on Cerebras accepts (`none`/`minimal` are refused), so the bench's settings check turned it away |
| Copy result titles/prices verbatim in the answer | Same as above | **No verdict** | Its judging was cut short repeatedly by infrastructure failures (a search-MCP outage, Cerebras queue timeouts, a bench restart) before the run's time ran out |

What this says so far:

- **Decode speed is mostly the platform's, not yours.** Per-call rate swings ±25% with shared load,
  and nothing we changed moved the mean by more than ~10%. Measure over many runs before believing a
  win.
- **The mean is over calls, so short calls hurt.** A tool-call turn of a few dozen tokens decodes
  slower per token than a long answer. Fewer, longer calls is the one direction that keeps showing up.
- **Speed tricks can break correctness.** Banning page fetches and forcing long candidate lists both
  led to invented or wrong links. A speed harness needs a correctness gate the agent can't touch.

## Recommendations

1. **Make every call long and predictable.** The score is a mean over calls, so a short tool-call
   turn drags it down. Ask for one search call with many queries in a fixed template
   (`<gift idea> for <recipient> buy online price` × 10) rather than a few short ad-hoc ones.
   This is the change we kept: ~+8% over 18 paired runs.
2. **Leave sampling alone.** Temperature 0 was probably slower (−9%), and reasoning effort
   `high` made no difference. Kimi on Cerebras rejects `none`, `minimal` and `xhigh`.
3. **Don't trade away correctness.** Banning page fetches and forcing long candidate lists both
   produced invented or wrong links. Keep a verifier in the loop that the agent can't edit.
4. **Measure over many runs.** Per-call speed swings ±25% with shared load. One fast run proves
   nothing; paired runs on random briefs do.

## Reproduce

See [README.md](README.md#run-the-hill-climb): `scripts/tps_proxy.py`, `scripts/shopper_bench.py`,
and the Thermite kit in `kit/`.
