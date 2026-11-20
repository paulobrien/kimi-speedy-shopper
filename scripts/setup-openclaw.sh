#!/usr/bin/env bash
# Install this repo's OpenClaw config and secrets file, then (re)start the gateway.
#
#   scripts/setup-openclaw.sh [path-to-thermite-operator-token]
#
# - Writes ~/.openclaw/openclaw.json from config/openclaw.example.json5 (backs up any existing file).
# - Creates ~/.openclaw/.env (mode 600) with CEREBRAS_API_KEY (empty: fill it in),
#   THERMITE_MCP_TOKEN (copied from the token file, if given) and a random OPENCLAW_GATEWAY_TOKEN.
#   Existing values are kept.
# - Installs the gateway as a systemd user service if needed and restarts it.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
TOKEN_FILE="${1:-}"

source ~/.nvm/nvm.sh >/dev/null
nvm use 24 >/dev/null
command -v openclaw >/dev/null || { echo "openclaw not installed: npm install -g openclaw@latest --allow-scripts=openclaw" >&2; exit 1; }

mkdir -p ~/.openclaw
CFG=~/.openclaw/openclaw.json
if [[ -f $CFG ]]; then cp "$CFG" "$CFG.bak.$(date +%Y%m%d%H%M%S)"; fi
sed "s|__REPO__|$REPO|g" "$REPO/config/openclaw.example.json5" > "$CFG"

ENV=~/.openclaw/.env
( umask 077; touch "$ENV" )
chmod 600 "$ENV"
grep -q '^CEREBRAS_API_KEY=' "$ENV" || echo "CEREBRAS_API_KEY=" >> "$ENV"
grep -q '^OPENCLAW_GATEWAY_TOKEN=' "$ENV" || echo "OPENCLAW_GATEWAY_TOKEN=$(openssl rand -hex 24)" >> "$ENV"
if ! grep -q '^THERMITE_MCP_TOKEN=' "$ENV"; then
  if [[ -n $TOKEN_FILE ]]; then echo "THERMITE_MCP_TOKEN=$(cat "$TOKEN_FILE")" >> "$ENV"
  else echo "THERMITE_MCP_TOKEN=" >> "$ENV"; echo "note: THERMITE_MCP_TOKEN is empty; pass Thermite's .dev/secrets/control-operator-token" >&2; fi
fi

openclaw config validate
if ! systemctl --user cat openclaw-gateway.service >/dev/null 2>&1; then openclaw gateway install; fi
systemctl --user restart openclaw-gateway.service
sleep 8
openclaw gateway status 2>&1 | grep -E 'Runtime|Connectivity|Listening' || true
grep -q '^CEREBRAS_API_KEY=.\+' "$ENV" || echo "next: put your key in $ENV (CEREBRAS_API_KEY=...) and rerun this script" >&2
