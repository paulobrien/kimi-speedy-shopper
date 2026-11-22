# Hackathon plan: Santa's Speedy Shopper, tuned by Thermite

Build window: **Sat 21 Nov 10:00 PT → Sun 22 Nov 10:00 PT** (18:00 → 18:00 GMT). Everything (X post, optional r/cerebras post, Speed Bounty entry on Discord) is due by **Sun 10:00 PT**.

## The brief, and what meets it

| Requirement | How we meet it |
| --- | --- |
| Kimi K3.1 Pro on Cerebras is central | Every shopper turn, and the mission-control agent, runs on `cerebras/moonshotai-kimi-k3.1-pro-trial` |
| OpenClaw harness | The shopper and mission control are both OpenClaw agents on the local gateway |
| Speed Bounty task | The `shopper` agent finds **five Christmas gifts on real retail sites**, each with its product link |
| No made-up or hard-coded results | Links come only from live search during the run; `scripts/verify_gifts.py` re-fetches each link and checks it's a live product page; the judge rejects any link that also appears in the agent's own files |
| Bounty TPS | Measured with the official patch (separate patched build, never in the public demo). Our own proxy reproduces its formula exactly for development |
| ≤60 s video, Cerebras speed, GPU side-by-side | `shopper` (Kimi K3.1 Pro on Cerebras) vs `shopper-gpu` (the same model and agent on Moonshot AI's own API via OpenRouter); `scripts/race.py` races the two from each side's first token, plus verified links on screen |

## How TPS is scored (from the official patch)

- For each model call: `completion_tokens / time_info.completion_time`, taken from the last chunk of Cerebras's stream. That's server-side decode speed, so queueing, prefill, network and tool time don't count.
- The headline is the **mean of the per-call rates** over the session (p90 is shown too). The readout is only in the patched **web chat UI**.
- The patch's example config uses thinking level `low` (`reasoning_effort=low`), temperature 1.0. Kimi rejects `none`, `minimal` and `xhigh`.

What we measured on our key (Sat 18:40 GMT): per-call TPS is noisy (≈270–470 for identical requests). Neither output length (60–4,000 tokens), reasoning effort (low/high) nor temperature (0/1) shows a clear effect in single samples. Any gains will be small and need many repeats to prove, which is exactly what Thermite's judge is for.

## Parts

1. **Shopper agent** (`shopper/`, OpenClaw agent `shopper`). Its only tools are web search and fetch (Parallel's free search MCP, connected as an MCP server). It's told to output exactly five gifts as `name — price — retailer — URL`.
2. **TPS meter** (`scripts/tps_proxy.py`). A local pass-through proxy to `api.cerebras.ai`. It logs each call's `completion_tokens` and `completion_time` and reports the same mean/p90 as the patch. The headless bench (and, for the demo, the gateway) point their Cerebras base URL at it.
3. **Verifier** (`scripts/verify_gifts.py`). Fetches each of the five links: HTTP status, product schema (JSON-LD `Product`/`Offer`) or price, and the page title. It's also shown in the demo, as proof that the links are real.
4. **Bench service** (`scripts/shopper_bench.py`). Runs one shopper attempt end to end on a candidate configuration: agent prompt plus request settings → OpenClaw run through the proxy → verify → JSON with mean TPS, p90, call count, validity, wall time. It's used both from the CLI and by the Thermite judge (reached from the rig container at `host.docker.internal`).
5. **Thermite hill climb** (`kit/`). A Thermite kit whose candidate is the shopper configuration (`shopper/AGENTS.md`, `shopper/settings.json`). The judge runs the bench several times with varied gift briefs. Score = mean TPS, gated on validity: 5 distinct live product links, all present in that run's tool results, none present in the candidate's files. Thermite's workers stay on the rig's current models; Kimi is central through OpenClaw.
6. **Mission control** (existing `mission` agent). OpenClaw on Kimi, steering the Thermite campaign through its MCP tools ("how's the speed run going?", "queue another lane"). This is the "guide" half of the demo.

## Outcome (Sun 22 Nov)

- Campaign `speedy-shopper-2` ran Sat 19:22 → Sun 13:25 GMT: 429 judge calls, 857 shopper runs, 6 ideas judged. Verdicts and lessons are in [SPEED_GUIDE.md](SPEED_GUIDE.md).
- Adopted: one long templated search call, +7.7% [+0.4%, +15.0%] pooled over two judgements (each alone inconclusive, so Thermite didn't promote it).
- Speed Bounty entry (patched web chat, recorded live): 483 tok/s mean, 587 p90, 5/5 links verified. Best unrecorded run: 504 mean, 584 p90, 5/5. Public demo race: Cerebras 285 vs Moonshot API 30 tok/s (9.6×).
- Infrastructure lessons: Cerebras queueing (up to ~4 min per call) and brief search-MCP outages caused false failures overnight; the bench now retries those instead of scoring them.

## Timeline

- **Sat evening (GMT):** parts 1–4 working on standard OpenClaw; first valid shopper runs with TPS numbers. Plan, README and commits.
- **Sat night:** kit + contract, judge-only test, then start the campaign (1–2 lanes; pause it whenever we take bounty measurements).
- **Sun morning:** take the best configuration. Build the patched OpenClaw in a separate folder, run the shopper in its web UI, and record the bounty video showing top mean TPS and the 5 links.
- **Sun midday:** record the public demo on standard OpenClaw (shopper speed, GPU side-by-side, Thermite climb chart). Push the repo, then post to X, Reddit and Discord well before 18:00 GMT.

## Constraints

- 100 RPM / 100K TPM per participant; **cached prompt tokens don't count**. Keep the agent's prompt prefix stable and small.
- The speed patch must not be published or committed, and the public demos use standard OpenClaw.
- Cerebras live support: Sat 10:30–12:30 PT, Sun 9:00–10:00 PT.
