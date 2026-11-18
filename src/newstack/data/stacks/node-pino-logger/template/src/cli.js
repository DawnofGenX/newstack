#!/usr/bin/env node
import { parseArgs } from "node:util";
import { createLogger } from "./logger.js";

const { values } = parseArgs({
  options: {
    level: { type: "string", default: "info" },
    msg: { type: "string", default: "hello" },
    password: { type: "string" },
  },
});

const logger = createLogger({ level: values.level, service: "demo" });
const payload = { event: "greeting" };
if (values.password) payload.password = values.password;
logger.info(payload, values.msg);
