# java functions

locals {
  java_function_path = "../../../../../src/FunctionApps/TestJava"
}

locals {
  java_publish_command = <<EOF
      mvn clean package -Denv=${var.environment} -f ${local.java_function_path}/pom.xml
      mvn azure-functions:deploy -Denv=${var.environment} -f ${local.java_function_path}/pom.xml
      az functionapp config appsettings set --resource-group ${var.resource_group_name} \
      --name ${module.pdi_function_app["java"].submodule_function_app.name} \
      --settings WEBSITE_RUN_FROM_PACKAGE="1" --query '[].[name]'
    EOF
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
    publish_code_command = local.java_publish_command
  }
}
