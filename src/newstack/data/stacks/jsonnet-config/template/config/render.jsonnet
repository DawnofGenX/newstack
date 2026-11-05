local manifest = import 'manifest.jsonnet';
local render = (import 'render.libsonnet').render;
render(manifest)
