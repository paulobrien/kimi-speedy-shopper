#!/usr/bin/env python3
"""Call one Thermite control MCP tool from the shell (streamable HTTP, operator token).

    python3 scripts/thermite_mcp.py list                      # tool names
    python3 scripts/thermite_mcp.py schema kit_add            # one tool's input schema
    python3 scripts/thermite_mcp.py call list_rigs '{}'
    python3 scripts/thermite_mcp.py call issue_command @payload.json

The token comes from THERMITE_MCP_TOKEN (env or ~/.openclaw/.env). Standard library only.
"""

import json
import os
import sys
import urllib.request

URL = os.environ.get("THERMITE_MCP_URL", "http://127.0.0.1:8800/mcp")


def env_token():
    tok = os.environ.get("THERMITE_MCP_TOKEN")
    if not tok and os.path.exists(os.path.expanduser("~/.openclaw/.env")):
        for line in open(os.path.expanduser("~/.openclaw/.env")):
            if line.startswith("THERMITE_MCP_TOKEN="):
                tok = line.split("=", 1)[1].strip()
    if not tok:
        sys.exit("THERMITE_MCP_TOKEN not set")
    return tok


class Client:
    def __init__(self):
        self.tok, self.sid, self.n = env_token(), None, 0
        self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                "clientInfo": {"name": "speedy-shopper", "version": "1"}})
        self.rpc("notifications/initialized", notify=True)

    def rpc(self, method, params=None, notify=False):
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            self.n += 1
            body["id"] = self.n
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
             "Authorization": f"Bearer {self.tok}", "MCP-Protocol-Version": "2025-06-18"}
        if self.sid:
            h["Mcp-Session-Id"] = self.sid
        with urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), h), timeout=300) as r:
            self.sid = r.headers.get("Mcp-Session-Id") or self.sid
            raw = r.read().decode()
        if notify or not raw.strip():
            return None
        if "data:" in raw[:30]:
            raw = "\n".join(l[5:] for l in raw.splitlines() if l.startswith("data:"))
        msg = json.loads(raw)
        if "error" in msg:
            raise SystemExit(f"error: {msg['error']}")
        return msg["result"]


def main():
    c = Client()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd in ("list", "schema"):
        tools = c.rpc("tools/list", {})["tools"]
        for t in tools:
            if cmd == "list":
                print(t["name"])
            elif t["name"] == sys.argv[2]:
                print(t.get("description", ""))
                print(json.dumps(t["inputSchema"], indent=1))
        return
    name, arg = sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "{}"
    args = json.load(open(arg[1:])) if arg.startswith("@") else json.loads(arg)
    res = c.rpc("tools/call", {"name": name, "arguments": args})
    for part in res.get("content", []):
        if part.get("type") == "text":
            print(part["text"])
    if res.get("isError"):
        sys.exit(1)


if __name__ == "__main__":
    main()
