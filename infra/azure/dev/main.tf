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

  sku           = var.acr_sku
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

  # Let Azure choose a stable default Kubernetes version

  default_node_pool {
    name           = "system"
    node_count     = var.aks_node_count
    vm_size        = var.aks_node_vm_size
    vnet_subnet_id = azurerm_subnet.aks.id
  }

  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
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

resource "random_string" "pg_suffix" {
  length  = 4
  upper   = false
  special = false
}

# Postgres settings
locals {
  postgres_name = "runner-pg-${var.environment}-${random_string.pg_suffix.result}"
}

resource "random_password" "postgres" {
  length  = 24
  special = true
}

# Public Postgres (Option A - default)
resource "azurerm_postgresql_flexible_server" "runner" {
  name                   = local.postgres_name
  resource_group_name    = azurerm_resource_group.runner.name
  location               = var.postgres_location

  administrator_login    = var.postgres_admin_user
  administrator_password = random_password.postgres.result

  version                = var.postgres_version
  sku_name               = var.postgres_sku_name
  storage_mb             = var.postgres_storage_mb

  public_network_access_enabled = true

  tags = merge(var.tags, { env = var.environment })
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "all" {
  name             = "allow-all-smoke"
  server_id        = azurerm_postgresql_flexible_server.runner.id
  start_ip_address = var.postgres_firewall_start_ip
  end_ip_address   = var.postgres_firewall_end_ip
}

resource "azurerm_postgresql_flexible_server_database" "runner" {
  name      = var.postgres_db_name
  server_id = azurerm_postgresql_flexible_server.runner.id
  collation = "en_US.utf8"
  charset   = "UTF8"
}
