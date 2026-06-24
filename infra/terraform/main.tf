# Demo infrastructure modelled with local/null/random providers only, so the
# full `terraform init/validate/plan/apply` cycle runs in CI with no cloud
# account. InfraPilot reads infra/desired_state.yaml as the logical source of
# truth; these resources make the Terraform path real and validatable.

locals {
  managed = {
    web-sg      = { type = "security_group", provider = "aws" }
    app-data    = { type = "storage_bucket", provider = "aws" }
    api-vm      = { type = "compute_instance", provider = "gcp" }
    edge-router = { type = "network_device", provider = "on_prem" }
  }
}

resource "random_id" "deployment" {
  byte_length = 4
}

# Stand-in for the provisioned resources; one null_resource per managed item.
resource "null_resource" "resource" {
  for_each = local.managed

  triggers = {
    name        = each.key
    type        = each.value.type
    provider    = each.value.provider
    environment = var.environment
  }
}

# Emit the rendered inventory as an artifact (what a real apply would output).
resource "local_file" "inventory" {
  filename = "${path.module}/.generated/inventory.json"
  content = jsonencode({
    deployment_id = random_id.deployment.hex
    environment   = var.environment
    default_tags  = var.default_tags
    resources     = local.managed
  })
}
