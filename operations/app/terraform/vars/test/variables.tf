## Set basic variables
variable "terraform_object_id" {
  type = string
  description = "Object id of user running TF"
  # NOTE: set to object ID of CT-DMZ-PRIME-INGESTION-TST-AZ-Contributor
  default = "9ff42a69-beb8-4b4a-9406-e7fbcbf847ee"
}

variable "tf_secrets_vault" {
  default = "pitest-tf-secrets"
}

variable "cdc_vnet_name" {
  default = "prime-ingestion-test-VNET"
}

variable "cdc_subnet_name" {
  default = "Default"
}

variable "environment" {
  default = "test"
}
variable "resource_group" {
  default = "prime-ingestion-test"
}

variable "resource_prefix" {
  default = "pitest"
}
variable "location" {
  default = "eastus"
}
variable "rsa_key_2048" {
  default = null 
}              
variable "rsa_key_4096" {
  default = null
}            
variable "https_cert_names" {
  default = []
}         

variable "aad_object_keyvault_admin" {
  # NOTE: set to object ID of CT-DMZ-PRIME-INGESTION-TST-AZ-Contributor
  default = "9ff42a69-beb8-4b4a-9406-e7fbcbf847ee"
}  # Group or individual user id

##################
## App Service Plan Vars
##################

variable "app_tier" {
  default = "PremiumV2"
}

variable "app_size" {
  default = "P3v2"
}

##################
## KeyVault Vars
##################

variable "use_cdc_managed_vnet" {
  default = true
}

variable "terraform_caller_ip_address" {
  default = "162.224.209.174"
}
