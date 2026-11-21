# Speed guide: getting the most tokens/sec from Kimi K3.1 Pro on Cerebras

_Draft. The findings fill in as the Thermite campaign proves or rejects each idea; every claim
here should point at a measurement._

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

| Idea | Why it might help | Verdict | Evidence |
| --- | --- | --- | --- |
| `reasoning_effort` max vs low | Longer reasoning per call spreads fixed per-call cost | _pending_ | |
| Temperature 0 | Speculative decoding accepts more drafted tokens when greedy | _pending_ | |
| One search call, no extra fetches | Fewer short, slow calls in the mean | _pending_ | |
| Copy titles/URLs verbatim from results | Copied text is easy for a draft model to predict | _pending_ | |
| Structured, predictable answer format | Same as above | _pending_ | |

## Recommendations

_Filled in from confirmed wins._

## Reproduce

See [README.md](README.md#run-the-hill-climb): `scripts/tps_proxy.py`, `scripts/shopper_bench.py`,
and the Thermite kit in `kit/`.
