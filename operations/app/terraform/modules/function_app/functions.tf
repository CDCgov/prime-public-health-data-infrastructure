# Devops functions

locals {
  devops_function_path   = "../../../../../src/FunctionApps/DevOps"
  devops_publish_command = <<EOF
      az functionapp deployment source config-zip --resource-group ${var.resource_group_name} \
      --name ${azurerm_function_app.pdi_infrastructure.name} --src ${data.archive_file.devops_function_app.output_path} \
      --build-remote false
    EOF
}

data "archive_file" "devops_function_app" {
  type        = "zip"
  source_dir  = local.devops_function_path
  output_path = "devops-function-app.zip"

  excludes = [
    ".venv",
    ".vscode",
    "local.settings.json"
  ]
}

resource "null_resource" "devops_function_app_publish" {
  provisioner "local-exec" {
    command = local.devops_publish_command
  }
  depends_on = [
    local.devops_publish_command,
    azurerm_function_app.pdi_infrastructure
  ]
  triggers = {
    input_json           = filemd5(data.archive_file.devops_function_app.output_path)
    publish_code_command = local.devops_publish_command
  }
}
