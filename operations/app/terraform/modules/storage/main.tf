data "azurerm_client_config" "current" {}

# Also, the convention "{prefix}storage" was already taken, which is why this was
# changed to "{prefix}datastorage"
resource "azurerm_storage_account" "storage_account" {
  resource_group_name       = var.resource_group
  name                      = "${var.resource_prefix}datastorage"
  location                  = var.location
  account_kind              = "StorageV2"
  account_tier              = "Standard"
  account_replication_type  = "GRS"
  min_tls_version           = "TLS1_2"
  allow_blob_public_access  = false
  enable_https_traffic_only = true

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]

    # ip_rules = sensitive(concat(
    #   split(",", data.azurerm_key_vault_secret.cyberark_ip_ingress.value),
    #   [split("/", var.terraform_caller_ip_address)[0]], # Storage accounts only allow CIDR-notation for /[0-30]
    # ))

    #ip_rules = [var.terraform_caller_ip_address]

    virtual_network_subnet_ids = var.app_subnet_ids
  }

  # Required for customer-managed encryption
  identity {
    type = "SystemAssigned"
  }

  lifecycle {
    prevent_destroy = false
  }

  tags = {
    environment = var.environment
  }
}

# Turns out that creating containers in storage accounts doesn't work like you'd expect; may be able
# to inline a template for it.
#
# See: https://github.com/hashicorp/terraform-provider-azurerm/issues/2977
# resource "azurerm_storage_container" "data_bronze" {
#   name                  = "bronze"
#   storage_account_name  = azurerm_storage_account.storage_account.name
#   container_access_type = "private"
# }
# 
# resource "azurerm_storage_container" "data_silver" {
#   name                  = "silver"
#   storage_account_name  = azurerm_storage_account.storage_account.name
#   container_access_type = "private"
# }
# 
# resource "azurerm_storage_container" "data_gold" {
#   name                  = "gold"
#   storage_account_name  = azurerm_storage_account.storage_account.name
#   container_access_type = "private"
# }

module "storageaccount_blob_private_endpoint" {
  source = "../common/private_sa_endpoint"
  primary = {
    name           = "pitestdatastorage-blob-privateendpoint"
    type           = "storage_account_blob"
    location       = "eastus"
    resource_group = var.resource_group
  }

  endpoint_subnet_ids = [var.cdc_service_subnet_id]

  private_dns_zone_group = {
    id                   = "/subscriptions/7d1e3999-6577-4cd5-b296-f518e5c8e677/resourceGroups/prime-ingestion-test/providers/Microsoft.Network/privateEndpoints/pitestdatastorage-blob-privateendpoint/privateDnsZoneGroups/default"
    name                 = "default"
    private_dns_zone_ids = "/subscriptions/7d1e3999-6577-4cd5-b296-f518e5c8e677/resourceGroups/prime-ingestion-test/providers/Microsoft.Network/privateDnsZones/privatelink.blob.core.windows.net"
  }

  private_service_connection = {
    is_manual_connection           = false
    name                           = "pitestdatastorage-blob-privateendpoint"
    private_connection_resource_id = "/subscriptions/7d1e3999-6577-4cd5-b296-f518e5c8e677/resourceGroups/prime-ingestion-test/providers/Microsoft.Storage/storageAccounts/pitestdatastorage"
    subresource_names              = "blob"
  }
}

module "storageaccount_file_private_endpoint" {
  source = "../common/private_sa_endpoint"
  primary = {
    name           = "pitestdatastorage-file-privateendpoint"
    type           = "storage_account_file"
    location       = "eastus"
    resource_group = var.resource_group
  }

  endpoint_subnet_ids = [var.cdc_service_subnet_id]

  private_dns_zone_group = {
    id                   = "/subscriptions/7d1e3999-6577-4cd5-b296-f518e5c8e677/resourceGroups/prime-ingestion-test/providers/Microsoft.Network/privateEndpoints/pitestdatastorage-file-privateendpoint/privateDnsZoneGroups/default"
    name                 = "default"
    private_dns_zone_ids = "/subscriptions/7d1e3999-6577-4cd5-b296-f518e5c8e677/resourceGroups/prime-ingestion-test/providers/Microsoft.Network/privateDnsZones/privatelink.file.core.windows.net"
  }

  private_service_connection = {
    is_manual_connection           = false
    name                           = "pitestdatastorage-file-privateendpoint"
    private_connection_resource_id = "/subscriptions/7d1e3999-6577-4cd5-b296-f518e5c8e677/resourceGroups/prime-ingestion-test/providers/Microsoft.Storage/storageAccounts/pitestdatastorage"
    subresource_names              = "file"
  }
}

module "storageaccount_queue_private_endpoint" {
  source = "../common/private_sa_endpoint"
  primary = {
    name           = "pitestdatastorage-queue-privateendpoint"
    type           = "storage_account_queue"
    location       = "eastus"
    resource_group = var.resource_group
  }

  endpoint_subnet_ids = [var.cdc_service_subnet_id]

  private_dns_zone_group = {
    id                   = "/subscriptions/7d1e3999-6577-4cd5-b296-f518e5c8e677/resourceGroups/prime-ingestion-test/providers/Microsoft.Network/privateEndpoints/pitestdatastorage-queue-privateendpoint/privateDnsZoneGroups/default"
    name                 = "default"
    private_dns_zone_ids = "/subscriptions/7d1e3999-6577-4cd5-b296-f518e5c8e677/resourceGroups/prime-ingestion-test/providers/Microsoft.Network/privateDnsZones/privatelink.queue.core.windows.net"
  }

  private_service_connection = {
    is_manual_connection           = false
    name                           = "pitestdatastorage-queue-privateendpoint"
    private_connection_resource_id = "/subscriptions/7d1e3999-6577-4cd5-b296-f518e5c8e677/resourceGroups/prime-ingestion-test/providers/Microsoft.Storage/storageAccounts/pitestdatastorage"
    subresource_names              = "queue"
  }
}

# Point-in-time restore, soft delete, versioning, and change feed were
# enabled in the portal as terraform does not currently support this.
# At some point, this should be moved into an azurerm_template_deployment
# resource.
# These settings can be configured under the "Data protection" blade
# for Blob service

# Grant the storage account Key Vault access, to access encryption keys
resource "azurerm_key_vault_access_policy" "storage_policy" {
  key_vault_id = var.application_key_vault_id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_storage_account.storage_account.identity.0.principal_id

  key_permissions = ["get", "unwrapkey", "wrapkey"]
}

resource "azurerm_storage_account_customer_managed_key" "storage_key" {
  count              = var.rsa_key_4096 != null && var.rsa_key_4096 != "" ? 1 : 0
  key_name           = var.rsa_key_4096
  key_vault_id       = var.application_key_vault_id
  key_version        = null // Null allows automatic key rotation
  storage_account_id = azurerm_storage_account.storage_account.id

  depends_on = [azurerm_key_vault_access_policy.storage_policy]
}
