# Native Terraform tests. No provider and no cloud credentials are involved:
# these run against the module's own inputs and outputs.

run "defaults_are_derived" {
  command = plan

  variables {
    project     = "demo-app"
    environment = "dev"
    owner       = "platform@example.com"
  }

  assert {
    condition     = output.name == "demo-app-dev"
    error_message = "name must combine project and environment."
  }

  assert {
    condition     = output.tags["managed-by"] == "terraform"
    error_message = "managed-by must always be terraform."
  }

  assert {
    condition     = output.is_production == false
    error_message = "dev must not report as production."
  }
}

run "caller_tags_override_defaults" {
  command = plan

  variables {
    project     = "demo-app"
    environment = "prod"
    owner       = "platform@example.com"
    extra_tags  = { "cost-center" = "42", "owner" = "finance@example.com" }
  }

  assert {
    condition     = output.tags["cost-center"] == "42"
    error_message = "extra_tags must be merged into the output."
  }

  assert {
    condition     = output.tags["owner"] == "finance@example.com"
    error_message = "extra_tags must win over computed defaults."
  }

  assert {
    condition     = output.is_production == true
    error_message = "prod must report as production."
  }
}

run "invalid_environment_is_rejected" {
  command = plan

  variables {
    project     = "demo-app"
    environment = "qa"
    owner       = "platform@example.com"
  }

  expect_failures = [var.environment]
}
