##########
## 01-network (including vnets)
##########

module "network" {
  source          = "../../modules/network"
  cdc_vnet_name   = var.cdc_vnet_name
  cdc_subnet_name = var.cdc_subnet_name
  environment     = var.environment
  location        = var.location
  resource_group  = var.resource_group
  resource_prefix = var.resource_prefix
}

# ##########
# ## 02-storage
# ##########

module "key_vault" {
  source                      = "../../modules/key_vault"
  environment                 = var.environment
  resource_group              = var.resource_group
  resource_prefix             = var.resource_prefix
  location                    = var.location
  aad_object_keyvault_admin   = var.aad_object_keyvault_admin
  terraform_caller_ip_address = var.terraform_caller_ip_address
  use_cdc_managed_vnet        = var.use_cdc_managed_vnet
  private_subnet_ids          = module.network.private_subnet_ids
  cyberark_ip_ingress         = ""
  terraform_object_id         = var.terraform_object_id
}

module "storage" {
  source                      = "../../modules/storage"
  environment                 = var.environment
  resource_group              = var.resource_group
  resource_prefix             = var.resource_prefix
  location                    = var.location
  rsa_key_4096                = var.rsa_key_4096
  terraform_caller_ip_address = var.terraform_caller_ip_address
  use_cdc_managed_vnet        = var.use_cdc_managed_vnet
  private_subnet_ids          = module.network.private_subnet_ids
  application_key_vault_id    = module.key_vault.application_key_vault_id
}


# # ##########
# # ## 03-App
# # ##########

module "app_service_plan" {
  source          = "../../modules/app_service_plan"
  environment     = var.environment
  resource_group  = var.resource_group
  resource_prefix = var.resource_prefix
  location        = var.location
  app_tier        = var.app_tier
  app_size        = var.app_size
}

# module "application_insights" {
#   source          = "../../modules/application_insights"
#   environment     = var.environment
#   resource_group  = var.resource_group
#   resource_prefix = var.resource_prefix
#   location        = var.location
#   service_plan_id = module.app_service_plan.service_plan_id
# }

# module "function_app" {
#   source                      = "../../modules/function_app"
#   environment                 = var.environment
#   resource_group              = var.resource_group
#   resource_prefix             = var.resource_prefix
#   location                    = var.location
#   ai_instrumentation_key      = module.application_insights.instrumentation_key
#   ai_connection_string        = module.application_insights.connection_string
#   terraform_caller_ip_address = var.terraform_caller_ip_address
#   use_cdc_managed_vnet        = var.use_cdc_managed_vnet
#   primary_access_key          = module.storage.sa_primary_access_key
#   primary_connection_string   = module.storage.sa_primary_connection_string
#   primary_name                = module.storage.sa_primary_name
#   app_service_plan            = module.app_service_plan.service_plan_id
#   public_subnet               = module.network.public_subnet_ids
#   application_key_vault_id    = module.key_vault.application_key_vault_id
# }