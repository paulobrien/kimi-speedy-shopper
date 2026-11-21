#!/usr/bin/env python3
"""Print one line per notable event of a Thermite run (baseline, verdicts, champions, failures).

    python3 scripts/watch_run.py speedy-shopper-1 [--interval 60] [--once]
"""
import json, subprocess, sys, time, os
HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = ("baseline", "verdict", "champion", "promot", "failed", "crash", "invalid", "paused", "error", "stopped")


def get_run(run):
    out = subprocess.run([sys.executable, os.path.join(HERE, "thermite_mcp.py"), "call", "get_run",
                          json.dumps({"run": run})], capture_output=True, text=True, timeout=120).stdout
    return json.loads(out)


def main():
    run = sys.argv[1]
    interval = int(sys.argv[sys.argv.index("--interval") + 1]) if "--interval" in sys.argv else 60
    seen = set()
    first = True
    while True:
        try:
            d = get_run(run)
            for t in d.get("timeline", []):
                if t["id"] in seen:
                    continue
                seen.add(t["id"])
                if first and "--once" not in sys.argv:
                    continue
                if any(k in t["kind"] for k in KINDS):
                    print(f'{t["at"][11:19]} {t["kind"]} {json.dumps(t.get("body"))[:300]}', flush=True)
            first = False
        except Exception as e:  # noqa: BLE001
            print(f"watch error: {e}", flush=True)
        if "--once" in sys.argv:
            return
        time.sleep(interval)


if __name__ == "__main__":
    main()
