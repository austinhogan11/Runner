output "resource_group_name" {
  value = azurerm_resource_group.runner.name
}

output "resource_group_location" {
  value = azurerm_resource_group.runner.location
}

output "acr_login_server" {
  value = azurerm_container_registry.runner.login_server
}

output "aks_name" {
  value = azurerm_kubernetes_cluster.runner.name
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.runner.fqdn
}

output "postgres_admin_user" {
  value = azurerm_postgresql_flexible_server.runner.administrator_login
}

output "postgres_admin_password" {
  value     = random_password.postgres.result
  sensitive = true
}

output "postgres_db_name" {
  value = azurerm_postgresql_flexible_server_database.runner.name
}