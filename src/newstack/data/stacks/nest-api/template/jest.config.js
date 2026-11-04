/**
 * ts-jest cannot resolve the `.js` suffix that NodeNext imports require, so the
 * mapper strips it back to the TypeScript source. That mapper is the only reason
 * this file exists: everything else is Jest's default for an ESM TypeScript tree.
 *
 * @type {import('jest').Config}
 */
export default {
  moduleFileExtensions: ["js", "json", "ts"],
  rootDir: ".",
  testRegex: ".*\\.(spec|e2e-spec)\\.ts$",
  extensionsToTreatAsEsm: [".ts"],
  moduleNameMapper: {
    "^(\\.{1,2}/.*)\\.js$": "$1",
  },
  transform: {
    "^.+\\.ts$": [
      "ts-jest",
      {
        useESM: true,
        diagnostics: { ignoreCodes: [151002] },
      },
    ],
  },
  testEnvironment: "node",
};
