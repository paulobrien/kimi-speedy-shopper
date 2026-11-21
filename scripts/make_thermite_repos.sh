#!/usr/bin/env bash
# Build the Thermite project (seed) and kit repositories from thermite/seed and kit/, bundle
# them, and render the contract with the kit's commit. Output in runs/thermite/:
#   speedy-shopper.bundle, speedy-shopper-kit.bundle, assign.json (payload for assign_campaign)
#
#   scripts/make_thermite_repos.sh [run-name] [inbox-dir]
#
# The seed bundle is copied to <inbox-dir>/repos/ (the rig's inbox); the kit bundle is meant
# for control (MCP kit_add). The kit includes run/bench-token from kit/.bench-token.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
RUN="${1:-speedy-shopper-1}"
INBOX="${2:-}"
OUT="$REPO/runs/thermite"
rm -rf "$OUT" && mkdir -p "$OUT"
export GIT_AUTHOR_NAME=thermite-prep GIT_AUTHOR_EMAIL=noreply@example.com
export GIT_COMMITTER_NAME=thermite-prep GIT_COMMITTER_EMAIL=noreply@example.com
export GIT_AUTHOR_DATE="2026-11-21T19:00:00Z" GIT_COMMITTER_DATE="2026-11-21T19:00:00Z"

mk() { # dir bundle
  git -C "$1" init -q -b main && git -C "$1" add -A && git -C "$1" commit -qm "$3"
  git -C "$1" bundle create -q "$2" main
  git -C "$1" rev-parse HEAD
}

mkdir -p "$OUT/seed" && cp -r "$REPO/thermite/seed/." "$OUT/seed/"
SEED=$(mk "$OUT/seed" "$OUT/speedy-shopper.bundle" "Speedy Shopper starting configuration")

mkdir -p "$OUT/kit" && cp -r "$REPO/kit/." "$OUT/kit/" && rm -f "$OUT/kit/.bench-token"
cp "$REPO/kit/.bench-token" "$OUT/kit/run/bench-token"
KIT=$(mk "$OUT/kit" "$OUT/speedy-shopper-kit.bundle" "Speedy Shopper kit")

sed "s/__KIT_COMMIT__/$KIT/" "$REPO/thermite/contract.json" > "$OUT/contract.json"
source ~/.nvm/nvm.sh >/dev/null && nvm use 24 >/dev/null
node "$REPO/scripts/thermite_prepare.mjs" "$OUT/kit/kit.json" "$OUT/contract.json" > "$OUT/parsed.json"

python3 - "$OUT" "$RUN" "$SEED" "$KIT" <<'PY'
import hashlib, json, sys
out, run, seed, kit = sys.argv[1:]
p = json.load(open(f"{out}/parsed.json"))
sha = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
payload = {
    "run": run, "contract": p["contract"], "contract_sha": p["contract_sha"],
    "seed": {"repo": "speedy-shopper", "commit": seed},
    "imports": [
        {"kind": "repo_bundle", "path": "repos/speedy-shopper.bundle", "repo": "speedy-shopper",
         "commit": seed, "sha256": sha(f"{out}/speedy-shopper.bundle")},
        {"kind": "kit_bundle", "path": "repos/speedy-shopper-kit.bundle", "repo": "speedy-shopper-kit",
         "commit": kit, "source": {"control": "kits/speedy-shopper-kit"}},
    ],
    "promotion": "auto",
    "note": "Hackathon: Kimi K3.1 Pro on Cerebras, Santa's Speedy Shopper TPS hill climb",
}
json.dump(payload, open(f"{out}/assign.json", "w"), indent=1)
print(json.dumps({"seed": seed, "kit": kit, "contract_sha": p["contract_sha"]}))
PY
if [[ -n $INBOX ]]; then mkdir -p "$INBOX/repos" && cp "$OUT/speedy-shopper.bundle" "$INBOX/repos/"; echo "seed bundle -> $INBOX/repos/"; fi
