local manifest = import 'manifest.jsonnet';
local schema = import 'schema.libsonnet';
local result = schema.validate(manifest);
if result.ok then 'ok\n' else std.join('\n', result.errors) + '\n'
