locals {
  data_containers = ["bronze", "silver", "gold"]
  data_ace_access = [
    { permissions = "---", id = null, type = "other", scope = "access" },
    { permissions = "---", id = null, type = "other", scope = "default" },
    { permissions = "r-x", id = null, type = "group", scope = "access" },
    { permissions = "r-x", id = null, type = "group", scope = "default" },
    { permissions = "rwx", id = null, type = "user", scope = "access" },
    { permissions = "rwx", id = null, type = "user", scope = "default" },
    { permissions = "rwx", id = null, type = "mask", scope = "access" },
    { permissions = "rwx", id = null, type = "mask", scope = "default" },
    { permissions = "rwx", id = var.adf_uuid, type = "user", scope = "access" },
    { permissions = "rwx", id = var.adf_uuid, type = "user", scope = "default" }
  ]
}

resource "azurerm_storage_data_lake_gen2_filesystem" "pdi_data" {
  for_each           = toset(local.data_containers)
  name               = each.value
  storage_account_id = azurerm_storage_account.pdi_data.id
  owner              = data.azuread_group.owners.id #data.azuread_service_principal.pitest.id
  group              = data.azuread_group.owners.id

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

locals {
  bronze_root_dirs = [
    "decrypted",
    "raw"
  ]
  bronze_sub_dirs = [
    "",
    "/eICR",
    "/ELR",
    "/OtherFiles",
    "/VEDSS",
    "/VIIS",
    "/VXU"
  ]
  # Nested loop over both lists, and flatten the result.
  bronze_mapping = distinct(flatten([
    for bronze_root_dir in local.bronze_root_dirs : [
      for bronze_sub_dir in local.bronze_sub_dirs : {
        bronze_sub_dir  = bronze_sub_dir
        bronze_root_dir = bronze_root_dir
      }
    ]
  ]))
  silver_root_dirs = []
  gold_root_dirs   = []
}

resource "azurerm_storage_data_lake_gen2_path" "pdi_data_bronze" {
  for_each           = { for entry in local.bronze_mapping : "${entry.bronze_root_dir}${entry.bronze_sub_dir}" => entry }
  path               = "${each.value.bronze_root_dir}${each.value.bronze_sub_dir}"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.pdi_data["bronze"].name
  storage_account_id = azurerm_storage_account.pdi_data.id
  resource           = "directory"
  owner              = data.azuread_group.owners.id #data.azuread_service_principal.pitest.id
  group              = data.azuread_group.owners.id

  lifecycle {
    prevent_destroy = true
  }
}

locals {
  webjob_containers = ["azure-webjobs-hosts", "azure-webjobs-secrets"]
  webjob_ace_access = [
    { permissions = "---", id = null, type = "other", scope = "access" },
    { permissions = "r-x", id = null, type = "group", scope = "access" },
    { permissions = "rwx", id = null, type = "user", scope = "access" },
    { permissions = "rwx", id = null, type = "mask", scope = "access" },
    { permissions = "rwx", id = var.function_app_id, type = "user", scope = "access" },
    { permissions = "rwx", id = var.function_infrastructure_app_id, type = "user", scope = "access" }
  ]
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
