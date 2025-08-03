variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"
  # The default value is set to 'development' for initial testing purposes.
  # You can change it to 'staging' or 'production' as needed.
  validation {
    # This validation ensures that the environment variable is set to one of the specified values.
    condition = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "AppName" {
  description = "The name of the Application Insights instance. If blank, a random name will be generated."
  type        = string
  default     = "olympiakos"
}

variable "ResourceGroupName" {
  type        = string
  default     = "OlympiakosGroup"
  description = "The name of the Azure resource group. If blank, a random name will be generated."
}

variable "ResourceGroupNamePrefix" {
  type        = string
  default     = "Olympiakos"
  description = "Prefix of the resource group name that's combined with a random ID so name is unique in your Azure subscription."
}

variable "ResourceGroupLocation" {
  type        = string
  default     = "francecentral"
  description = "Location of the resource group."
}

variable "StorageAccountName" {
  type        = string
  default     = "olympiakossa"
  description = "Name of the storage account."
}

variable "SaAccountTier" {
  description = "The tier of the storage account. Possible values are Standard and Premium."
  type        = string
  default     = "Standard"
}

variable "SaAccountReplicationType" {
  description = "The replication type of the storage account. Possible values are LRS, GRS, RAGRS, and ZRS."
  type        = string
  default     = "LRS"
}
variable "WsName" {
  description = "The name of the Log Analytics workspace."
  type        = string
  default     = "OlympiakosWorkspace"
}
variable "AspName" {
  description = "The name of the App Service Plan."
  type        = string
  default     = "OlympiakosServicePlan"
}

variable "FunctionAppSku" {
  description = "The sku of the function."
  type        = string
  default     = "S1"
}

variable "SqlServerName" {
  description = "The name of the SQL server. only lowercase letters, numbers, and hyphens are allowed. "
  type        = string
  default     = "olympiakos-sqlserver"
}
variable "SqlAdminLogin" {
  description = "The name of the SQL server."
  type        = string
  default     = "sqlAdmin"
}

variable "OlympiakosSqlDatabaseName" {
  description = "The name of the SQL database."
  type        = string
  default     = "OlympiakosDatabase"
}

variable "OfficeIpRuleName" {
  description = "The name of the IP rule for the SQL server."
  type        = string
  default     = "office_ip_rule"
}
variable "HomeIpRuleName" {
  description = "The name of the IP rule for the SQL server."
  type        = string
  default     = "home_ip_rule"
}

variable "OfficeIp" {
  description = "The IP address of your office to allow access to the SQL server."
  type        = string
  default     = "<YOUR_OFFICE_IP_HERE>"
}

variable "HomeIp" {
  description = "The IP address of your office to allow access to the SQL server."
  type        = string
  default     = "<YOUR_HOME_IP_HERE>"
}



variable "SubscriptionId" {
  description = "The Azure subscription ID to use for the resources."
  type        = string
  default     = "<YOUR_SUBSCRIPTION_ID_HERE>"
}


variable "DockerImageTag" {
  description = "The Docker image tag for the Function App container."
  type        = string
  default     = "dev" # Or your desired default tag
}

variable "ModelBlobStorageContainerName" {
  description = "The name of the blob container for storing ML models."
  type        = string
  default     = "models"
}
variable "LogsBlobStorageContainerName" {
  description = "The name of the blob container for storing data."
  type        = string
  default     = "container-logs"
}



