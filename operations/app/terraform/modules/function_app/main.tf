resource "azurerm_function_app" "function_app" {
  name                       = "${var.resource_prefix}-functionapp"
  location                   = var.location
  resource_group_name        = var.resource_group
  app_service_plan_id        = var.app_service_plan
  storage_account_name       = "${var.resource_prefix}datastorage"
  storage_account_access_key = var.primary_access_key
  https_only                 = true
  os_type                    = "linux"
  version                    = "~3"
  enable_builtin_logging     = false

  app_settings = {
     # Use the CDC DNS for everything; they have mappings for all our internal
    # resources, so if we add a new resource we'll have to contact them (see
    # prime-router/docs/dns.md)
    "WEBSITE_DNS_SERVER" = "172.17.0.135"

    # "DOCKER_REGISTRY_SERVER_URL"      = var.container_registry_login_server
    # "DOCKER_REGISTRY_SERVER_USERNAME" = var.container_registry_admin_username
    # "DOCKER_REGISTRY_SERVER_PASSWORD" = var.container_registry_admin_password

    # With this variable set, clients can only see (and pull) signed images from the registry
    # First make signing work, then enable this
    # "DOCKER_CONTENT_TRUST" = 1

    # App Insights
    "APPINSIGHTS_INSTRUMENTATIONKEY"                  = var.ai_instrumentation_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING"           = var.ai_connection_string
    "ApplicationInsightsAgent_EXTENSION_VERSION"      = "~3"
    "DiagnosticServices_EXTENSION_VERSION"            = "~3"
    "InstrumentationEngine_EXTENSION_VERSION"         = "disabled"
    "SnapshotDebugger_EXTENSION_VERSION"              = "disabled"
    "XDT_MicrosoftApplicationInsights_BaseExtensions" = "disabled"
    "XDT_MicrosoftApplicationInsights_Mode"           = "recommended"
    "XDT_MicrosoftApplicationInsights_PreemptSdk"     = "disabled"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE"             = false
    "FEATURE_FLAG_SETTINGS_ENABLED"                   = true 
  }

  # TODO: if we have to allow inbound HTTP we'll need to revisit these

  # site_config {
  #   ip_restriction {
  #     action                    = "Allow"
  #     name                      = "AllowVNetTraffic"
  #     priority                  = 100
  #     virtual_network_subnet_id = var.public_subnet[0]
  #   }

  #   ip_restriction {
  #     action                    = "Allow"
  #     name                      = "AllowVNetEastTraffic"
  #     priority                  = 100
  #     virtual_network_subnet_id = var.public_subnet[0]
  #   }

  #   scm_use_main_ip_restriction = true

  #   http2_enabled             = true
  #   always_on                 = false
  #   use_32_bit_worker_process = false
  #   # linux_fx_version          = "DOCKER|${var.container_registry_login_server}/${var.resource_prefix}:latest"
  # }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
  }

  lifecycle {
    ignore_changes = [
      # Allows Docker versioning via GitHub Actions
      site_config[0].linux_fx_version,
    ]
  }
}

resource "azurerm_function_app" "infrastructure_app" {
  name                       = "${var.resource_prefix}-infra-functionapp"
  location                   = var.location
  resource_group_name        = var.resource_group
  app_service_plan_id        = var.app_service_plan
  storage_account_name       = "${var.resource_prefix}datastorage"
  storage_account_access_key = var.primary_access_key
  https_only                 = true
  os_type                    = "linux"
  version                    = "~3"
  enable_builtin_logging     = false

  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY"         = var.ai_instrumentation_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING"  = var.ai_connection_string
    "FUNCTIONS_WORKER_RUNTIME"               = "python"
    "SCM_DO_BUILD_DURING_DEPLOYMENT"         = 0
    "WEBSITE_DNS_SERVER"                     = "172.17.0.135"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE"    = false
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
  }
}

resource "azurerm_key_vault_access_policy" "functionapp_app_config_access_policy" {
  key_vault_id = var.application_key_vault_id
  tenant_id    = azurerm_function_app.function_app.identity.0.tenant_id
  object_id    = azurerm_function_app.function_app.identity.0.principal_id

  secret_permissions = [
    "Get",
  ]
}

resource "azurerm_key_vault_access_policy" "infrastructure_app_config_access_policy" {
  key_vault_id = var.application_key_vault_id
  tenant_id    = azurerm_function_app.infrastructure_app.identity.0.tenant_id
  object_id    = azurerm_function_app.infrastructure_app.identity.0.principal_id

  secret_permissions = [
    "Get",
  ]
}

resource "azurerm_app_service_virtual_network_swift_connection" "function_app_vnet_integration" {
  app_service_id = azurerm_function_app.function_app.id
  subnet_id      = var.cdc_subnet_id
}

resource "azurerm_app_service_virtual_network_swift_connection" "infrastructure_app_vnet_integration" {
  app_service_id = azurerm_function_app.infrastructure_app.id
  subnet_id      = var.cdc_subnet_id
}
