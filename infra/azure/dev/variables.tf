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
  default     = "Standard_D2s_v3"
}

variable "aks_node_count" {
  type        = number
  description = "AKS default node count"
  default     = 1
}

variable "acr_sku" {
  type        = string
  description = "Azure Container Registry SKU"
  default     = "Basic"
}

# Postgres (Flexible Server) settings
variable "postgres_private_access" {
  type        = bool
  description = "Use private access (VNet + delegated subnet + private DNS)"
  default     = false
}

variable "postgres_location" {
  type        = string
  description = "Region to deploy Postgres (can differ from AKS region)"
  default     = "eastus"
}

variable "postgres_admin_user" {
  type        = string
  description = "Postgres admin username"
  default     = "runneradmin"
}

variable "postgres_sku_name" {
  type        = string
  description = "Flexible Server SKU (e.g., B_Standard_B1ms, GP_Standard_D2s_v3)"
  default     = "B_Standard_B1ms"
}

variable "postgres_version" {
  type        = string
  description = "Postgres major version"
  default     = "16"
}

variable "postgres_db_name" {
  type        = string
  description = "Application database name"
  default     = "runner"
}

variable "postgres_storage_mb" {
  type        = number
  description = "Flexible Server storage in MB"
  default     = 32768
}

variable "postgres_firewall_start_ip" {
  type        = string
  description = "Public firewall start IP (public mode only)"
  default     = "0.0.0.0"
}

variable "postgres_firewall_end_ip" {
  type        = string
  description = "Public firewall end IP (public mode only)"
  default     = "255.255.255.255"
}

# Postgres (Flexible Server) settings
variable "postgres_admin_user" {
  type        = string
  description = "Postgres admin username"
  default     = "runneradmin"
}

variable "postgres_sku_name" {
  type        = string
  description = "Flexible Server SKU (e.g., B_Standard_B1ms, GP_Standard_D2s_v3)"
  default     = "B_Standard_B1ms"
}

variable "postgres_version" {
  type        = string
  description = "Postgres major version"
  default     = "16"
}

variable "postgres_db_name" {
  type        = string
  description = "Application database name"
  default     = "runner"
}

variable "postgres_storage_mb" {
  type        = number
  description = "Flexible Server storage in MB"
  default     = 32768
}
