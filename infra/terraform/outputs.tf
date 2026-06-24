output "deployment_id" {
  description = "Unique id for this apply."
  value       = random_id.deployment.hex
}

output "managed_resources" {
  description = "Logical resources placed under management."
  value       = keys(local.managed)
}
