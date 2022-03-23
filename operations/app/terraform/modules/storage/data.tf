# data "azurerm_client_config" "current" {}

data "azuread_group" "owners" {
  display_name = var.data_access_group
}

data "azuread_service_principal" "pitest" {
  display_name = var.data_access_sp
}

# storage account data containers and permissions
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

# storage account data directories
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

# storage account function app containers and permissions
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