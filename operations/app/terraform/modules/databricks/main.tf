resource "azurerm_databricks_workspace" "pdi" {
  name                          = "${var.resource_prefix}-databricks"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  sku                           = "standard"
  public_network_access_enabled = true

  custom_parameters {
    nat_gateway_name         = "${var.resource_prefix}-nat-gateway"
    no_public_ip             = false
    public_ip_name           = "${var.resource_prefix}-nat-gw-public-ip"
    storage_account_name     = "${var.resource_prefix}dbstorage"
    storage_account_sku_name = "Standard_GRS"
    vnet_address_prefix      = "10.139"
  }

  lifecycle {
    ignore_changes = [
      public_network_access_enabled,
      name,
      tags,
      custom_parameters
    ]
  }

  tags = {
    environment = var.environment
    managed-by  = "terraform"
  }
}

resource "azurerm_databricks_workspace" "databricks_VNET" {
  name                                  = "${var.resource_prefix}-databricks-VNET"
  location                              = var.location
  resource_group_name                   = var.resource_group_name
  sku                                   = "standard"
  public_network_access_enabled         = false
  network_security_group_rules_required = AllRules

  custom_parameters {
    virtual_network_id                                   = var.databricks_managed_vnet_id
    public_subnet_name                                   = "databricks-public"
    public_subnet_network_security_group_association_id  = var.databricks_public_subnet_network_security_group_association_id
    private_subnet_name                                  = "databricks-private"
    private_subnet_network_security_group_association_id = var.databricks_private_subnet_network_security_group_association_id
  }

  tags = {
    environment = var.environment
    managed-by  = "terraform"
  }
}
