output "name" {
  description = "Name prefix for resources in this environment."
  value       = local.name
}

output "tags" {
  description = "Tags to apply to every resource, including caller overrides."
  value       = local.tags
}

output "is_production" {
  description = "True when this module instance targets production."
  value       = var.environment == "prod"
}
