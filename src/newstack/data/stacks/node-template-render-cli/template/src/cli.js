#!/usr/bin/env node
import { parseArgs } from "node:util";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, basename, extname } from "node:path";
import { render } from "./renderer.js";

const { values, positionals } = parseArgs({
  options: {
    template: { type: "string" },
    context: { type: "string" },
    partials: { type: "string" },
  },
  allowPositionals: true,
});

let templatePath = values.template ?? positionals[0];
let contextPath = values.context ?? positionals[1];
let partialsDir = values.partials ?? positionals[2];

if (templatePath === "--help" || templatePath === "-h" || templatePath === "help") {
  process.stdout.write("Usage: template-render <template> <context.json> [partialsDir]\n");
  process.exit(0);
}

const template = readFileSync(templatePath, "utf8");
const context = JSON.parse(readFileSync(contextPath, "utf8"));

const partials = {};
if (partialsDir) {
  for (const name of readdirSync(partialsDir)) {
    const full = join(partialsDir, name);
    if (statSync(full).isFile()) {
      const key = basename(name, extname(name));
      partials[key] = readFileSync(full, "utf8");
      partials[name] = readFileSync(full, "utf8");
    }
  }
}

const result = render(template, context, partials);
process.stdout.write(result);
