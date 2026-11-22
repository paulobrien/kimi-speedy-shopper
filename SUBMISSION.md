# Submission drafts

Deadline: **Sun 22 Nov 2026, 10:00 PT (18:00 GMT)**. Fill in the handles, numbers and links marked `<…>`.

## X post (required)

> Speedy Shopper 🎅⚡ An OpenClaw agent on Kimi K3.1 Pro finds 5 real Christmas gifts with links in seconds. Overnight, Thermite autoresearch tested 8 speed ideas against a judge it can't touch. One held up: +8% decode speed over 18 paired runs, every gift still a live product page.
>
> Team: @paulobrien
> Code: https://github.com/paulobrien/kimi-speedy-shopper
>
> @Cerebras @Kimi_Moonshot #KimiOnCerebras

(Video attached, ≤60 s.)

## Reddit r/cerebras (flair "Kimi K3.1 Pro Hackathon")

**Title:** Speedy Shopper: a Kimi K3.1 Pro gift-finding agent that an autoresearch loop tuned for speed overnight

- **Project name:** Speedy Shopper
- **Team members:** u/paulobrien
- **Description:** Speedy Shopper is an OpenClaw agent running on Kimi K3.1 Pro on Cerebras. It searches the web and returns five real Christmas gifts with product links, and a verifier opens every link to prove it's a live product page. We then pointed Thermite, an open-source autoresearch system, at the agent: its workers rewrite the agent's instructions and request settings, and its judge reruns the shopper on random gift briefs, keeping a change only if the gifts are still real and Kimi's server-side decode speed went up. A second OpenClaw agent on Kimi is mission control for the campaign, in chat.
- **GitHub:** https://github.com/paulobrien/kimi-speedy-shopper
- **Demo video:** <upload or YouTube link>

## LinkedIn post

> This weekend I built **Speedy Shopper** for the Cerebras × Moonshot AI hackathon: an AI agent that finds five real Christmas gifts, with working product links, in seconds.
>
> It runs on Kimi K3.1 Pro on Cerebras inside OpenClaw, an open-source agent harness. Every link is checked by a verifier that opens the page and confirms it's a live product, so there are no made-up gifts.
>
> Then I let an autoresearch loop loose on it overnight. Thermite, an open-source autoresearch tool, had its agents rewrite the shopper's instructions and settings, while a judge they can't touch re-ran the shopper on random gift requests. It kept a change only if the gifts were still real *and* the model decoded faster. Of 8 ideas, one held up: asking for one long, templated search instead of a few short queries, worth ~8% over 18 paired runs. Most of the folklore (greedy decoding, more reasoning) didn't survive measurement, and two "speed tricks" made the agent invent links.
>
> Three things I learned:
> - Same model, different hardware: Kimi K3.1 Pro decoded ~8× faster on Cerebras than on Moonshot AI's own API.
> - The score is a mean over model calls, so short calls drag it down. Make every call long and predictable.
> - Speed tricks can quietly break correctness. Keep a verifier in the loop that the agent can't edit.
>
> Speed guide and code: https://github.com/paulobrien/kimi-speedy-shopper
>
> #AI #Agents #Cerebras #OpenSource

## Speed Bounty (Discord #share-your-demo)

> Speed Bounty entry: <N from the recording> TPS
>
> Santa's Speedy Shopper on the patched OpenClaw web chat, Kimi K3.1 Pro on Cerebras. The video shows the mean tok/s readout and the five products with their links. The shopper's prompt and settings were tuned by a Thermite hill climb on the same metric. Repo: https://github.com/paulobrien/kimi-speedy-shopper

## Video shot list (≤ 60 s, standard OpenClaw)

| Time | Shot |
| --- | --- |
| 0–3 s | Title card: "Speedy Shopper: Kimi K3.1 Pro on Cerebras + OpenClaw" |
| 3–18 s | OpenClaw web chat, Speedy Shopper agent: type "Find five Christmas gifts for a cat owner". Five gifts with links appear. Show the timer and tok/s from `tps_proxy.py --summary runs/gateway_calls.jsonl` |
| 18–25 s | Terminal: `verify_gifts.py` ticks all five links green (live product pages) |
| 25–35 s | `scripts/race.py`: the same prompt on Kimi K3.1 Pro on Cerebras vs Moonshot AI's own API, clocks from first token; Cerebras finishes while Moonshot is still streaming (~8–13× decode speed) |
| 35–50 s | Thermite dashboard: the speedy-shopper campaign's champion chart climbing; mission control in chat answering "How's the speed run going?" |
| 50–60 s | End card: ~450 tok/s, +8% from the overnight hill climb, ~8× Moonshot's API; repo link, #KimiOnCerebras |

Before recording: pause the Thermite run so it doesn't share the token budget, hide notifications and keys, and use a fresh chat session.
