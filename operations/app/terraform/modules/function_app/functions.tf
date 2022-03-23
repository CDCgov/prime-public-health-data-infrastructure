data "archive_file" "file_function_app" {
  type        = "zip"
  source_dir  = "../../../../../src/FunctionApps/PITest_FunctionApp"
  output_path = "function-app.zip"
}

resource "azurerm_storage_blob" "functions" {
  name = "${filesha256(data.archive_file.file_function_app.output_path)}.zip"
  storage_account_name = var.sa_data_name
  storage_container_name = "functions"
  type = "Block"
  source = data.archive_file.file_function_app.output_path

  depends_on = [
    data.archive_file.file_function_app
  ]
}
