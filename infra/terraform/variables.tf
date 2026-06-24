variable "environment" {
  description = "Target environment name."
  type        = string
  default     = "demo"
}

variable "default_tags" {
  description = "Tags applied to every managed resource (enforced by policy TAG-001)."
  type        = map(string)
  default = {
    owner      = "platform-team"
    managed_by = "infrapilot"
  }
}
