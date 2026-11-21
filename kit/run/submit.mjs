#!/usr/bin/env node
// Run step: send the candidate's shopper files to the bench service on the host, which runs
// the shopper on standard OpenClaw with Kimi K3.1 Pro on Cerebras and scores it like the
// official speed patch (mean over calls of completion_tokens / completion_time, server-side).
// usage: submit.mjs <shopper-dir> <params.json> <out-dir>
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const [dir, paramsPath, out] = process.argv.slice(2);
const p = JSON.parse(readFileSync(paramsPath, "utf8"));
const here = dirname(fileURLToPath(import.meta.url));
const token = readFileSync(join(here, "bench-token"), "utf8").trim();
const url = process.env.SHOPPER_BENCH_URL ?? "http://host.docker.internal:8898/bench";
const files = {
  "AGENTS.md": readFileSync(join(dir, "AGENTS.md"), "utf8"),
  "settings.json": readFileSync(join(dir, "settings.json"), "utf8"),
};
const res = await fetch(url, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ token, files, set: p.set, reps: p.reps }),
  signal: AbortSignal.timeout(1400_000),
});
const body = await res.text();
if (!res.ok) {
  console.error(`bench service ${res.status}: ${body.slice(0, 500)}`);
  process.exit(1);
}
writeFileSync(join(out, "result.json"), body);
const r = JSON.parse(body);
console.log(`pass=${r.pass} mean_tps=${Math.round(r.mean_tps)} valid_rate=${r.valid_rate}`);
