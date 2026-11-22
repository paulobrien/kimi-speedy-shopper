# Submission drafts

Deadline: **Sun 22 Nov 2026, 10:00 PT (18:00 GMT)**. Fill in the links and numbers marked `<…>`. Videos and image are in `runs/video/` (not in git).

## X post (required): post as a thread

**1/** (attach `public.mp4`). This is the official submission post, so it carries every required field.

> Speedy Shopper 🎅 is an OpenClaw agent on Kimi K3.1 Pro that finds five real Christmas gifts with working links in seconds. On @Cerebras it decodes about 9.6x faster than on Moonshot's own API.
>
> Team: @paulobrien
> GitHub: https://github.com/paulobrien/kimi-speedy-shopper
>
> @Kimi_Moonshot #KimiOnCerebras

**2/**

> The part I'm most pleased with: I didn't hand-tune it. Thermite (thanks @iamMrDuncan!) ran an autoresearch loop overnight. AI workers rewrote the prompt and settings, and a separate judge re-ran every change. Faster wasn't enough, though. Every link still had to be real.

**3/** (attach the image)

> By morning it had run the shopper 857 times and checked 4,000+ links. One change held up: a single long, templated search, about 8% faster.
>
> Temperature 0 was slower, extra reasoning did nothing, and two shortcuts got caught inventing links.
>
> Write-up: https://github.com/paulobrien/kimi-speedy-shopper

## Reddit r/cerebras (flair "Kimi K3.1 Pro Hackathon")

**Title:** I let an autoresearch loop tune my Kimi K3.1 Pro shopping agent overnight

- **Project name:** Speedy Shopper
- **Team members:** u/paulobrien
- **Description:** Speedy Shopper is an OpenClaw agent on Kimi K3.1 Pro on Cerebras that finds five real Christmas gifts with working product links in seconds, and decodes about 9.6x faster than the same model on Moonshot's own API. Rather than hand-tune it, I pointed Thermite (open-source autoresearch) at it overnight: AI workers rewrote the prompt and settings, and a judge they couldn't touch re-ran the shopper 857 times on random gift requests. A change only stuck if it was faster and every link was still a real, live product page. One did (a single long, templated search, about 8% faster over 18 paired runs), while temperature 0, extra reasoning and two link-inventing shortcuts all got thrown out.
- **GitHub:** https://github.com/paulobrien/kimi-speedy-shopper
- **Demo video:** upload `public.mp4` directly (or paste a YouTube link)

## LinkedIn post (attach `runs/video/linkedin.png`)

> After the success in the first Cerebras hackathon, I figured I'd give this weekend's one a go too!
>
> The challenge was festive: build an agent that finds five real Christmas gifts, with working product links, as fast as possible. Mine is called Speedy Shopper. It runs Kimi K3.1 Pro on Cerebras inside OpenClaw, and it decodes about 9.6x faster there than the same model does on Moonshot's own API. A verifier opens every link it returns, so there are no made-up gifts.
>
> This time I wanted to try something a bit different. Instead of tuning the agent by hand, I gave it to Thermite, an open-source autoresearch tool, and let it hill-climb overnight. AI workers proposed changes to the shopper's instructions and settings. A separate judge, which they had no way to influence, re-ran the shopper on random gift requests and only kept a change if it was faster and every gift was still a real, live product.
>
> By the morning it had run the shopper 857 times and checked over 4,000 links. Only one idea survived: asking for one long, templated search instead of several short ones, which made it about 8% faster across 18 paired runs. Temperature 0 made it slower, extra reasoning made no difference, and two "speed tricks" were caught inventing links and thrown out.
>
> It might look like trivial festive fun, but the ideas underneath apply directly to how we use AI in business:
>
> - Hill-climbing works for accuracy, not just speed. Swap "tokens per second" for "correct answers on a held-out test set" and the same loop can tune a support assistant, a document-extraction pipeline or a coding agent overnight.
> - Keep whatever is making the changes away from whatever is scoring them. That separation is the difference between real improvement and an AI quietly gaming its own metric.
> - Check outputs against the real world. The link checks are what caught the shortcuts that invented results. Any agent that cites sources, updates records or takes actions needs an independent check like that before anything reaches a customer.
> - Measure with repeats, not anecdotes. Individual runs varied by around 25%, and only paired runs on random inputs separated real gains from noise. The same applies when comparing models, prompts or vendors.
> - Where you run a model matters as much as which model you pick, especially for real-time and agentic work.
> - Test the common advice on your own workload. Here, "use temperature 0" made things slower and "add more reasoning" did nothing.
>
> The code and a full write-up are on GitHub: https://github.com/paulobrien/kimi-speedy-shopper
>
> Thanks to Cerebras and Moonshot AI for another great weekend.
>
> #AI #Agents #Cerebras #KimiOnCerebras #OpenSource

## Speed Bounty (Discord #share-your-demo)

> Speed Bounty entry: 504 TPS
>
> Santa's Speedy Shopper, running OpenClaw and Kimi K3.1 Pro on Cerebras in the patched web chat. The video shows the TPS readout and the five products with their links, all re-checked as live product pages. The prompt was tuned for this metric by an overnight Thermite hill climb (857 judged runs, and a change only stuck if it was faster and every link stayed real). Repo: https://github.com/paulobrien/kimi-speedy-shopper

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
