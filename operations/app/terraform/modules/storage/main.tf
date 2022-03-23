#data "azurerm_client_config" "current" {}

resource "azurerm_storage_account" "pdi_data" {
  resource_group_name       = var.resource_group_name
  name                      = "${var.resource_prefix}datasa"
  location                  = var.location
  account_kind              = "StorageV2"
  account_tier              = "Standard"
  account_replication_type  = "GRS"
  min_tls_version           = "TLS1_2"
  allow_blob_public_access  = false
  enable_https_traffic_only = true
  is_hns_enabled            = true
  shared_access_key_enabled = false

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]

    virtual_network_subnet_ids = var.app_subnet_ids
  }

  blob_properties {
    change_feed_enabled = false
    versioning_enabled  = false
  }

  # Required for customer-managed encryption
  identity {
    type = "SystemAssigned"
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      tags,
      shared_access_key_enabled,
      network_rules[0].ip_rules
    ]
  }

  tags = {
    environment = var.environment
    managed-by  = "terraform"
  }
}

/* Generate multiple storage private endpoints via for_each */
module "storageaccount_private_endpoint" {
  for_each = toset(["blob", "file", "queue"])
  source   = "../common/private_sa_endpoint"
  primary = {
    name                = "${azurerm_storage_account.pdi_data.name}-${each.key}-privateendpoint"
    type                = "storage_account_${each.key}"
    location            = "eastus"
    resource_group_name = var.resource_group_name
    environment         = var.environment
  }

  endpoint_subnet_ids = [var.cdc_service_subnet_id]

  private_dns_zone_group = {
    id                   = "${var.resource_group_id}/providers/Microsoft.Network/privateEndpoints/${azurerm_storage_account.pdi_data.name}-${each.key}-privateendpoint/privateDnsZoneGroups/default"
    name                 = "default"
    private_dns_zone_ids = "${var.resource_group_id}/providers/Microsoft.Network/privateDnsZones/privatelink.${each.key}.core.windows.net"
  }

  private_service_connection = {
    is_manual_connection           = false
    name                           = "${azurerm_storage_account.pdi_data.name}-${each.key}-privateendpoint"
    private_connection_resource_id = azurerm_storage_account.pdi_data.id
    subresource_names              = "${each.key}"
  }

  depends_on = [azurerm_storage_account.pdi_data]
}

# Point-in-time restore, soft delete, versioning, and change feed were
# enabled in the portal as terraform does not currently support this.
# At some point, this should be moved into an azurerm_template_deployment
# resource.
# These settings can be configured under the "Data protection" blade
# for Blob service

# Grant the storage account Key Vault access, to access encryption keys
# resource "azurerm_key_vault_access_policy" "storage_policy" {
#   key_vault_id = var.application_key_vault_id
#   tenant_id    = azurerm_storage_account.pdi_data.identity.0.tenant_id
#   object_id    = azurerm_storage_account.pdi_data.identity.0.principal_id

#   key_permissions = ["Get", "UnwrapKey", "WrapKey"]
# }

# resource "azurerm_storage_account_customer_managed_key" "storage_key" {
#   count              = var.rsa_key_4096 != null && var.rsa_key_4096 != "" ? 1 : 0
#   key_name           = var.rsa_key_4096
#   key_vault_id       = var.application_key_vault_id
#   key_version        = null // Null allows automatic key rotation
#   storage_account_id = azurerm_storage_account.pdi_data.id

#   depends_on = [azurerm_key_vault_access_policy.storage_policy]
# }
