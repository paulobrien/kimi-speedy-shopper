#!/usr/bin/env python3
"""Side-by-side race: Kimi K3.1 Pro on Cerebras vs the same model on GPUs (OpenRouter).

Sends the same prompt to both at once and streams both answers side by side in the
terminal, with live tokens/sec. Inference speed is what's compared, so each side's clock
starts at its own first token. Time spent waiting in a provider's queue is shown on its
header but excluded (Cerebras's preview endpoint can queue for minutes under hackathon load).

    python3 scripts/race.py                      # replay mode (default)
    python3 scripts/race.py --live               # draw as tokens arrive (when queues are short)
    python3 scripts/race.py --prompt "..." --max-tokens 1200

Replay mode collects both streams with their arrival times, then plays them back in real
time from each side's first token, so a long queue on either side doesn't change the race.
Keys come from the environment or ~/.openclaw/.env: CEREBRAS_API_KEY, OPENROUTER_API_KEY.
Standard library only.
"""

import argparse
import json
import os
import shutil
import sys
import textwrap
import threading
import time
import urllib.request

DEFAULT_PROMPT = ("Write a gift guide for a cat owner: five Christmas gift ideas, "
                  "each with a name, a price range and a short paragraph on why it's a good pick.")
SIDES = {
    "cerebras": {"label": "Kimi K3.1 Pro · Cerebras", "url": "https://api.cerebras.ai/v1/chat/completions",
                 "model": "moonshotai-kimi-k3.1-pro-trial", "key": "CEREBRAS_API_KEY",
                 "url_env": "RACE_CEREBRAS_URL"},
    "gpu": {"label": "Kimi K3.1 Pro · GPU (OpenRouter)", "url": "https://openrouter.ai/api/v1/chat/completions",
            "model": "moonshotai/kimi-k3.1-pro", "key": "OPENROUTER_API_KEY", "url_env": "RACE_GPU_URL",
            "extra": {"provider": {"sort": "throughput", "ignore": ["Cerebras"]}}},
}
DIM, BOLD, RESET, GREEN, CYAN = "\x1b[2m", "\x1b[1m", "\x1b[0m", "\x1b[32m", "\x1b[36m"


def load_env():
    path = os.path.expanduser("~/.openclaw/.env")
    if os.path.exists(path):
        for line in open(path):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                if v and k not in os.environ:
                    os.environ[k] = v


class Stream:
    def __init__(self, name, args):
        self.name, self.cfg, self.args = name, SIDES[name], args
        self.events = []          # (seconds since first token, text, is_reasoning)
        self.t_send = self.t_first = self.t_last = None
        self.usage = self.time_info = self.provider = self.error = None
        self.done = False

    def run(self):
        c = self.cfg
        body = {"model": c["model"], "messages": [{"role": "user", "content": self.args.prompt}],
                "max_tokens": self.args.max_tokens, "stream": True,
                "stream_options": {"include_usage": True}, "reasoning_effort": self.args.reasoning_effort,
                **c.get("extra", {})}
        headers = {"Authorization": f"Bearer {os.environ.get(c['key'], '')}", "Content-Type": "application/json"}
        url = os.environ.get(c["url_env"], c["url"])
        self.t_send = time.perf_counter()
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), headers)
            with urllib.request.urlopen(req, timeout=900) as r:
                for raw in r:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:") or line[5:].strip() == "[DONE]":
                        continue
                    ev = json.loads(line[5:])
                    self.usage = ev.get("usage") or self.usage
                    self.time_info = ev.get("time_info") or self.time_info
                    self.provider = ev.get("provider") or self.provider
                    for ch in ev.get("choices", []):
                        d = ch.get("delta", {})
                        for text, reasoning in ((d.get("reasoning") or d.get("reasoning_content"), True),
                                                (d.get("content"), False)):
                            if text:
                                now = time.perf_counter()
                                if self.t_first is None:
                                    self.t_first = now
                                self.t_last = now
                                self.events.append((now - self.t_first, text, reasoning))
        except Exception as e:  # noqa: BLE001
            self.error = f"{type(e).__name__}: {e}"[:200]
        self.done = True

    @property
    def wait_s(self):
        return (self.t_first - self.t_send) if self.t_first else None

    @property
    def tokens(self):
        return (self.usage or {}).get("completion_tokens") or sum(1 for _ in self.events)

    def decode_s(self):
        return (self.t_last - self.t_first) if self.t_first and self.t_last else None

    def tps(self):
        d = self.decode_s()
        return (self.tokens - 1) / d if d else None


def render(streams, ts, width, height, final=False):
    if not isinstance(ts, (list, tuple)):
        ts = [ts] * len(streams)
    col = (width - 3) // 2
    out = ["\x1b[H\x1b[2J"]
    heads, bodies = [], []
    for s, t in zip(streams, ts):
        shown = [(x, txt, r) for x, txt, r in s.events if x <= t]
        chars = sum(len(txt) for _, txt, _ in s.events) or 1
        frac = sum(len(txt) for _, txt, _ in shown) / chars
        toks = s.tokens * frac
        el = min(t, s.decode_s() or 0)
        finished = s.events and t >= s.events[-1][0]
        rate = (toks - 1) / el if el > 0.05 and toks > 1 else 0
        wait = f"queue+TTFT {s.wait_s:.1f}s (excluded)" if s.wait_s is not None else "waiting…"
        state = f"{GREEN}done in {s.decode_s():.1f}s{RESET}" if finished else f"{el:5.1f}s"
        heads.append([f"{BOLD}{s.cfg['label']}{RESET}",
                      f"{CYAN}{rate:6.0f} tok/s{RESET}  {int(toks):5d} tokens  {state}",
                      f"{DIM}{wait}{RESET}"])
        text = "".join(txt for _, txt, _ in shown)
        lines = []
        for para in text.split("\n"):
            lines.extend(textwrap.wrap(para, col) or [""])
        body_h = height - 6
        lines = lines[-body_h:]
        bodies.append((lines, None))
    for i in range(3):
        out.append(f"{pad(heads[0][i], col)} │ {heads[1][i]}\n")
    out.append("─" * col + "─┼─" + "─" * col + "\n")
    for i in range(height - 6):
        left = bodies[0][0][i] if i < len(bodies[0][0]) else ""
        right = bodies[1][0][i] if i < len(bodies[1][0]) else ""
        out.append(f"{left:<{col}} │ {right}\n")
    if final:
        a, b = streams
        if a.tps() and b.tps():
            out.append(f"{BOLD}Cerebras {a.tps():.0f} tok/s vs GPU {b.tps():.0f} tok/s: "
                       f"{a.tps() / b.tps():.1f}× faster decoding{RESET}  "
                       f"{DIM}(clocks start at each side's first token){RESET}\n")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def pad(s, n):
    visible = len(s) - sum(len(x) for x in (DIM, BOLD, RESET, GREEN, CYAN) for _ in range(s.count(x)))
    return s + " " * max(0, n - visible)


def main():
    load_env()
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", default=DEFAULT_PROMPT)
    p.add_argument("--max-tokens", type=int, default=1200)
    p.add_argument("--reasoning-effort", default="low")
    p.add_argument("--gpu-provider", help='pin the OpenRouter side to one provider, e.g. "Moonshot AI" '
                   "(default: OpenRouter's fastest by throughput, never Cerebras)")
    p.add_argument("--live", action="store_true", help="draw as tokens arrive instead of replaying")
    p.add_argument("--json", metavar="FILE", help="also save both streams' timings here")
    a = p.parse_args()
    if a.gpu_provider:
        SIDES["gpu"]["extra"] = {"provider": {"only": [a.gpu_provider], "allow_fallbacks": False}}
        SIDES["gpu"]["label"] = f"Kimi K3.1 Pro · {a.gpu_provider} (OpenRouter)"
    streams = [Stream("cerebras", a), Stream("gpu", a)]
    threads = [threading.Thread(target=s.run, daemon=True) for s in streams]
    for th in threads:
        th.start()
    width, height = shutil.get_terminal_size((160, 40))
    if a.live:
        while not all(s.done for s in streams):
            render_live(streams, time.perf_counter(), width, height)
            time.sleep(1 / 20)
        render_live(streams, time.perf_counter(), width, height, final=True)
    else:
        sys.stdout.write(f"{DIM}Collecting both streams (queue time is excluded)…{RESET}\n")
        while not all(s.done for s in streams):
            sys.stdout.write("\r" + "   ".join(
                f"{s.cfg['label']}: " + ("error" if s.error else "streaming" if s.t_first else "in queue")
                + (f" {len(s.events)} chunks" if s.t_first else "") for s in streams))
            sys.stdout.flush()
            time.sleep(0.25)
        end = max((s.events[-1][0] for s in streams if s.events), default=0)
        t0 = time.perf_counter()
        while True:
            t = time.perf_counter() - t0
            render(streams, t, width, height)
            if t > end + 0.3:
                break
            time.sleep(1 / 30)
        render(streams, end + 1, width, height, final=True)
    for s in streams:
        if s.error:
            print(f"{s.cfg['label']}: {s.error}")
    if a.json:
        json.dump({s.name: {"wait_s": s.wait_s, "decode_s": s.decode_s(), "tokens": s.tokens, "tps": s.tps(),
                            "server_time_info": s.time_info, "provider": s.provider} for s in streams},
                  open(a.json, "w"), indent=2)


def render_live(streams, now, width, height, final=False):
    # Each side's clock is its own time since its first token.
    ts = [1e9 if final else ((now - s.t_first) if s.t_first else -1) for s in streams]
    render(streams, ts, width, height, final)


if __name__ == "__main__":
    main()
