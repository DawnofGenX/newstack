#!/usr/bin/env node
import { parseArgs } from "node:util";
import { applyMigrations, migrationStatus } from "./migrations.js";

const { values } = parseArgs({
  options: {
    db: { type: "string", default: "app.db" },
    dir: { type: "string", default: "migrations" },
    status: { type: "boolean", default: false },
  },
});

if (values.status) {
  console.log(JSON.stringify(migrationStatus({ dbPath: values.db, dir: values.dir }), null, 2));
} else {
  const results = applyMigrations({ dbPath: values.db, dir: values.dir });
  console.log(JSON.stringify(results, null, 2));
}
