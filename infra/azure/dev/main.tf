resource "azurerm_resource_group" "runner" {
  name     = var.resource_group_name
  location = var.location

  tags = merge(var.tags, {
    env = var.environment
  })
}