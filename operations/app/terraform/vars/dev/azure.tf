terraform {
  required_version = ">= 1.0.5, < 1.2.0" # This version must also be changed in other environments

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 2.61.0" # This version must also be changed in other environments
    }
  }

  backend "azurerm" {
    resource_group_name  = "prime-ingestion-dev"
    storage_account_name = "pidevterraform"
    container_name       = "terraformstate"
    key                  = "prime-ingestion-dev.tfstate"
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
  subscription_id            = "7d1e3999-6577-4cd5-b296-f518e5c8e677"
  storage_use_azuread        = true
}
