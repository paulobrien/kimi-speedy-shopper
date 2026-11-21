#!/usr/bin/env node
// Check: read the bench service's verdict for this run. The service, not the candidate, wrote
// result.json (the candidate only supplies a prompt and settings), so its numbers are the
// measurement: validity (5 live product links from this run's own search results, none
// hard-coded) and mean server-side TPS.
// usage: check.mjs <params.json> <out-dir>
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const [, out] = process.argv.slice(2);
const path = join(out, "result.json");
if (!existsSync(path)) {
  console.log(JSON.stringify({ pass: false, reasons: ["no result.json from the bench service"] }));
  process.exit(0);
}
const r = JSON.parse(readFileSync(path, "utf8"));
const reasons = (r.reasons ?? []).map((x) => String(x).slice(0, 160)).slice(0, 4);
const ok = r.pass === true && r.mean_tps > 0;
console.log(
  JSON.stringify({
    pass: ok,
    reasons: ok ? [] : reasons.length ? reasons : ["no valid attempt"],
    mean_tps: ok ? r.mean_tps : 0,
    valid_rate: r.valid_rate ?? 0,
    calls: r.calls > 0 ? r.calls : 1,
  }),
);
