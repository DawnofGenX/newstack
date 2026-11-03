variable "project" {
  description = "Short project slug used as the name prefix."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,30}$", var.project))
    error_message = "project must be 2-31 characters, start with a letter, and contain only lowercase letters, digits and hyphens."
  }
}

variable "environment" {
  description = "Deployment environment this set of names belongs to."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "owner" {
  description = "Team or person accountable for these resources (email or team handle)."
  type        = string

  validation {
    condition     = can(regex("^[^\\s]+$", var.owner)) && length(var.owner) > 2
    error_message = "owner must be a single non-empty token with no whitespace."
  }
}

variable "extra_tags" {
  description = "Additional tags merged over the computed defaults."
  type        = map(string)
  default     = {}
}
