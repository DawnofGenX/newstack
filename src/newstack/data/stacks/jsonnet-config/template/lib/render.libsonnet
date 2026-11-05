// Turns a validated manifest into the document the deploy step consumes.
{
  render(manifest)::
    local services = std.sort(manifest.services, function(s) s.name);
    {
      services: [
        {
          name: s.name,
          image: s.image,
          port: s.port,
          replicas: s.replicas,
          env: if std.objectHas(s, 'env') then s.env else {},
        }
        for s in services
      ],
      totalReplicas: std.foldl(function(acc, s) acc + s.replicas, services, 0),
      serviceNames: [s.name for s in services],
    },
}
