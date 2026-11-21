#!/usr/bin/env node
// Run step: send the candidate's shopper files to the bench service on the host, which runs
// the shopper on standard OpenClaw with Kimi K3.1 Pro on Cerebras and scores it like the
// official speed patch (mean over calls of completion_tokens / completion_time, server-side).
// Uses node:http, not fetch: a bench call can take many minutes when Cerebras is queueing, and
// fetch gives up waiting for headers after 300 s.
// usage: submit.mjs <shopper-dir> <params.json> <out-dir>
import { readFileSync, writeFileSync } from "node:fs";
import { request } from "node:http";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const [dir, paramsPath, out] = process.argv.slice(2);
const p = JSON.parse(readFileSync(paramsPath, "utf8"));
const here = dirname(fileURLToPath(import.meta.url));
const token = readFileSync(join(here, "bench-token"), "utf8").trim();
const url = new URL(process.env.SHOPPER_BENCH_URL ?? "http://host.docker.internal:8898/bench");
const body = JSON.stringify({
  token,
  set: p.set,
  reps: p.reps,
  files: {
    "AGENTS.md": readFileSync(join(dir, "AGENTS.md"), "utf8"),
    "settings.json": readFileSync(join(dir, "settings.json"), "utf8"),
  },
});

const text = await new Promise((resolve, reject) => {
  const req = request(
    url,
    { method: "POST", headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) } },
    (res) => {
      let data = "";
      res.setEncoding("utf8");
      res.on("data", (c) => (data += c));
      res.on("end", () =>
        res.statusCode === 200 ? resolve(data) : reject(new Error(`bench service ${res.statusCode}: ${data.slice(0, 400)}`)),
      );
    },
  );
  req.setTimeout(1_450_000, () => req.destroy(new Error("bench service timed out")));
  req.on("error", reject);
  req.end(body);
});
writeFileSync(join(out, "result.json"), text);
const r = JSON.parse(text);
console.log(`pass=${r.pass} mean_tps=${Math.round(r.mean_tps)} valid_rate=${r.valid_rate}`);
