output "resource_group_name" {
  value = azurerm_resource_group.resource_group.name
}


output "function_app_url" {
  value = azurerm_linux_function_app.olympiakos_function_app.default_hostname
}

output "sql_server_fqdn" {
  value = azurerm_mssql_server.sql_server.fully_qualified_domain_name
}

output "storage_account_name" {
  value = azurerm_storage_account.StorageAccount.name
}

output "sql_scripts_created" {
  description = "The paths to the generated SQL scripts."
  value       = [for script in local_file.sql_script_files : script.filename]
}

output "function_app_default_hostname" {
    description = "The default hostname of the function app"
    value = azurerm_linux_function_app.olympiakos_function_app.default_hostname
}

output "sql_admin_password" {
    description = "The generated SQL admin password. Store this securely."
    value = random_password.sql_admin_password.result
    sensitive = true
}

output "sql_connection_info" {
  value = {
    server   = azurerm_mssql_server.sql_server.fully_qualified_domain_name
    database = azurerm_mssql_database.sql_database.name
    username = var.SqlAdminLogin
  }
  sensitive = false
}

output "acr_login_server" {
  description = "The login server of the Azure Container Registry."
  value       = azurerm_container_registry.acr.login_server
}

output "function_app_name" {
  description = "The name of the Azure Function App."
  value       = azurerm_linux_function_app.olympiakos_function_app.name
}