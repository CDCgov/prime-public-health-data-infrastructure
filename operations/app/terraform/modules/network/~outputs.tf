output "cdc_subnet_id" {
  value = data.azurerm_subnet.cdc_subnet.id
}

output "dev_private_subnet_id" {
  value = azurerm_subnet.dev_private_subnet.id
}

output "private_nsg_id" {
    value = azurerm_network_security_group.vnet_nsg_private.id
}

output "private_subnet_ids" {
  value = toset([
    data.azurerm_subnet.cdc_subnet.id,
    azurerm_subnet.dev_private_subnet.id
  ])
}

# output "public_subnet_ids" {
#   value = azurerm_subnet.public_subnet[*].id
# }
# 
# output "container_subnet_ids" {
#   value = azurerm_subnet.container_subnet[*].id
# }
# 
# output "private_subnet_ids" {
#   value = azurerm_subnet.private_subnet[*].id
# }
# 
# output "endpoint_subnet_ids" {
#   value = azurerm_subnet.endpoint_subnet[*].id
# }