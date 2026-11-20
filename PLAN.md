# Hackathon plan: Kimi K3.1 Pro on Cerebras + OpenClaw + Thermite

Build window: **Sat 21 Nov 10:00 PT → Sun 22 Nov 10:00 PT**. Submit (X post, optional r/cerebras) by Sun 10:00 PT.

## The idea

**An OpenClaw agent running on Kimi K3.1 Pro (Cerebras) is mission control for Thermite.**

- **OpenClaw is the harness and the face of the project.** You talk to one OpenClaw agent in chat (dashboard, TUI or a messaging channel). It runs on `cerebras/moonshotai-kimi-k3.1-pro-trial` and holds Thermite's 68 MCP tools via the operator token. It starts campaigns, reads results, steers lanes and explains what's happening.
- **Thermite does the autoresearch.** Its worker lanes also use Kimi on Cerebras (an OpenAI-compatible provider in Thermite). Its judge keeps only wins that hold up.
- **The demo campaign is a TPS hill climb.** Thermite searches for the prompt and request settings that get the highest tokens/sec from Kimi K3.1 Pro on Cerebras. The kit measures TPS and is the judge. The result is our TPS-bounty entry, and the story films well: agents racing to make the model faster, steered by chat.
- **Speed is visible on camera:** OpenClaw/Kimi replies and Thermite trial turnaround in seconds. Side-by-side: the same OpenClaw agent on a GPU-served model (local GB10 or a hosted GPU provider) visibly crawling.

Why this role: the rules need Kimi-on-Cerebras as a central component **and** the OpenClaw harness. Thermite's own agents don't run on OpenClaw, so OpenClaw has to be the operator in the loop, not an add-on.

## Constraints to design around

- **100K tokens/min, 100 requests/min per participant.** Thermite lanes on Kimi plus the TPS kit's own measurement calls share this budget. Run 1–2 lanes; keep the kit's calls short.
- The **TPS bounty's measurement and entry rules aren't published.** Ask at kickoff or in `#hackathon-support`.
- Reasoning is off by default (`reasoning_effort` turns it on). It matters for TPS and for agent quality.

## Done before the window (setup only)

- Node 24.22.3 (nvm default), OpenClaw 2026.11.6 installed.
- `~/.openclaw/openclaw.json`: Cerebras provider with Kimi K3.1 Pro (plus `gpt-oss-120b` as a stand-in until Kimi access opens), gateway on loopback :18789 with a token, Thermite MCP over streamable HTTP with a 12-tool filter. Secrets live in `~/.openclaw/.env` (600).
- Gateway runs as a systemd user service (`openclaw-gateway.service`).
- **`mission` agent**: workspace [agent/](agent/), only the Thermite tools, no skills, tool search off. A request is ~25 KB (~6–7K tokens), down from ~84 KB (~21K) for the default `main` agent.
- **Verified 2026-11-20:** `scripts/openclaw_smoke.sh cerebras/gpt-oss-120b` runs OpenClaw → Cerebras → `thermite__list_rigs` → answer in 3.8 s. `scripts/cerebras_smoke.py --model gpt-oss-120b` gives ~1,400 TPS and 275 ms TTFT, and Cerebras returns `time_info` (server-side completion time) for TPS.
- Config template [config/openclaw.example.json5](config/openclaw.example.json5) plus [scripts/setup-openclaw.sh](scripts/setup-openclaw.sh) to reproduce the setup; [scripts/record.sh](scripts/record.sh) records the screen to a ≤60 s 1080p MP4 (ffmpeg 6.1 and OBS 30 installed; capture tested).
- **Not yet verified:** Kimi itself. The key currently gets 404 `model_not_found` for `moonshotai-kimi-k3.1-pro-trial`, because preview access isn't live yet. Its free-tier limits are 5 RPM / 30K TPM for gpt-oss-120b.

## Build in the window (core work)

1. The Thermite kit that measures Kimi TPS on Cerebras, plus a contract for the hill climb, and Thermite's worker model set to Kimi on Cerebras.
2. The OpenClaw agent's persona/skill as Thermite mission control, plus tool approval set so the demo runs without prompts.
3. The GPU side-by-side and recording the ≤60 s video.
4. The README, a public GitHub repo, and the X/Reddit posts.
