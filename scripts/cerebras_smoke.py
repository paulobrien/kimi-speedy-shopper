#!/usr/bin/env python3
"""Smoke-test Kimi K3.1 Pro on Cerebras and report speed.

Streams one chat completion and prints time to first token, wall-clock output
tokens/sec, and the server-side numbers from `usage` / `time_info` when the
API returns them. Standard library only.

    CEREBRAS_API_KEY=... python3 scripts/cerebras_smoke.py
    python3 scripts/cerebras_smoke.py --prompt "Write a haiku" --max-tokens 64
    python3 scripts/cerebras_smoke.py --reasoning-effort low

The key is read from the environment or from ./.env; it is never printed.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = os.environ.get("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1")
DEFAULT_MODEL = "moonshotai-kimi-k3.1-pro-trial"
DEFAULT_PROMPT = (
    "Write a 300-word explanation of how wafer-scale chips speed up LLM inference."
)


def load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if value and key not in os.environ:
                os.environ[key] = value


def main() -> int:
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.environ.get("CEREBRAS_MODEL", DEFAULT_MODEL))
    p.add_argument("--prompt", default=DEFAULT_PROMPT)
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--reasoning-effort", choices=["low", "medium", "high"])
    p.add_argument("--list-models", action="store_true")
    p.add_argument("--quiet", action="store_true", help="don't echo the output text")
    args = p.parse_args()

    key = os.environ.get("CEREBRAS_API_KEY")
    if not key:
        print("CEREBRAS_API_KEY is not set (env or ./.env).", file=sys.stderr)
        return 2
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    if args.list_models:
        req = urllib.request.Request(f"{BASE_URL}/models", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            for m in json.load(r).get("data", []):
                print(m.get("id"))
        return 0

    body = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "max_completion_tokens": args.max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if args.reasoning_effort:
        body["reasoning_effort"] = args.reasoning_effort

    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions", data=json.dumps(body).encode(), headers=headers
    )
    start = time.perf_counter()
    first = None
    chunks = 0
    usage = time_info = None
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            for raw in r:
                line = raw.decode().strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                ev = json.loads(data)
                usage = ev.get("usage") or usage
                time_info = ev.get("time_info") or time_info
                for choice in ev.get("choices", []):
                    delta = choice.get("delta", {})
                    text = delta.get("content") or delta.get("reasoning") or ""
                    if text:
                        if first is None:
                            first = time.perf_counter()
                        chunks += 1
                        if not args.quiet:
                            sys.stdout.write(text)
                            sys.stdout.flush()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:500]}", file=sys.stderr)
        return 1
    end = time.perf_counter()

    print("\n\n--- speed ---")
    print(f"model: {args.model}")
    if first is not None:
        print(f"time to first token: {(first - start) * 1000:.0f} ms")
    out_tokens = (usage or {}).get("completion_tokens")
    if out_tokens and first is not None and end > first:
        print(f"output tokens: {out_tokens}")
        print(f"client TPS (after first token): {out_tokens / (end - first):.0f}")
        print(f"client TPS (whole request): {out_tokens / (end - start):.0f}")
    else:
        print(f"content chunks: {chunks} (no usage returned)")
    if time_info:
        ct = time_info.get("completion_time")
        print(f"server time_info: {json.dumps(time_info)}")
        if out_tokens and ct:
            print(f"server TPS (completion_tokens / completion_time): {out_tokens / ct:.0f}")
    if usage:
        print(f"usage: {json.dumps(usage)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
