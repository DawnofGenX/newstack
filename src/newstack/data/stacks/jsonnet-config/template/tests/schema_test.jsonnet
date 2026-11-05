local schema = import 'schema.libsonnet';
local h = import 'harness.libsonnet';

local service(overrides={}) = {
  name: 'gateway',
  image: 'ghcr.io/example/gateway:1.0.0',
  port: 8080,
  replicas: 2,
} + overrides;

local valid = { services: [service(), service({ name: 'worker', port: 9090 })] };

local errorsOf(manifest) = schema.validate(manifest).errors;

local hasError(manifest, fragment) =
  std.length([e for e in errorsOf(manifest) if std.length(std.findSubstr(fragment, e)) > 0]) > 0;

[
  h.check('a well formed manifest passes', schema.validate(valid).ok),
  h.check('a name must be lower case',
          hasError({ services: [service({ name: 'Gateway' })] }, 'lower-case')),
  h.check('a name cannot start with a dash',
          hasError({ services: [service({ name: '-gateway' })] }, 'lower-case')),
  h.check('an empty image is rejected',
          hasError({ services: [service({ image: '' })] }, 'image')),
  h.check('port 0 is rejected', hasError({ services: [service({ port: 0 })] }, 'port')),
  h.check('port 70000 is rejected', hasError({ services: [service({ port: 70000 })] }, 'port')),
  h.check('zero replicas are rejected', hasError({ services: [service({ replicas: 0 })] }, 'replicas')),
  h.check('twenty one replicas are rejected', hasError({ services: [service({ replicas: 21 })] }, 'replicas')),
  h.check('a non-string env value is rejected',
          hasError({ services: [service({ env: { LOG_LEVEL: 3 } })] }, 'env.LOG_LEVEL')),
  h.check('duplicate names are rejected',
          hasError({ services: [service(), service()] }, 'duplicate')),
  h.check('an empty manifest is rejected', !schema.validate({ services: [] }).ok),
  h.equal('a passing manifest reports no errors', std.length(errorsOf(valid)), 0),
]
