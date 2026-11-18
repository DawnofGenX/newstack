#!/usr/bin/env node
import { parseArgs } from "node:util";
import { readFileSync, writeFileSync } from "node:fs";
import { loadConfig, configFromEnv, readFileConfig } from "./config.js";

const { values } = parseArgs({
  options: {
    file: { type: "string" },
    config: { type: "string" },
    env: { type: "boolean", default: false },
    out: { type: "string" },
    port: { type: "string" },
    host: { type: "string" },
    debug: { type: "boolean", default: false },
    name: { type: "string" },
  },
});

const defaults = { port: 3000, host: "127.0.0.1", debug: false, name: "app" };
const fileConfig = (values.config ?? values.file) ? readFileConfig(values.config ?? values.file) : {};
const envConfig = values.env ? configFromEnv() : {};
const cliConfig = {};
if (values.port !== undefined) cliConfig.port = Number(values.port);
if (values.host !== undefined) cliConfig.host = values.host;
if (values.debug) cliConfig.debug = true;
if (values.name !== undefined) cliConfig.name = values.name;

const resolved = loadConfig({ defaults, fileConfig, envConfig, cliConfig });
const json = JSON.stringify(resolved, null, 2);
if (values.out) writeFileSync(values.out, json + "\n");
else process.stdout.write(json + "\n");