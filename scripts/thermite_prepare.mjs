#!/usr/bin/env node
// Validate the kit and contract with Thermite's own schema code, and print the contract
// (defaults applied) with its hash, as `thermite contract validate` would.
// usage: node scripts/thermite_prepare.mjs <kit.json> <contract.json> > parsed.json
// Needs THERMITE_SRC (default ~/source/repos/thermite) with node_modules installed; Node 24
// runs Thermite's TypeScript directly.
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const src = process.env.THERMITE_SRC ?? join(homedir(), "source/repos/thermite");
const load = (p) => import(pathToFileURL(join(src, "src/core", p)).href);
const { parseContract, contractSha } = await load("contract.ts");
const { KitSchema, kitProblems } = await load("kit.ts");

const [kitPath, contractPath] = process.argv.slice(2);
const kit = KitSchema.safeParse(JSON.parse(readFileSync(kitPath, "utf8")));
if (!kit.success) {
  console.error("kit.json invalid:", kit.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`));
  process.exit(1);
}
const c = parseContract(JSON.parse(readFileSync(contractPath, "utf8")));
if (!c.ok) {
  console.error("contract invalid:", c.errors);
  process.exit(1);
}
const problems = kitProblems(c.contract, kit.data, "cpu");
if (problems.length) {
  console.error("kit does not fit contract:", problems);
  process.exit(1);
}
console.log(JSON.stringify({ contract: c.contract, contract_sha: contractSha(c.contract) }));
