"""Minimal client for Parallel's free search MCP (https://search.parallel.ai/mcp).

Used by verify_gifts.py as a second fetcher for retail pages that block plain
HTTP clients (403/429). Standard library only.
"""

import json
import urllib.request

URL = "https://search.parallel.ai/mcp"


class ParallelMCP:
    def __init__(self, url=URL, timeout=60):
        self.url, self.timeout, self.sid, self.n = url, timeout, None, 0
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "speedy-shopper-verify", "version": "1"}})
        self._rpc("notifications/initialized", notify=True)

    def _rpc(self, method, params=None, notify=False):
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            self.n += 1
            body["id"] = self.n
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
             "MCP-Protocol-Version": "2025-06-18"}
        if self.sid:
            h["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(self.url, json.dumps(body).encode(), h)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            self.sid = r.headers.get("Mcp-Session-Id") or self.sid
            raw = r.read().decode()
        if notify or not raw.strip():
            return None
        if "data:" in raw[:30]:
            raw = "\n".join(l[5:] for l in raw.splitlines() if l.startswith("data:"))
        msg = json.loads(raw)
        if "error" in msg:
            raise RuntimeError(msg["error"])
        return msg["result"]

    def call(self, tool, args):
        res = self._rpc("tools/call", {"name": tool, "arguments": args})
        text = "".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        try:
            return json.loads(text)
        except ValueError:
            return {"text": text}

    def fetch(self, urls, objective="Product name, price and whether it can be bought"):
        return self.call("web_fetch", {"urls": list(urls), "objective": objective})
