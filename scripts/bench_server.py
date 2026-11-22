#!/usr/bin/env python3
"""HTTP front for shopper_bench, so Thermite's judge (in a container) can score a candidate.

The judge's run step POSTs the candidate's shopper files; this service runs the
shopper on this machine's standard OpenClaw, through the TPS proxy, one attempt
at a time, and answers with the scores.

    python3 scripts/bench_server.py --host 172.17.0.1 --port 8898   # Docker bridge only

POST /bench  {"token": "...", "files": {"AGENTS.md": "...", "settings.json": "..."},
              "set": "visible"|"held", "reps": 2}
GET  /health

Briefs are drawn at random from the set on every call, so a candidate can't
tune for (or cache) particular searches. settings.json is checked against an
allowlist: the model, provider and tools are fixed by config/shopper.json5.
"""

import argparse
import json
import os
import random
import secrets
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import shopper_bench  # noqa: E402

BRIEFS = {
    "visible": [
        "a 10-year-old who loves science", "a dad who likes cooking and barbecue",
        "a teenager into music and headphones", "a gardener grandmother",
        "a coffee-obsessed coworker, under $50", "a board-game fan",
        "a runner training for a marathon", "a cat owner",
    ],
    "held": [
        "a teenager who loves drawing", "someone who's always cold at home",
        "a home barista on a budget", "a beginner photographer",
        "a toddler who loves trucks", "a book lover who has everything",
    ],
}
THINKING = {"low", "medium", "high", "max", "minimal"}
PARAMS = {"temperature", "top_p", "maxTokens", "frequency_penalty", "presence_penalty"}
MAX_FILE = 64_000
LOCK = threading.Lock()


def check_settings(raw):
    s = json.loads(raw)
    if not isinstance(s, dict):
        raise ValueError("settings.json must be an object")
    extra = set(s) - {"thinking", "params", "notes"}
    if extra:
        raise ValueError(f"settings.json: unknown keys {sorted(extra)}; allowed: thinking, params, notes")
    if "thinking" in s and s["thinking"] not in THINKING:
        raise ValueError(f"settings.json: thinking must be one of {sorted(THINKING)}")
    params = s.get("params") or {}
    if not isinstance(params, dict) or set(params) - PARAMS:
        raise ValueError(f"settings.json: params may only set {sorted(PARAMS)}")
    for k, v in params.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise ValueError(f"settings.json: params.{k} must be a number")
    return s


INFRA = ("No callable tools remain", "no registered", "ECONNRESET", "gateway closed",
         "'kind': 'timeout'", "timed out after")
BUDGET_S = 1380  # the kit's run step gives up after 1450 s, including time waiting for the lock


def infra_failure(a):
    """A run that never reached the model because the harness or a tool server failed."""
    rs = " ".join(a.get("reasons", []))
    # A timeout while Cerebras queues the request is infra too, even after a first call went through.
    return ("openclaw run failed" in rs or "timed out after" in rs) and any(m in rs for m in INFRA)


def run_bench(req, args):
    files = req.get("files") or {}
    if "AGENTS.md" not in files or "settings.json" not in files:
        raise ValueError("need files AGENTS.md and settings.json")
    check_settings(files["settings.json"])
    briefs = BRIEFS.get(req.get("set", "visible"))
    if not briefs:
        raise ValueError("set must be visible or held")
    t0 = time.time()
    reps = max(1, min(int(req.get("reps", 2)), 4))
    picks = random.sample(briefs, reps)
    with tempfile.TemporaryDirectory(prefix="cand-") as cand:
        for name, text in files.items():
            if "/" in name or name.startswith(".") or len(text) > MAX_FILE:
                raise ValueError(f"bad file {name!r}")
            with open(os.path.join(cand, name), "w") as f:
                f.write(text)
        attempts, infra = [], 0
        with LOCK:  # one attempt at a time: the proxy log is attributed by position
            for i, brief in enumerate(picks):
                for _ in range(3):  # infra hiccups (MCP didn't register, queue timeouts) aren't the candidate's fault
                    left = BUDGET_S - (time.time() - t0)
                    per = min(args.timeout, int(left / (reps - i)) - 70)
                    if per < 120:
                        break
                    ns = SimpleNamespace(base_url=args.base_url, log=args.log, timeout=per, min_verified=4)
                    a = shopper_bench.attempt(cand, brief, ns)
                    if not infra_failure(a):
                        attempts.append(a)
                        break
                    infra += 1
                    time.sleep(10)
    if not attempts:
        raise ValueError("no scorable attempt: every run hit an infrastructure failure (Cerebras queue timeout or MCP)")
    valid = [a for a in attempts if a["valid"]]
    tps = [a["mean_tps"] for a in valid]
    return {
        "pass": len(valid) >= max(1, (len(attempts) + 1) // 2),
        "reasons": sorted({r for a in attempts for r in a["reasons"]}),
        "mean_tps": sum(tps) / len(tps) if tps else 0,
        "valid_rate": len(valid) / len(attempts),
        "infra_retries": infra,
        "calls": sum(a["calls"] for a in attempts) / len(attempts),
        "wall_s": sum(a["wall_s"] for a in attempts) / len(attempts),
        "attempts": [{k: a[k] for k in ("brief", "valid", "reasons", "mean_tps", "calls", "per_call",
                                        "wall_s", "answer")} for a in attempts],
    }


class Handler(BaseHTTPRequestHandler):
    token = ""
    args = None

    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % a))

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, {"ok": True}) if self.path == "/health" else self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/bench":
            return self._send(404, {"error": "not found"})
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        except ValueError:
            return self._send(400, {"error": "bad json"})
        if not secrets.compare_digest(str(req.get("token", "")), self.token):
            return self._send(403, {"error": "bad token"})
        try:
            res = run_bench(req, self.args)
        except ValueError as e:
            return self._send(200, {"pass": False, "reasons": [str(e)], "mean_tps": 0, "valid_rate": 0})
        except Exception as e:  # noqa: BLE001
            return self._send(500, {"error": f"{type(e).__name__}: {e}"})
        with open(os.path.join(REPO, "runs", "bench_server.jsonl"), "a") as f:
            f.write(json.dumps({"t": time.time(), "set": req.get("set"), **res}) + "\n")
        self._send(200, res)


def main():
    shopper_bench.load_env()
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="172.17.0.1")
    p.add_argument("--port", type=int, default=8898)
    p.add_argument("--token-file", default=os.path.join(REPO, "kit", ".bench-token"))
    p.add_argument("--base-url", default="http://127.0.0.1:8899/v1")
    p.add_argument("--log", default=os.path.join(REPO, "runs", "tps_calls.jsonl"))
    p.add_argument("--timeout", type=int, default=600)
    a = p.parse_args()
    Handler.token = open(a.token_file).read().strip()
    Handler.args = a
    os.makedirs(os.path.join(REPO, "runs"), exist_ok=True)
    print(f"bench_server on {a.host}:{a.port}", file=sys.stderr)
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    sys.exit(main())
