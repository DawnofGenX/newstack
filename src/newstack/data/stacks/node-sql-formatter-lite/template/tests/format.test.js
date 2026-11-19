import { test } from "node:test";
import assert from "node:assert/strict";
import { formatSql } from "../src/format.js";

test("basic", () => {
  assert.equal(formatSql("select id, name from users where active=1"), "SELECT id, name FROM users WHERE active=1;");
});

test("lowercase keywords", () => {
  assert.equal(formatSql("select * from t"), "SELECT * FROM t;");
});

test("already semicolon", () => {
  assert.equal(formatSql("select 1;"), "SELECT 1;");
});