variable "environment" {
  type        = string
  description = "Environment name (dev/uat/prod)"
  default     = "dev"
}

variable "location" {
  type        = string
  description = "Azure region"
  default     = "eastus2"
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

variable "aks_node_vm_size" {
  type        = string
  description = "AKS node pool VM size"
  default     = "standard_dc2s_v3"
}

variable "postgres_admin_user" {
  type        = string
  description = "Postgres admin username"
  default     = "runneradmin"
}

variable "postgres_sku_name" {
  type        = string
  description = "Flexible server SKU"
  default     = "B_Standard_B1ms"
}

variable "postgres_version" {
  type        = string
  description = "Postgres major version"
  default     = "16"
}

variable "postgres_db_name" {
  type        = string
  description = "App database name"
  default     = "runner"
}