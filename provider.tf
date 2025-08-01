terraform {
  # Specify the required Terraform version
  required_version = ">=1.0"
  # Define the required providers
  required_providers {
    # Azure Resource Manager provider
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>4.0"
    }
    # Random provider for generating random values
    random = {
      source  = "hashicorp/random"
      version = "~>3.0"
    }
    # Local provider for local file operations
    azapi = {
      source = "Azure/azapi"
    }
    # Archive provider for creating zip files
    # This is used to package the function app code into a zip file
    archive = {
        source = "hashicorp/archive"
    }
    # Local provider for local file operations
    # This is used to manage local files, such as the SQL scripts
    local = {
        source  = "hashicorp/local"
        version = ">=2.1"
      }
  }
}
# Configure the Azure provider
# This block sets up the Azure provider with the necessary features and subscription ID
provider "azurerm" {
  features {}
  subscription_id = var.SubscriptionId
}