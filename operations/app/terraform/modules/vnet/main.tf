resource "azurerm_virtual_network" "east" {
  name                = "${var.resource_prefix}-East-vnet"
  location            = "East US"
  resource_group_name = var.resource_group
  address_space       = ["10.1.0.0/16"]
  dns_servers         = ["10.1.0.4", "10.1.0.5"]

  tags = {
      environment = var.environment
  }
}