local h = import 'harness.libsonnet';
local schemaTests = import 'schema_test.jsonnet';
local renderTests = import 'render_test.jsonnet';

local results = schemaTests + renderTests;

h.report(results)
