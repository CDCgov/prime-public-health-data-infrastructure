resource "azurerm_application_insights" "app_insights" {
  name                = "${var.resource_prefix}-appinsights"
  location            = var.location
  resource_group_name = var.resource_group
  application_type    = "web"

  tags = {
    environment = var.environment
  }
}