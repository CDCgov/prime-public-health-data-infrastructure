# java functions

locals {
  java_function_path = "../../../../../src/FunctionApps/TestJava"
  # Deploy zip and re-add WEBSITE_RUN_FROM_PACKAGE
  java_publish_command = <<EOF
      az functionapp deployment source config-zip --resource-group ${var.resource_group_name} \
      --name ${module.pdi_function_app["java"].submodule_function_app.name} --src ${data.archive_file.java_function_app.output_path} \
      --build-remote false
      az functionapp config appsettings set --resource-group ${var.resource_group_name} \
      --name ${module.pdi_function_app["java"].submodule_function_app.name} \
      --settings WEBSITE_RUN_FROM_PACKAGE="1" --query '[].[name]'
    EOF
}

data "archive_file" "java_function_app" {
  type        = "zip"
  source_dir  = local.java_function_path
  output_path = "function-app-java.zip"

  excludes = [
    ".venv",
    ".vscode",
    "local.settings.json",
    "getting_started.md",
    "README.md",
    ".gitignore"
  ]
}

resource "null_resource" "java_function_app_publish" {
  provisioner "local-exec" {
    command = local.java_publish_command
  }
  depends_on = [
    local.java_publish_command,
    module.pdi_function_app["java"].submodule_function_app
  ]
  triggers = {
    input_json           = filemd5(data.archive_file.java_function_app.output_path)
    publish_code_command = local.java_publish_command
  }
}
