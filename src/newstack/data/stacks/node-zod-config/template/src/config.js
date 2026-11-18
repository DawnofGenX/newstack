import { readFileSync } from "node:fs";
import { z } from "zod";

export const ConfigSchema = z.object({
  port: z.number().int().min(1).max(65535).default(3000),
  host: z.string().min(1).default("127.0.0.1"),
  debug: z.boolean().default(false),
  name: z.string().min(1).default("app"),
});

export const DEFAULTS = ConfigSchema.parse({});

export function parseConfig(raw) {
  return ConfigSchema.parse(raw ?? {});
}

export function mergeConfigs(...layers) {
  const merged = {};
  for (const layer of layers) {
    if (!layer) continue;
    for (const [k, v] of Object.entries(layer)) {
      if (v !== undefined && v !== null) merged[k] = v;
    }
  }
  return ConfigSchema.parse(merged);
}

export function loadConfig({ defaults = {}, fileConfig = {}, envConfig = {}, cliConfig = {} } = {}) {
  return mergeConfigs(defaults, fileConfig, envConfig, cliConfig);
}

export function configFromEnv(env = process.env, prefix = "APP_") {
  const out = {};
  const port = env[`${prefix}PORT`];
  if (port !== undefined) out.port = Number(port);
  const host = env[`${prefix}HOST`];
  if (host !== undefined) out.host = host;
  const debug = env[`${prefix}DEBUG`];
  if (debug !== undefined) out.debug = debug === "1" || debug === "true";
  const name = env[`${prefix}NAME`];
  if (name !== undefined) out.name = name;
  return out;
}

export function readFileConfig(filePath) {
  const raw = readFileSync(filePath, "utf8");
  return JSON.parse(raw);
}