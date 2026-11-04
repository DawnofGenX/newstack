# {{ title }}

{{ description }}

A production-shaped Helm chart for one stateless HTTP service: a Deployment, a
Service, an optional ServiceAccount, shared name/label helpers, and a
`values.schema.json` that makes a typo'd override a build failure instead of a
silently broken rollout.

## Layout

```
Chart.yaml                     chart metadata (apiVersion v2)
values.yaml                    every knob, with the defaults documented inline
values.schema.json             JSON Schema for values.yaml — enforced by helm
.helmignore                    what `helm package` leaves out
templates/_helpers.tpl         name/fullname/chart/labels/selectorLabels helpers
templates/deployment.yaml      the workload: hardened securityContext, probes, resources
templates/service.yaml         ClusterIP service on .Values.service.port -> containerPort 8080
templates/serviceaccount.yaml  created when serviceAccount.create is true
templates/tests/test-connection.yaml  `helm test` hook: a pod that curls the Service
templates/NOTES.txt            post-install instructions, rendered per release
.github/workflows/ci.yml       lint + render + schema check, no cluster required
```

## Render and inspect (no cluster needed)

```sh
helm lint .
helm template my-release . --namespace default
```

`helm lint` validates the chart and the values against the schema;
`helm template` renders the manifests locally. Nothing here talks to a cluster,
which is why CI can prove the chart is sound without one.

## Install

```sh
helm upgrade --install my-release . --namespace default --create-namespace
```

## Values

| Key | Default | Meaning |
| --- | --- | --- |
| `replicaCount` | `2` | Pods in the Deployment (schema: 1-20) |
| `image.repository` | `ghcr.io/example/{{ npm_name }}` | Image to run |
| `image.tag` | `""` | Falls back to `.Chart.AppVersion` when empty |
| `image.pullPolicy` | `IfNotPresent` | Kubernetes pull policy |
| `serviceAccount.create` | `true` | Create a dedicated ServiceAccount |
| `serviceAccount.name` | `""` | Override the derived ServiceAccount name |
| `service.type` | `ClusterIP` | `ClusterIP`, `NodePort` or `LoadBalancer` |
| `service.port` | `80` | Service port, forwarded to the container's `http` port (8080) |
| `resources` | 50m/64Mi requests, 200m/128Mi limits | Container resources |
| `env` | `APP_ENV=production` | Extra environment variables |
| `podSecurityContext` | non-root uid 10001 | Pod-level security context |
| `securityContext` | read-only rootfs, no privilege escalation, all caps dropped | Container-level security context |
| `nameOverride` / `fullnameOverride` | `""` | Replace the derived names |

## Why the schema

`values.schema.json` is not documentation — helm evaluates it on `lint`, `template`
and `install`. `helm template my-release . --set replicaCount=0` fails, because the
schema says `replicaCount` is an integer of at least 1. That is the cheapest place
to catch a bad `--set` from a CI job, and it is why the chart ships one.

## Requirements

Helm 3.8 or newer (developed and tested with Helm 4.3.1). A Kubernetes cluster is
only needed to install, not to lint or render.
