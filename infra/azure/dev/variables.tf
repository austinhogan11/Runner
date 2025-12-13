variable "environment" {
  type        = string
  description = "Environment name (dev/uat/prod)"
  default     = "dev"
}

variable "location" {
  type        = string
  description = "Azure region"
  default     = "eastus"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
  default     = "runner-dev-rg"
}

variable "tags" {
  type        = map(string)
  description = "Common tags"
  default = {
    app = "runner"
  }
}