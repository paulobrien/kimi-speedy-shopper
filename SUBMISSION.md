# Submission drafts

Deadline: **Sun 22 Nov 2026, 10:00 PT (18:00 GMT)**. Fill in the links and numbers marked `<…>`. Videos and image are in `runs/video/` (not in git).

## X post (required): post as a thread

**1/** (attach the public video)

> 🎅⚡ Meet Speedy Shopper: an OpenClaw agent on Kimi K3.1 Pro that finds 5 REAL Christmas gifts, with live product links, in seconds.
>
> On @Cerebras it decoded 9.6× faster than the same model on Moonshot's own API.
>
> @Kimi_Moonshot #KimiOnCerebras 🧵👇

**2/**

> Then we tried something different 🧪
>
> Overnight, Thermite autoresearch (huge thanks @iamMrDuncan 🙏) hill-climbed it: AI workers rewrote its prompt and settings while a judge they can't touch re-ran every idea on random gift requests. Only faster changes that kept every link real survived.

**3/** (attach the image)

> 18 hours. 857 shopper runs. 4,000+ links checked.
>
> Winner: one long templated search, +7.7% decode speed over 18 paired runs ⚡
> Busted: temperature 0 (slower), extra reasoning (no gain), two "speed tricks" caught inventing links 🚫
>
> Code + speed guide 👉 https://github.com/paulobrien/kimi-speedy-shopper

## Reddit r/cerebras (flair "Kimi K3.1 Pro Hackathon")

**Title:** I let an autoresearch loop tune my Kimi K3.1 Pro shopping agent overnight: 857 runs, 4,000+ verified links, one real speed win

- **Project name:** Speedy Shopper
- **Team members:** u/paulobrien
- **Description:** Speedy Shopper is an OpenClaw agent on Kimi K3.1 Pro on Cerebras that finds five real Christmas gifts with working product links in seconds, and a verifier opens every link to prove it's a live product page. On Cerebras it decoded 9.6× faster than the same model on Moonshot's own API. Then I did something a bit different: instead of hand-tuning, I pointed Thermite (open-source autoresearch) at the agent overnight. Its AI workers rewrote the shopper's prompt and settings, and a judge they couldn't touch re-ran the shopper 857 times on random gift briefs, keeping a change only if it decoded faster *and* every link was still real. The winner: one long, templated search call, +7.7% decode speed over 18 paired runs. Temperature 0 was slower, more reasoning did nothing, and two "speed tricks" were caught inventing links. Everything's measured, and it's all in the repo's speed guide.
- **GitHub:** https://github.com/paulobrien/kimi-speedy-shopper
- **Demo video:** <upload or YouTube link>

## LinkedIn post (attach `runs/video/linkedin.png`)

> After the success in the first Cerebras hackathon, I figured I'd give this weekend's one a go too! 🎅⚡
>
> Meet **Speedy Shopper**: an AI agent that finds five real Christmas gifts, with working product links, in seconds. It runs on Kimi K3.1 Pro on Cerebras inside OpenClaw, and on Cerebras it decoded **9.6× faster** than the same model on Moonshot's own API. Every link gets opened by a verifier, so there are no made-up gifts.
>
> But this time I wanted to try something a bit different. Instead of hand-tuning the agent, I handed it to **Thermite**, an open-source autoresearch tool, and let it hill-climb overnight. AI workers proposed and wrote changes to the shopper's instructions and settings; an independent judge, which they couldn't touch, re-ran the shopper on random gift requests and only accepted a change if it was faster *and* every gift was still a real, live product page.
>
> By morning: **18 hours, 857 shopper runs and 4,000+ links opened and checked.**
>
> What survived, and what didn't:
> ✅ One long, templated search instead of a few short ones: **+7.7% decode speed** over 18 paired runs
> ❌ Temperature 0: slower, not faster
> ❌ More reasoning: no measurable effect
> 🚫 Two "speed tricks" were caught inventing or picking wrong links, and rejected
>
> It might look like trivial festive fun, but the ideas underneath apply directly to how we put AI to work in business:
>
> 🎯 **Hill-climb for accuracy, not just speed.** Swap "tokens per second" for "correct answers on a held-out test set" and the same loop tunes the prompts, settings and tool use of a support assistant, a document-extraction pipeline or a coding agent, overnight, while the team sleeps.
> 🔒 **Keep the optimiser away from the judge.** The agents proposing changes could never touch the scoring. That separation is the difference between genuine improvement and an AI quietly gaming its own metric.
> ✅ **Verify against the real world.** Every link was re-opened and checked, and that's what caught the "speed tricks" that invented results. Any agent that cites sources, updates records or takes actions needs an independent check like this before anything reaches a customer.
> 📏 **Measure with repeats, not anecdotes.** Individual runs swung by ±25%; only paired runs on random inputs separated real gains from noise. The same discipline applies when comparing models, prompts or vendors.
> ⚖️ **Benchmark the platform, not just the model.** The same model decoded 9.6× faster on Cerebras. For real-time and agentic workloads, where you run it matters as much as which model you pick.
> 🧪 **Test the folklore on your own workload.** "Use temperature 0" and "add more reasoning" are common advice; here, one made things slower and the other did nothing.
>
> The code and a full speed guide are open source: https://github.com/paulobrien/kimi-speedy-shopper
>
> Thanks to Cerebras and Moonshot AI for another brilliant weekend!
>
> #AI #Agents #Cerebras #KimiOnCerebras #OpenSource #Autoresearch

## Speed Bounty (Discord #share-your-demo)

> Speed Bounty entry: 483 TPS 🎅⚡
>
> Santa's Speedy Shopper: OpenClaw + Kimi K3.1 Pro on Cerebras, patched web chat. Five real gifts, five live product links (all re-opened and verified), and the mean tok/s readout on screen. The shopper's prompt was tuned for exactly this metric by an overnight Thermite hill climb: 857 judged runs, and only changes that were faster AND kept every link real survived. Repo: https://github.com/paulobrien/kimi-speedy-shopper

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
