// The manifest this project compiles: three services, one shared environment.
{
  services: [
    {
      name: 'gateway',
      image: 'ghcr.io/example/gateway:1.4.0',
      port: 8080,
      replicas: 2,
      env: { LOG_LEVEL: 'info' },
    },
    {
      name: 'worker',
      image: 'ghcr.io/example/worker:1.4.0',
      port: 9090,
      replicas: 3,
      env: { LOG_LEVEL: 'warn' },
    },
    {
      name: 'scheduler',
      image: 'ghcr.io/example/scheduler:1.4.0',
      port: 7070,
      replicas: 1,
    },
  ],
}
