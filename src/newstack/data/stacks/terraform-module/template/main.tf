# Computed naming and tagging, shared by every resource the caller creates.
#
# A module like this is where conventions live: if the naming rule exists in one
# place, it cannot drift between the load balancer and the database.

locals {
  name = "${var.project}-${var.environment}"

  base_tags = {
    project     = var.project
    environment = var.environment
    owner       = var.owner
    managed-by  = "terraform"
  }

  # Caller-supplied tags win, so an exception never requires forking the module.
  tags = merge(local.base_tags, var.extra_tags)
}
