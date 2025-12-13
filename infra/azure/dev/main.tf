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