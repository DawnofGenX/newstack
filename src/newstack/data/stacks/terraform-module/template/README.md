# {{ title }}

A reusable Terraform module: validated inputs, computed naming and tags, and tests
that run with `terraform test` — no cloud account required.

## Inputs

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `project` | `string` | yes | Short project slug, 2-31 chars, lowercase letters/digits/hyphens |
| `environment` | `string` | yes | One of `dev`, `staging`, `prod` |
| `owner` | `string` | yes | Accountable team or person, no whitespace |
| `extra_tags` | `map(string)` | no | Tags merged over the computed defaults |

## Outputs

| Name | Description |
| --- | --- |
| `name` | `<project>-<environment>`, the resource name prefix |
| `tags` | Full tag map, caller overrides applied |
| `is_production` | `true` when `environment == "prod"` |

## Use it

```hcl
module "naming" {
  source = "./modules/naming"

  project     = "demo-app"
  environment = "prod"
  owner       = "platform@example.com"
  extra_tags  = { "cost-center" = "42" }
}
```

## Checks

```console
$ terraform fmt -check -recursive
$ terraform init -backend=false
$ terraform validate
$ terraform test
```

`terraform test` runs every case in `main.tftest.hcl`, including the one that asserts
an invalid environment is rejected — the validation rule is covered, not just declared.
