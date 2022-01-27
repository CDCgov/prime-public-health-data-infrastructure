resource "azurerm_log_analytics_workspace" "pdi" {
  name                = "pitest-law"
  location            = var.location
  resource_group_name = var.resource_group
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

locals {
  default = {
    "function_app" = {
      id   = "${var.function_app_id}"
      name = "function_app"
    },
    "function_infrastructure_app" = {
      id   = "${var.function_infrastructure_app_id}"
      name = "function_infrastructure_app"
    }
  }
}

resource "azurerm_monitor_diagnostic_setting" "function_app_diag" {
  for_each                   = local.default
  name                       = "${each.value.name}_diag"
  target_resource_id         = each.value.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.pdi.id

  log {
    category = "FunctionAppLogs"
    enabled  = true

    retention_policy {
      enabled = true
      days    = 60
    }
  }

  metric {
    category = "AllMetrics"

    retention_policy {
      enabled = true
      days    = 60
    }
  }
}

resource "azurerm_monitor_diagnostic_setting" "app_service_diag" {
  name                       = "app_service_diag"
  target_resource_id         = var.app_service_plan_id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.pdi.id

  metric {
    category = "AllMetrics"

    retention_policy {
      enabled = true
      days    = 60
    }
  }
}

resource "azurerm_monitor_diagnostic_setting" "vnet_diag" {
  name                       = "vnet_diag"
  target_resource_id         = var.cdc_managed_vnet_id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.pdi.id

  log {
    category = "VMProtectionAlerts"
    enabled  = true

    retention_policy {
      enabled = true
      days    = 60
    }
  }

  metric {
    category = "AllMetrics"

    retention_policy {
      enabled = true
      days    = 60
    }
  }
}
