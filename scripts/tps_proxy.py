#!/usr/bin/env python3
"""Pass-through proxy to the Cerebras API that logs each call's decode speed.

Point an OpenClaw provider's baseUrl at http://127.0.0.1:8899/v1 and every
chat completion is forwarded unchanged to api.cerebras.ai and streamed back.
From the stream's last chunk it records `usage.completion_tokens` and
`time_info.completion_time`, the same numbers the official speed patch uses:
per-call TPS = completion_tokens / completion_time, and the headline is the
mean of the per-call rates (p90 alongside).

    python3 scripts/tps_proxy.py                 # listen on 127.0.0.1:8899
    python3 scripts/tps_proxy.py --log calls.jsonl
    python3 scripts/tps_proxy.py --summary calls.jsonl   # mean / p90 of a log

One JSON line per call is appended to the log. The proxy never reads or logs
the Authorization header; it forwards it as is. Standard library only.
"""

import argparse
import http.client
import json
import math
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

UPSTREAM = os.environ.get("CEREBRAS_UPSTREAM", "https://api.cerebras.ai")
LOG_LOCK = threading.Lock()
HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade",
       "proxy-authorization", "proxy-authenticate", "host", "content-length",
       "accept-encoding"}


def summarize(calls):
    rates = sorted(c["tps"] for c in calls if c.get("tps"))
    if not rates:
        return {"calls": 0}
    p90 = rates[max(0, math.ceil(0.9 * len(rates)) - 1)]
    return {
        "calls": len(rates),
        "mean_tps": sum(rates) / len(rates),
        "p90_tps": p90,
        "min_tps": rates[0],
        "output_tokens": sum(c["completion_tokens"] for c in calls if c.get("tps")),
        "decode_s": sum(c["completion_time"] for c in calls if c.get("tps")),
    }


def read_log(path, start=0):
    calls = []
    if not os.path.exists(path):
        return calls
    with open(path) as f:
        f.seek(start)
        for line in f:
            line = line.strip()
            if line:
                calls.append(json.loads(line))
    return calls


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    log_path = "tps_calls.jsonl"
    dump_dir = None

    def log_message(self, fmt, *args):  # quiet
        pass

    def _forward(self, method):
        up = urlsplit(UPSTREAM)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        req_meta = {}
        if body and self.path.endswith("/chat/completions"):
            try:
                j = json.loads(body)
                req_meta = {k: j.get(k) for k in ("model", "reasoning_effort", "temperature",
                                                  "max_completion_tokens", "max_tokens", "stream")}
                req_meta["n_messages"] = len(j.get("messages") or [])
                req_meta["n_tools"] = len(j.get("tools") or [])
                req_meta["request_bytes"] = len(body)
            except ValueError:
                pass
        if req_meta and self.dump_dir:
            # Keep the request (prompt, tool results) so a judge can check that every
            # answer link came from a tool result. Headers (the API key) are never saved.
            req_meta["dump"] = os.path.join(self.dump_dir, f"{time.time():.6f}.json")
            with open(req_meta["dump"], "wb") as f:
                f.write(body)
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
        headers["Host"] = up.netloc
        conn = http.client.HTTPSConnection(up.netloc, timeout=300) if up.scheme == "https" \
            else http.client.HTTPConnection(up.netloc, timeout=300)
        t0 = time.time()
        conn.request(method, self.path, body=body, headers=headers)
        resp = conn.getresponse()
        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() not in HOP:
                self.send_header(k, v)
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Connection", "close")
        self.end_headers()

        usage = time_info = None
        buf = b""
        while True:
            chunk = resp.read1(65536) if hasattr(resp, "read1") else resp.read(65536)
            if not chunk:
                break
            self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
            self.wfile.flush()
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line.startswith(b"data:"):
                    continue
                data = line[5:].strip()
                if data == b"[DONE]":
                    continue
                try:
                    ev = json.loads(data)
                except ValueError:
                    continue
                usage = ev.get("usage") or usage
                time_info = ev.get("time_info") or time_info
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()
        if not req_meta.get("stream") and buf:
            try:
                ev = json.loads(buf)
                usage, time_info = ev.get("usage"), ev.get("time_info")
            except ValueError:
                pass
        conn.close()

        if req_meta:
            ct = (time_info or {}).get("completion_time")
            tokens = (usage or {}).get("completion_tokens")
            rec = {"t": t0, "wall_s": round(time.time() - t0, 3), "status": resp.status,
                   **req_meta, "completion_tokens": tokens, "completion_time": ct,
                   "reasoning_tokens": ((usage or {}).get("completion_tokens_details") or {}).get("reasoning_tokens"),
                   "prompt_tokens": (usage or {}).get("prompt_tokens"),
                   "cached_tokens": ((usage or {}).get("prompt_tokens_details") or {}).get("cached_tokens"),
                   "tps": (tokens / ct) if tokens and ct and tokens >= 1 and ct > 0 else None}
            with LOG_LOCK, open(self.log_path, "a") as f:
                f.write(json.dumps(rec) + "\n")

    def do_POST(self):
        self._forward("POST")

    def do_GET(self):
        self._forward("GET")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=int(os.environ.get("TPS_PROXY_PORT", 8899)))
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--log", default=os.environ.get("TPS_PROXY_LOG", "tps_calls.jsonl"))
    p.add_argument("--dump-dir", default=os.environ.get("TPS_PROXY_DUMP_DIR"),
                   help="save each chat request body here (for the judge's provenance check)")
    p.add_argument("--summary", metavar="LOG", help="print mean/p90 TPS of a log and exit")
    a = p.parse_args()
    if a.summary:
        print(json.dumps(summarize(read_log(a.summary)), indent=2))
        return 0
    Handler.log_path = os.path.abspath(a.log)
    if a.dump_dir:
        os.makedirs(a.dump_dir, exist_ok=True)
        Handler.dump_dir = os.path.abspath(a.dump_dir)
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"tps_proxy: {a.host}:{a.port} -> {UPSTREAM}, log {Handler.log_path}", file=sys.stderr)
    srv.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
