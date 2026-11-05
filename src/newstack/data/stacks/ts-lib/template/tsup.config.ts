import { defineConfig } from "tsup";

// One entry, two formats. `exports` in package.json points at the files this
// emits, and `dts` writes dist/index.d.ts next to them, so `import` and
// `require` both get types. publint is the gate that keeps those three honest.
export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm", "cjs"],
  dts: true,
  sourcemap: true,
  clean: true,
  target: "es2022",
  outExtension({ format }) {
    return { js: format === "cjs" ? ".cjs" : ".js" };
  },
});
