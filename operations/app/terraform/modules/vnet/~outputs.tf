output "ids" {
  value = [azurerm_virtual_network.east.id]
}

output "names" {
    value = [azurerm_virtual_network.east.name]
}

output "vnet_address_spaces" {
  description = "The address space of the newly created vNet"
  value       = [azurerm_virtual_network.east.address_space]
}

output "vnets" {
  value = [azurerm_virtual_network.east]
}