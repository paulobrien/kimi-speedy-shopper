#!/usr/bin/env bash
# End-to-end check: an OpenClaw agent on Kimi K3.1 Pro (Cerebras) calls Thermite over MCP.
# Needs CEREBRAS_API_KEY set in ~/.openclaw/.env and the gateway restarted after setting it.
# Usage: scripts/openclaw_smoke.sh [model]   (default: the mission agent's model, Kimi K3.1 Pro)
#   e.g. scripts/openclaw_smoke.sh cerebras/gpt-oss-120b   before Kimi preview access is live
set -euo pipefail
MODEL_ARGS=()
[[ $# -ge 1 ]] && MODEL_ARGS=(--model "$1")
source ~/.nvm/nvm.sh >/dev/null
nvm use 24 >/dev/null

echo "== gateway"; openclaw gateway status 2>&1 | grep -E 'Runtime|Connectivity|Listening' || true
# (`openclaw mcp probe` only runs with the gateway stopped, so it isn't checked here.)
echo "== model + tool call"
time openclaw agent --agent mission --json --timeout 180 "${MODEL_ARGS[@]}" \
  --message "Use the thermite list_rigs tool and tell me, in one sentence, which rigs exist and whether each is live."
