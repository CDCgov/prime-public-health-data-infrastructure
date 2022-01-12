locals {
#   dns_zones_private = [
#     "privatelink.vaultcore.azure.net",
#     "privatelink.postgres.database.azure.com",
#     "privatelink.blob.core.windows.net",
#     "privatelink.file.core.windows.net",
#     "privatelink.queue.core.windows.net",
#     #"privatelink.azurecr.io",
#     "privatelink.servicebus.windows.net",
#     "privatelink.azurewebsites.net",
#     "prime.local",
#   ]

#   # Due to only a single DNS record allowed per resource group, some private endpoints conflicts in with multiple VNETs
#   # By omitting the DNS records, we ensure the Azure backbone is used instead of attempting to reach an unpeered VNET
#   omit_dns_zones_private_in_cdc_vnet = [
#     "privatelink.vaultcore.azure.net",
#   ]

  # not sure if these are still needed... we may turn them into outputs instead...
  # vnet_primary_name = var.cdc_vnet_name
  # vnet_primary      = data.azurerm_virtual_network.cdc_vnet[local.vnet_primary_name]
  # vnet_names = [
  #   local.vnet_primary_name
  # ]
}

# we need this data lookup because we need to reference/manipulate
# the CDC-managed VNet and subnet
data "azurerm_virtual_network" "cdc_vnet" {
  name                 = var.cdc_vnet_name
  resource_group_name  = var.resource_group
}

data "azurerm_subnet" "cdc_subnet" {
  name                 = var.cdc_subnet_name
  resource_group_name  = var.resource_group
  virtual_network_name = var.cdc_vnet_name
}

# Note that I manually added to this subnet the equivalent of:
#   service_endpoints    = [
#     "Microsoft.Storage",
#     "Microsoft.KeyVault",
#     "Microsoft.ContainerRegistry",
#   ]