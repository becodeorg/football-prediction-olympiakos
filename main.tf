# This Terraform configuration creates an Azure Resource Group with Function App and SQL Database

resource "random_uuid" "random_id" {
  # This generates a random UUID to ensure unique resource names
}

# Generate a strong, random password for the SQL administrator
resource "random_password" "sql_admin_password" {
  length           = 16
  special          = true
  min_upper        = 1
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
}
# Create a resource group for the Azure resources
resource "azurerm_resource_group" "resource_group"{
    name     = var.ResourceGroupName
    location = var.ResourceGroupLocation
}
# Create a resource group for the Azure resources
resource "azurerm_storage_account" "StorageAccount" {
  name                 = var.StorageAccountName
  resource_group_name  = azurerm_resource_group.resource_group.name
  location             = azurerm_resource_group.resource_group.location
  account_tier         = var.SaAccountTier
  account_replication_type = var.SaAccountReplicationType

  tags = {
    environment = var.environment
  }
}

# Create a blob container for storing ML models
resource "azurerm_storage_container" "models_container" {
  name                  = var.ModelBlobStorageContainerName
  storage_account_id  = azurerm_storage_account.StorageAccount.id
  container_access_type = "private"  # Private access for security
}
resource "azurerm_storage_container" "logs_container" {
  name                  = var.LogsBlobStorageContainerName
  storage_account_name  = azurerm_storage_account.StorageAccount.name
  container_access_type = "private"
}

# Grant the Function App's managed identity access to the storage account
# resource "azurerm_role_assignment" "function_app_api_storage_blob_data" {
#   scope                = azurerm_storage_account.StorageAccount.id
#   role_definition_name = "Storage Blob Data Contributor"
#   principal_id         = azurerm_linux_function_app.olympiakos_function_app.identity[0].principal_id

#   depends_on = [azurerm_linux_function_app.olympiakos_function_app]
# }

# Create a container registry for the function app
# This is used to store the Docker images for the function app
resource "azurerm_container_registry" "acr" {
  name                = "${var.AppName}acr"
  resource_group_name = azurerm_resource_group.resource_group.name
  location            = azurerm_resource_group.resource_group.location
  sku                 = "Basic"
  admin_enabled       = true
}

# Create a Log Analytics workspace for Application Insights
resource "azurerm_log_analytics_workspace" "log_analytics_workspace" {
  name                = coalesce(var.WsName, "${var.ResourceGroupName}-loganalytics")
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name
  retention_in_days   = 30
}

# Create an Application Insights instance for monitoring
resource "azurerm_application_insights" "app_insights" {
  name                = "${var.AppName}-appinsights"
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.log_analytics_workspace.id
}

# Create a service plan
resource "azurerm_service_plan" "service_plan" {
  name                = var.AspName
  resource_group_name = azurerm_resource_group.resource_group.name
  location            = azurerm_resource_group.resource_group.location
  sku_name            = var.FunctionAppSku
  os_type             = "Linux"
  
}


# Create SQL Server
resource "azurerm_mssql_server" "sql_server" {
  name                         = var.SqlServerName
  resource_group_name          = azurerm_resource_group.resource_group.name
  location                     = azurerm_resource_group.resource_group.location
  version                      = "12.0"
  administrator_login          = var.SqlAdminLogin
  administrator_login_password = random_password.sql_admin_password.result  
  minimum_tls_version          = "1.2"
  
  tags = {
    environment = var.environment
  }
}
# Create SQL Database
resource "azurerm_mssql_database" "sql_database" {
  name         = var.OlympiakosSqlDatabaseName
  server_id    = azurerm_mssql_server.sql_server.id
  collation    = "SQL_Latin1_General_CP1_CI_AS" # Default collation
  license_type = "LicenseIncluded" # Use LicenseIncluded for Azure SQL Database
  max_size_gb  = 2 # Set max size to 2GB for the demo
  sku_name     = "S0" # Use S0 tier for the demo

  lifecycle {
    prevent_destroy = true # Prevent accidental deletion of the SQL Database
  }

  tags = {
    environment = var.environment
  }
}

# Create a function app with system-assigned managed identity
# Create a function app with system-assigned managed identity
resource "azurerm_linux_function_app" "olympiakos_function_app" {
  name                = var.AppName
  resource_group_name = azurerm_resource_group.resource_group.name
  location            = azurerm_resource_group.resource_group.location
  service_plan_id     = azurerm_service_plan.service_plan.id
  storage_account_name = azurerm_storage_account.StorageAccount.name
  storage_account_access_key = azurerm_storage_account.StorageAccount.primary_access_key
  
  # Enable system-assigned managed identity
  identity {
    type = "SystemAssigned"
  }

  site_config {
     always_on            = true
    #linux_fx_version = "DOCKER|${azurerm_container_registry.acr.login_server}/${var.AppName}:${var.DockerImageTag}"
    # Python runtime version is now handled by the Docker image, so this block is removed.
    application_stack {
        #python_version = "3.10"
         docker {
            # Use the Docker image from the Azure Container Registry
            image_name = var.AppName
            registry_url = "https://${azurerm_container_registry.acr.login_server}"
            registry_username = azurerm_container_registry.acr.admin_username
            registry_password = azurerm_container_registry.acr.admin_password
            image_tag= var.DockerImageTag
        }
    }
   
    # Enable additional logging for debugging
    #application_insights_key         = azurerm_application_insights.app_insights.instrumentation_key
    application_insights_connection_string = azurerm_application_insights.app_insights.connection_string
  }
    
  # app settings
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"              = "python" 
    "AzureWebJobsStorage"                   = azurerm_storage_account.StorageAccount.primary_connection_string 
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.app_insights.connection_string 
    "FUNCTIONS_EXTENSION_VERSION"           = "~4"
    "SQL_CONNECTION_STRING_ODBC"            = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:${azurerm_mssql_server.sql_server.fully_qualified_domain_name},1433;Database=${azurerm_mssql_database.sql_database.name};Uid=${var.SqlAdminLogin};Pwd=${random_password.sql_admin_password.result};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE"   = "false" # Recommended for stateless containers
    "WEBSITES_PORT"                         = "80"
    "DOCKER_ENABLE_CI"                      = "true"
    "SCM_DO_BUILD_DURING_DEPLOYMENT"        = "false"
    "WEBSITE_RUN_FROM_PACKAGE"              = "0"
    always_on            = true
    "DOCKER_CUSTOM_IMAGE_NAME"             = "${azurerm_container_registry.acr.login_server}/${var.AppName}:${var.DockerImageTag}"
    # Blob Storage Configuration
    "STORAGE_ACCOUNT_NAME"                 = azurerm_storage_account.StorageAccount.name
    "STORAGE_ACCOUNT_URL"                  = azurerm_storage_account.StorageAccount.primary_blob_endpoint
    #"LOGS_CONTAINER_NAME"                  = azurerm_storage_container.logs_container.name
    # Use managed identity for blob access (more secure than connection strings)
    #"AZURE_CLIENT_ID"                      = "managed_identity"  # Special value for system-assigned identity
    "AZURE_STORAGE_CONNECTION_STRING"       = azurerm_storage_account.StorageAccount.primary_connection_string
    "MODELS_CONTAINER_NAME"                 = var.ModelBlobStorageContainerName
    "LOGS_CONTAINER_NAME"                   = var.LogsBlobStorageContainerName
  }

  tags = {
    environment = var.environment
  }

  # depends on other resources to ensure they are created before the function app
  # This ensures that the function app is created after the storage account, ACR, SQL server, and SQL database
  depends_on = [
    azurerm_storage_account.StorageAccount,
    azurerm_container_registry.acr, # Now depends on ACR instead of storage blob
    azurerm_mssql_server.sql_server,
    azurerm_mssql_database.sql_database,
  ]
}

# Removed: Role Assignment for Function App's Managed Identity to access storage
# This role assignment was for WEBSITE_RUN_FROM_PACKAGE, not needed for Docker image deployment

# Create a firewall rule for office IP
resource "azurerm_mssql_firewall_rule" "office_ip_rule" {
  name             = var.OfficeIpRuleName
  server_id        = azurerm_mssql_server.sql_server.id
  start_ip_address = var.OfficeIp
  end_ip_address   = var.OfficeIp
}
# Create a firewall rule for home IP
resource "azurerm_mssql_firewall_rule" "home_ip_rule" {
  name             = var.HomeIpRuleName
  server_id        = azurerm_mssql_server.sql_server.id
  start_ip_address = var.HomeIp
  end_ip_address   = var.HomeIp
}
# Create a firewall rule to allow Azure services to access the SQL server
resource "azurerm_mssql_firewall_rule" "azure_services_rule" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.sql_server.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Optional: Add Azure AD admin for SQL Server (recommended for production)
# resource "azurerm_mssql_server_extended_auditing_policy" "sql_server_audit" {
#   server_id                      = azurerm_mssql_server.sql_server.id
#   storage_endpoint               = azurerm_storage_account.StorageAccount.primary_blob_endpoint
#   storage_account_access_key     = azurerm_storage_account.StorageAccount.primary_access_key
#   storage_account_access_key_is_secondary = false
#   retention_in_days              = 30
# }

# Database initialization scripts
locals {
  sql_scripts = {
    "01_tables" = templatefile("${path.module}/sql_templates/tables.sql.tpl", {
      database_name = azurerm_mssql_database.sql_database.name
    })
    # "02_data" = templatefile("${path.module}/sql_templates/initial_data.sql.tpl", {
    #   environment = var.environment
    # })
    "02_procedures" = file("${path.module}/sql_templates/stored_procedures.sql")
  }
}

# Create local files for each SQL script
# This allows us to use the local_file resource to create files from the templates
resource "local_file" "sql_script_files" {
  for_each = local.sql_scripts
  content  = each.value
  filename = "${path.module}/sql_templates/${each.key}.sql"
}


# Execute the SQL scripts using the files created above
resource "null_resource" "execute_templated_sql" {
  for_each = local_file.sql_script_files
  # triggered when the content of the SQL script changes
  # This ensures that the SQL script is executed only when its content changes
  triggers = {
    # Use md5() on the content, which is known at plan time
    script_hash = md5(each.value.content)
  }

  provisioner "local-exec" {
    # Use sqlcmd to execute the SQL script against the SQL database
    # This assumes sqlcmd is installed and available in the PATH      
    command = <<EOT
      sqlcmd -S "${azurerm_mssql_server.sql_server.fully_qualified_domain_name}" -d "${azurerm_mssql_database.sql_database.name}" -U "${var.SqlAdminLogin}" -P "${random_password.sql_admin_password.result}" -i "${each.value.filename}"
    EOT
    interpreter = ["PowerShell", "-Command"]
  }

  # This ensures that the SQL scripts are executed after the SQL server and database are created
  depends_on = [
    azurerm_mssql_firewall_rule.azure_services_rule,
    azurerm_mssql_firewall_rule.home_ip_rule,
    azurerm_mssql_firewall_rule.office_ip_rule,
    local_file.sql_script_files
  ]
}
