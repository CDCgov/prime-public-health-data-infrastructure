## Set basic variables
variable "terraform_object_id" {
  type = string
  description = "Object id of user running TF"
  default = ""
}
variable "tf_secrets_vault" {
  default = "mla-tf-secrets"
}

variable "environment"{
    default = "test"
}
variable "resource_group"{
    default = "prime-ingestion-test"
}

variable "resource_prefix"{
    default = "pitest"
}
variable "location"{
    default = "eastus"
}
variable "rsa_key_2048"{
    default = null 
}              
variable "rsa_key_4096"{
    default = null
}            
variable "https_cert_names"{
    default = []
}         

variable "aad_object_keyvault_admin"{
    default = "f94409a9-12b1-4820-a1b6-e3e0a4fa282d"
}  # Group or individual user id

##################
## App Service Plan Vars
##################

variable "app_tier" {
  default = "Standard"
}

variable "app_size" {
  default = "S1"
}

##################
## KeyVault Vars
##################

variable "use_cdc_managed_vnet" {
  default = false
}

variable "terraform_caller_ip_address" {
  default = "162.224.209.174"
}
