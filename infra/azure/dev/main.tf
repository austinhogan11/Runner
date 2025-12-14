resource "azurerm_resource_group" "runner" {
  name     = var.resource_group_name
  location = var.location

  tags = merge(var.tags, {
    env = var.environment
  })
}

resource "azurerm_container_registry" "runner" {
  name                = "runneracr${replace(var.environment, "-", "")}"
  resource_group_name = azurerm_resource_group.runner.name
  location            = azurerm_resource_group.runner.location

  sku           = "Basic"
  admin_enabled = false

  tags = merge(var.tags, {
    env = var.environment
  })
}

resource "azurerm_log_analytics_workspace" "runner" {
  name                = "runner-law-${var.environment}"
  location            = azurerm_resource_group.runner.location
  resource_group_name = azurerm_resource_group.runner.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = merge(var.tags, { env = var.environment })
}

resource "azurerm_virtual_network" "runner" {
  name                = "runner-vnet-${var.environment}"
  location            = azurerm_resource_group.runner.location
  resource_group_name = azurerm_resource_group.runner.name
  address_space       = ["10.10.0.0/16"]

  tags = merge(var.tags, { env = var.environment })
}

resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet-${var.environment}"
  resource_group_name  = azurerm_resource_group.runner.name
  virtual_network_name = azurerm_virtual_network.runner.name
  address_prefixes     = ["10.10.1.0/24"]
}

resource "azurerm_kubernetes_cluster" "runner" {
  name                = "runner-aks-${var.environment}"
  location            = azurerm_resource_group.runner.location
  resource_group_name = azurerm_resource_group.runner.name
  dns_prefix          = "runner-aks-${var.environment}"

  kubernetes_version  = null # let Azure choose default stable

  default_node_pool {
    name           = "system"
    node_count     = 1
    vm_size        = var.aks_node_vm_size
    vnet_subnet_id = azurerm_subnet.aks.id
  }

  identity {
    type = "SystemAssigned"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.runner.id
  }

  tags = merge(var.tags, { env = var.environment })
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.runner.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.runner.kubelet_identity[0].object_id

  depends_on = [
    azurerm_kubernetes_cluster.runner,
    azurerm_container_registry.runner
  ]
}