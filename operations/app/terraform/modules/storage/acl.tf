locals {
  containers = ["bronze", "silver", "gold"]
  ace_access = [
    { permissions = "---", id = null, type = "other", scope = "access" },
    { permissions = "---", id = null, type = "other", scope = "default" },
    { permissions = "---", id = null, type = "group", scope = "access" },
    { permissions = "---", id = null, type = "group", scope = "default" },
    { permissions = "---", id = null, type = "user", scope = "access" },
    { permissions = "---", id = null, type = "user", scope = "default" },
    { permissions = "rwx", id = null, type = "mask", scope = "access" },
    { permissions = "rwx", id = null, type = "mask", scope = "default" },
    { permissions = "rwx", id = data.azuread_group.owners.id, type = "group", scope = "access" },
    { permissions = "rwx", id = data.azuread_group.owners.id, type = "group", scope = "default" },
    { permissions = "rwx", id = data.azuread_service_principal.pitest.id, type = "user", scope = "access" },
    { permissions = "rwx", id = data.azuread_service_principal.pitest.id, type = "user", scope = "default" }
  ]
}

resource "azurerm_storage_data_lake_gen2_path" "pdi_data_temp" {
  for_each           = toset(local.containers)
  path               = "temp"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.pdi_data[each.value].name
  storage_account_id = azurerm_storage_account.pdi_data.id
  resource           = "directory"
}

resource "azurerm_storage_data_lake_gen2_filesystem" "pdi_data" {
  for_each           = toset(local.containers)
  name               = each.value
  storage_account_id = azurerm_storage_account.pdi_data.id

  dynamic "ace" {
    for_each = local.ace_access
    content {
      id          = ace.value.id
      permissions = ace.value.permissions
      scope       = ace.value.scope
      type        = ace.value.type
    }
  }
}