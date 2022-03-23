resource "azurerm_storage_data_lake_gen2_filesystem" "pdi_data" {
  for_each           = toset(local.data_containers)
  name               = each.value
  storage_account_id = azurerm_storage_account.pdi_data.id
  owner              = data.azuread_group.owners.id
  group              = data.azuread_group.owners.id
  properties         = {}

  dynamic "ace" {
    for_each = local.data_ace_access
    content {
      id          = ace.value.id
      permissions = ace.value.permissions
      scope       = ace.value.scope
      type        = ace.value.type
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_storage_data_lake_gen2_path" "pdi_data_bronze" {
  for_each           = { for entry in local.bronze_mapping : "${entry.bronze_root_dir}${entry.bronze_sub_dir}" => entry }
  path               = "${each.value.bronze_root_dir}${each.value.bronze_sub_dir}"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.pdi_data["bronze"].name
  storage_account_id = azurerm_storage_account.pdi_data.id
  resource           = "directory"
  owner              = data.azuread_group.owners.id
  group              = data.azuread_group.owners.id

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_storage_data_lake_gen2_filesystem" "webjobs" {
  for_each           = toset(local.webjob_containers)
  name               = each.value
  storage_account_id = azurerm_storage_account.pdi_data.id

  dynamic "ace" {
    for_each = local.webjob_ace_access
    content {
      id          = ace.value.id
      permissions = ace.value.permissions
      scope       = ace.value.scope
      type        = ace.value.type
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}
