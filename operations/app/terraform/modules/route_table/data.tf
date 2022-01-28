data "azurerm_route_table" "cdc_managed" {
  name                = "prime-ingestion-test-RT"
  resource_group_name = var.resource_group
}
