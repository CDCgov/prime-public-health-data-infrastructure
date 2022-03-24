# Devops functions

data "archive_file" "devops_function_app" {
  type        = "zip"
  source_dir  = "../../../../../src/FunctionApps/DevOps"
  output_path = "devops-function-app.zip"
}

locals {
  publish_devops_command = <<EOF
      az functionapp deployment source config-zip --resource-group ${var.resource_group_name} \
      --name ${azurerm_function_app.pdi_infrastructure.name} --src ${data.archive_file.devops_function_app.output_path} \
      --build-remote false
    EOF
}

resource "null_resource" "devops_function_app_publish" {
  provisioner "local-exec" {
    command = local.publish_devops_command
  }
  depends_on = [
    local.publish_devops_command,
    azurerm_function_app.pdi_infrastructure
  ]
  triggers = {
    input_json           = filemd5(data.archive_file.devops_function_app.output_path)
    publish_code_command = local.publish_devops_command
  }
}
