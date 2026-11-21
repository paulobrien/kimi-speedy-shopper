# Speedy Shopper: candidate configuration

This repository is the **OpenClaw shopper agent** that Thermite tunes. The agent runs on
**Kimi K3.1 Pro on Cerebras** inside OpenClaw. Given "Find five Christmas gifts for <someone>",
it searches the web (Parallel search MCP: `parallel__web_search`, `parallel__web_fetch`) and
answers with five real products, each with its product-page link.

## What you can change

Only `shopper/`:

- `shopper/AGENTS.md`: the agent's instructions (its whole system-prompt workspace file).
- `shopper/settings.json`:
  - `thinking`: low | medium | high | max | minimal. OpenClaw sends `reasoning_effort`; Kimi on
    Cerebras accepts low, high and max, and minimal/medium are sent as low.
  - `params`: only temperature, top_p, maxTokens, frequency_penalty, presence_penalty.
  - `notes`: free text, ignored.

The model, provider, tools and the user's message ("Find five Christmas gifts for {brief}.")
are fixed by the judge.

## How it is scored

- Each judged run does 2 shopper attempts, with gift briefs drawn at random, and is **valid**
  only if most attempts are valid. An attempt is valid when:
  - the final answer has **exactly five distinct URLs**;
  - each is a live product page on a retail site, on at least 2 retailers;
  - every URL appeared in a tool result during that attempt; and
  - no URL is written in `shopper/` (hard-coded results are disqualified).
- **Score = mean tokens/sec**: for every model call, `completion_tokens / completion_time` from
  Cerebras's own server-side timing; the mean over the attempt's calls, then over valid
  attempts. This is the official Speed Bounty metric. Queueing, prefill, network and tool time
  don't count; only how fast the model decodes each call's output.
- Reasoning tokens count as output tokens.

Per-call speed is noisy (roughly 270–560 tok/s for identical requests), so only consistent
gains survive the judge's repeats.
