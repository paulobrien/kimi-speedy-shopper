# Submission drafts

Deadline: **Sun 22 Nov 2026, 10:00 PT (18:00 GMT)**. Fill in the links and numbers marked `<…>`. Videos and image are in `runs/video/` (not in git).

## X post (required): post as a thread

**1/** (attach `public.mp4`). This is the official submission post, so it carries every required field.

> 🎅⚡ Speedy Shopper: an OpenClaw agent on Kimi K3.1 Pro that finds 5 real Christmas gifts with live product links in seconds. On @Cerebras it decodes 9.6× faster than on Moonshot's own API.
>
> Team: @paulobrien
> GitHub: https://github.com/paulobrien/kimi-speedy-shopper
>
> @Kimi_Moonshot #KimiOnCerebras 🧵

**2/**

> Then we tried something different 🧪
>
> Overnight, Thermite autoresearch (huge thanks @iamMrDuncan 🙏) hill-climbed it: AI workers rewrote its prompt and settings while a judge they can't touch re-ran every idea. Only faster changes with every link still real survived.

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
- **Description:** Speedy Shopper is an OpenClaw agent on Kimi K3.1 Pro on Cerebras that finds five real Christmas gifts with working product links in seconds, decoding 9.6× faster than the same model on Moonshot's own API. Instead of hand-tuning it, I pointed Thermite, an open-source autoresearch system, at it overnight: AI workers rewrote its prompt and settings while a judge they couldn't touch re-ran it 857 times on random gift briefs. A change only survived if it decoded faster *and* every link was still a real, live product page. The winner was one long, templated search call (+7.7% decode speed over 18 paired runs), while temperature 0, extra reasoning and two link-inventing "speed tricks" were all rejected.
- **GitHub:** https://github.com/paulobrien/kimi-speedy-shopper
- **Demo video:** upload `public.mp4` directly (or paste a YouTube link)

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

> Speed Bounty entry: 504 TPS 🎅⚡
>
> Santa's Speedy Shopper: OpenClaw + Kimi K3.1 Pro on Cerebras, patched web chat. Five real gifts, five live product links (all re-opened and verified), and the mean tok/s readout on screen. The shopper's prompt was tuned for exactly this metric by an overnight Thermite hill climb: 857 judged runs, and only changes that were faster AND kept every link real survived. Repo: https://github.com/paulobrien/kimi-speedy-shopper

## What's in the videos

**Public demo** (58 s, standard OpenClaw, 1080p, no audio):

| Time | Shot |
| --- | --- |
| 0–3 s | Title card |
| 3–27 s | Standard OpenClaw web chat: "Find five Christmas gifts for a home barista on a budget". The Cerebras queue wait is fast-forwarded with an on-screen label (queue time isn't counted in TPS); the agent's work plays in real time. |
| 27–32 s | That run, measured: 427 tok/s mean over 4 calls (server-side, from our proxy), 5/5 links re-opened and verified |
| 32–49 s | `race.py` replay: same prompt on Cerebras vs Moonshot AI's own API, clocks from first token: 285 vs 30 tok/s, 9.6× |
| 49–55 s | Thermite verdicts chart with 95% intervals |
| 55–58 s | End card: repo link and tags |

**Speed Bounty** (15 s, patched OpenClaw web chat, Discord only): our top run, "a dad who likes cooking and barbecue" (Sun ~13:30 GMT, worked for 11 s), with the patch's readout 504 tok/s mean · 584 p90 (server) and the five products with links, then a card showing all five re-verified live. A live-recorded take at 483 tok/s (5/5) is kept as `bounty483.mp4`.
