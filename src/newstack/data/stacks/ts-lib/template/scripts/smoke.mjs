// Proves the two published entry points resolve and agree with the source.
// Run after `npm run build`: CI does, and so does `newstack check`.
import assert from "node:assert/strict";
import { createRequire } from "node:module";

import { countText, formatCounts } from "../dist/index.js";

const require = createRequire(import.meta.url);
const cjs = require("../dist/index.cjs");

const esm = countText("one two\nthree\n");
assert.deepEqual(esm, { lines: 2, words: 3, bytes: 14 }, "the ESM entry is wrong");
assert.equal(formatCounts(esm), "       2       3      14", "the ESM formatter is wrong");

const fromCjs = cjs.countText("one two\nthree\n");
assert.deepEqual(fromCjs, esm, "the CJS entry disagrees with the ESM entry");

console.log("dist/index.js and dist/index.cjs both work");
