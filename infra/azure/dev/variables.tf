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
