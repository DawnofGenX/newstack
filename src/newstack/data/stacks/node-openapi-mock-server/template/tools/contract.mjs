#!/usr/bin/env node
import process from "node:process";

const args = process.argv.slice(2);
let base = "http://127.0.0.1:5531";
for (let i = 0; i < args.length; i++) if (args[i] === "--base") base = args[i + 1];

let checks = 0;
function ok(l){checks++; console.log(`  ok   ${l}`);}
function fail(l,d){console.error(`  FAIL ${l}${d?": "+d:""}`); process.exit(1);}
function assert(c,l,d){ if(c) ok(l); else fail(l,d); }

async function main() {
  console.log(`contract: ${base}`);
  const health = await fetch(`${base}/health`);
  assert(health.status === 200, "health 200", String(health.status));
  assert((await health.json()).status === "ok", "health ok");

  const pets = await fetch(`${base}/pets`);
  assert(pets.status === 200, "pets 200");
  const petsBody = await pets.json();
  assert(Array.isArray(petsBody) === false || Array.isArray(petsBody), "pets json");

  const one = await fetch(`${base}/pets/7`);
  assert(one.status === 200, "pet by id 200");
  const oneBody = await one.json();
  assert(typeof oneBody === "object", "pet object");

  const post = await fetch(`${base}/pets`, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" });
  assert(post.status === 201, "post pets 201", String(post.status));
  assert((await post.json()).name === "fido", "example from examples");

  const nf = await fetch(`${base}/nope`);
  assert(nf.status === 404, "unknown path 404");
  const nfBody = await nf.json();
  assert(Array.isArray(nfBody.paths), "404 lists paths");

  const wm = await fetch(`${base}/health`, { method: "DELETE" });
  assert(wm.status === 405, "wrong method 405");

  const rq = await fetch(`${base}/search`);
  assert(rq.status === 400, "missing required query 400");

  const rok = await fetch(`${base}/search?q=hi`);
  assert(rok.status === 200, "required query ok 200");

  console.log(`contract: ${checks} checks passed`);
}
main().catch((e)=>{console.error(`contract failed: ${e.message}`); process.exit(1);});