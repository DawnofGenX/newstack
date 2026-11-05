local render = (import 'render.libsonnet').render;
local h = import 'harness.libsonnet';

local manifest = {
  services: [
    { name: 'worker', image: 'w:1', port: 9090, replicas: 3 },
    { name: 'gateway', image: 'g:1', port: 8080, replicas: 2, env: { LOG_LEVEL: 'info' } },
  ],
};

local document = render(manifest);

[
  h.equal('services are sorted by name', document.serviceNames, ['gateway', 'worker']),
  h.equal('total replicas are summed', document.totalReplicas, 5),
  h.equal('a service without env renders an empty env', document.services[1].env, {}),
  h.equal('env is carried through', document.services[0].env.LOG_LEVEL, 'info'),
  h.equal('ports are carried through', document.services[0].port, 8080),
  h.equal('every service is rendered', std.length(document.services), 2),
]
