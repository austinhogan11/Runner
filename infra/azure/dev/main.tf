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
  admin_enabled = true

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

resource "random_password" "postgres" {
  length  = 24
  special = true
}

# Subnet dedicated to Postgres Flexible Server (delegated)
resource "azurerm_subnet" "postgres" {
  name                 = "postgres-subnet-${var.environment}"
  resource_group_name  = azurerm_resource_group.runner.name
  virtual_network_name = azurerm_virtual_network.runner.name
  address_prefixes     = ["10.10.2.0/24"]

  delegation {
    name = "postgres-flexible-delegation"

    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# Private DNS zone for Postgres private access
resource "azurerm_private_dns_zone" "postgres" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.runner.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "runner-postgres-dnslink-${var.environment}"
  resource_group_name   = azurerm_resource_group.runner.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.runner.id
}

resource "azurerm_postgresql_flexible_server" "runner" {
  name                   = "runner-pg-${var.environment}"
  resource_group_name    = azurerm_resource_group.runner.name
  location               = azurerm_resource_group.runner.location

  administrator_login    = var.postgres_admin_user
  administrator_password = random_password.postgres.result

  version                = var.postgres_version
  sku_name               = var.postgres_sku_name

  storage_mb             = 32768

  delegated_subnet_id    = azurerm_subnet.postgres.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres.id

  public_network_access_enabled = false

  depends_on = [
    azurerm_private_dns_zone_virtual_network_link.postgres
  ]

  tags = merge(var.tags, { env = var.environment })
}

resource "azurerm_postgresql_flexible_server_database" "runner" {
  name      = var.postgres_db_name
  server_id = azurerm_postgresql_flexible_server.runner.id
  collation = "en_US.utf8"
  charset   = "UTF8"
}