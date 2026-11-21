#!/usr/bin/env python3
"""Run Santa's Speedy Shopper end to end and score it.

One attempt = one headless OpenClaw turn (`openclaw agent exec`) on Kimi K3.1 Pro
on Cerebras, through scripts/tps_proxy.py, with a candidate configuration:

    <candidate>/AGENTS.md       the shopper's instructions (its workspace)
    <candidate>/settings.json   {"thinking": "low", "params": {"temperature": 1.0, ...}}

Each attempt is scored exactly as the official speed patch scores a session:
the mean (and p90) over model calls of completion_tokens / completion_time from
Cerebras's own timing. It's valid only if the answer has five distinct URLs that
are live product pages on 2+ retailers (scripts/verify_gifts.py), every URL
appeared in a tool result during that run, and none is written in the
candidate's own files (no hard-coding).

    python3 scripts/shopper_bench.py                       # shopper/, one random brief
    python3 scripts/shopper_bench.py --reps 3 --json
    python3 scripts/shopper_bench.py --candidate path/to/candidate --brief "a cat owner"

Needs the proxy running (python3 scripts/tps_proxy.py --log runs/tps_calls.jsonl
--dump-dir runs/dumps) and CEREBRAS_API_KEY in the environment or ~/.openclaw/.env.
Run attempts one at a time: the proxy log is attributed by position.
"""

import argparse
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from tps_proxy import read_log, summarize  # noqa: E402
from verify_gifts import CART_RE, PRICE_RE, extract_urls, verify  # noqa: E402


def bare(url):
    return re.sub(r"^https?://(www\.)?", "", url).rstrip("/")


def search_results(seen):
    """Every {url, title, excerpts} search/fetch result in this run's tool output."""
    out = []
    for line in seen.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        out.extend(r for r in obj.get("results") or [] if isinstance(r, dict) and r.get("url"))
    return out


def search_evidence(url, results):
    """Price + buy signal in this run's own search result for the URL.

    Big retailers (Argos, Currys...) block both plain fetches and Parallel's fetcher, but
    the search index crawled them; the excerpt for that URL is the evidence."""
    b = bare(url)
    for r in results:
        if bare(r["url"]) == b:
            text = " ".join(r.get("excerpts") or [])
            if PRICE_RE.search(text) and CART_RE.search(text):
                return True
    return False

DEFAULT_MESSAGE = "Find five Christmas gifts for {brief}."


def load_env():
    path = os.path.expanduser("~/.openclaw/.env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if v and k not in os.environ:
                    os.environ[k] = v


def openclaw_bin():
    found = shutil.which("openclaw")
    if found:
        return found
    nvm = os.path.expanduser("~/.nvm/versions/node")
    for v in sorted(os.listdir(nvm), reverse=True) if os.path.isdir(nvm) else []:
        cand = os.path.join(nvm, v, "bin", "openclaw")
        if os.path.exists(cand):
            return cand
    raise SystemExit("openclaw not found on PATH")


def tool_text(dumps):
    """All tool-result text the model was shown during the attempt."""
    out = []
    for path in dumps:
        try:
            body = json.load(open(path))
        except (OSError, ValueError):
            continue
        for m in body.get("messages") or []:
            if m.get("role") == "tool":
                c = m.get("content")
                out.append(c if isinstance(c, str) else json.dumps(c))
    return "\n".join(out)


def candidate_text(cand):
    out = []
    for root, _, files in os.walk(cand):
        for f in files:
            try:
                out.append(open(os.path.join(root, f), errors="replace").read())
            except OSError:
                pass
    return "\n".join(out)


def args_min_verified(args):
    return getattr(args, "min_verified", 4)


def attempt(cand, brief, args):
    settings = json.load(open(os.path.join(cand, "settings.json")))
    message = DEFAULT_MESSAGE.replace("{brief}", brief)
    with tempfile.TemporaryDirectory(prefix="shopper-") as tmp:
        ws = os.path.join(tmp, "ws")
        shutil.copytree(cand, ws, ignore=shutil.ignore_patterns("settings.json", "briefs.txt"))
        cfg = os.path.join(tmp, "openclaw.json5")
        tpl = open(os.path.join(REPO, "config", "shopper.json5")).read()
        open(cfg, "w").write(tpl.replace("__BASE_URL__", args.base_url))
        override = {"agents": {"defaults": {"params": settings.get("params") or {}}}}
        cmd = [openclaw_bin(), "agent", "exec", "--config", cfg, "--cwd", ws,
               "--thinking", settings.get("thinking", "low"), "--timeout", str(args.timeout),
               "--json", "--config-override", json.dumps(override), message]
        log_start = os.path.getsize(args.log) if os.path.exists(args.log) else 0
        t0 = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout + 60)
        except subprocess.TimeoutExpired:
            proc = SimpleNamespace(stdout="", stderr=f"timed out after {args.timeout + 60}s")
        wall = time.time() - t0
        time.sleep(0.3)  # let the proxy finish writing the last call
    calls = read_log(args.log, log_start)
    stats = summarize(calls)
    try:
        out = json.loads(proc.stdout)
    except ValueError:
        out = {"ok": False, "final": "", "error": (proc.stderr or proc.stdout)[-800:]}
    final = out.get("final") or ""
    urls = extract_urls(final)
    seen = tool_text([c["dump"] for c in calls if c.get("dump")])
    own = candidate_text(cand)
    not_from_tools = [u for u in urls if bare(u) not in seen]
    hard_coded = [u for u in urls if bare(u) in own]
    ver = verify(final) if urls else {"pass": False, "verified": 0, "urls": 0, "domains": 0, "results": []}
    results = search_results(seen)
    for r in ver["results"]:
        if not r["ok"] and r["status"] != 404 and search_evidence(r["url"], results):
            r["ok"] = True
            r["evidence"] = r["evidence"] + ["search result: price + buy button"]
    good = [r for r in ver["results"] if r["ok"]]
    ver["verified"] = len(good)
    # Dead = the shop says it doesn't exist (404/410) or the host doesn't answer and no fetcher
    # or search result vouches for it. Unconfirmed = blocked by bot protection (403/429/503).
    dead = [r for r in ver["results"] if not r["ok"] and (r["status"] in (404, 410) or
                                                        (r["status"] == 0 and not r["blocked"]))]
    ver["strict"] = len(urls) == 5 and len(good) == 5 and len({r["domain"] for r in good}) >= 2
    ver["pass"] = (len(urls) == 5 and len(good) >= args_min_verified(args) and not dead
                   and len({r["domain"] for r in good}) >= 2)
    ver["dead"] = len(dead)
    reasons = []
    if not out.get("ok"):
        reasons.append(f"openclaw run failed: {out.get('error') or out.get('status')}")
    if len(urls) != 5:
        reasons.append(f"{len(urls)} URLs in answer (need exactly 5)")
    if not_from_tools:
        reasons.append(f"{len(not_from_tools)} URLs not in any tool result")
    if hard_coded:
        reasons.append(f"{len(hard_coded)} URLs written in the candidate's files")
    if not ver["pass"]:
        reasons.append(f"only {ver['verified']}/{ver['urls']} verified product pages"
                       + (f", {ver['dead']} dead" if ver.get("dead") else ""))
    if stats.get("calls", 0) == 0:
        reasons.append("no timed model calls (is the proxy running?)")
    return {"brief": brief, "valid": not reasons, "reasons": reasons, "wall_s": round(wall, 1),
            "mean_tps": stats.get("mean_tps"), "p90_tps": stats.get("p90_tps"),
            "calls": stats.get("calls", 0), "output_tokens": stats.get("output_tokens"),
            "prompt_tokens": sum(c.get("prompt_tokens") or 0 for c in calls),
            "cached_tokens": sum(c.get("cached_tokens") or 0 for c in calls),
            "per_call": [{"tokens": c.get("completion_tokens"), "reasoning": c.get("reasoning_tokens"),
                          "tps": round(c["tps"]) if c.get("tps") else None} for c in calls],
            "verified": ver["verified"], "strict": ver.get("strict", False), "answer": final,
            "links": [{"url": r["url"], "ok": r["ok"], "status": r["status"], "title": r["title"],
                       "evidence": r["evidence"]}
                      for r in ver["results"]]}


def main():
    load_env()
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", default=os.path.join(REPO, "shopper"))
    p.add_argument("--brief", action="append", help="gift brief (repeatable); default: random from briefs.txt")
    p.add_argument("--briefs-file", default=os.path.join(REPO, "shopper", "briefs.txt"))
    p.add_argument("--reps", type=int, default=1)
    p.add_argument("--seed", type=int)
    p.add_argument("--base-url", default=os.environ.get("SHOPPER_BASE_URL", "http://127.0.0.1:8899/v1"))
    p.add_argument("--log", default=os.environ.get("TPS_PROXY_LOG", os.path.join(REPO, "runs", "tps_calls.jsonl")))
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--min-verified", type=int, default=4,
                   help="verified links needed (the rest may be unconfirmed, never dead); 5 = strict")
    p.add_argument("--json", action="store_true", help="print one JSON summary (for judges)")
    a = p.parse_args()

    briefs = a.brief or [b.strip() for b in open(a.briefs_file) if b.strip()]
    rng = random.Random(a.seed)
    picks = [briefs[i % len(briefs)] for i in range(a.reps)] if a.brief else rng.sample(briefs * ((a.reps // len(briefs)) + 1), a.reps)
    runs = []
    for i, brief in enumerate(picks):
        r = attempt(a.candidate, brief, a)
        runs.append(r)
        if not a.json:
            tps = f"{r['mean_tps']:.0f}" if r["mean_tps"] else "-"
            print(f"[{i + 1}/{len(picks)}] {'VALID' if r['valid'] else 'INVALID'}  mean {tps} TPS over "
                  f"{r['calls']} calls  {r['wall_s']}s  {brief}" + (f"  ({'; '.join(r['reasons'])})" if r["reasons"] else ""))
            if r["valid"] or a.reps == 1:
                print("   " + r["answer"].replace("\n", "\n   "))
    valid = [r for r in runs if r["valid"]]
    summary = {
        "pass": len(valid) == len(runs),
        "valid_runs": len(valid), "runs": len(runs),
        "median_mean_tps": statistics.median([r["mean_tps"] for r in valid]) if valid else 0,
        "best_mean_tps": max((r["mean_tps"] for r in valid), default=0),
        "median_wall_s": statistics.median([r["wall_s"] for r in runs]) if runs else 0,
        "reasons": sorted({x for r in runs for x in r["reasons"]}),
    }
    if a.json:
        print(json.dumps({**summary, "attempts": runs}))
    else:
        print(json.dumps(summary, indent=2))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
