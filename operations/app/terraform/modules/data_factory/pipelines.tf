resource "azurerm_data_factory_pipeline" "transfer_files" {
  name                = "transfer-files"
  resource_group_name = var.resource_group_name
  data_factory_id     = azurerm_data_factory.pdi.id
  annotations         = []
  concurrency         = 1
  parameters          = {}

  depends_on = [
    azurerm_data_factory_dataset_binary.vdh,
    azurerm_data_factory_linked_service_azure_blob_storage.pdi_datasa
  ]

  variables = {
    "sink_base_path"   = "VIIS"
    "source_base_path" = "/"
  }

  activities_json = jsonencode(
    [
      {
        dependsOn = [
          {
            activity = "Set Source Base Path"
            dependencyConditions = [
              "Succeeded",
            ]
          },
          {
            activity = "Set Sink Base Path"
            dependencyConditions = [
              "Succeeded",
            ]
          },
        ]
        name = "Get Metadata1"
        policy = {
          retry                  = 0
          retryIntervalInSeconds = 30
          secureInput            = false
          secureOutput           = false
          timeout                = "7.00:00:00"
        }
        type = "GetMetadata"
        typeProperties = {
          dataset = {
            parameters = {
              base_path = {
                type  = "Expression"
                value = "@variables('source_base_path')"
              }
              file_name = "*"
            }
            referenceName = "SFTPBinarySource"
            type          = "DatasetReference"
          }
          fieldList = [
            "childItems",
          ]
          formatSettings = {
            compressionProperties = null
            type                  = "BinaryReadSettings"
          }
          storeSettings = {
            disableChunking          = false
            enablePartitionDiscovery = false
            type                     = "SftpReadSettings"
            recursive                = true
          }
        }
        userProperties = []
      },
      {
        dependsOn = [
          {
            activity = "Get Metadata1"
            dependencyConditions = [
              "Succeeded",
            ]
          },
        ]
        name = "ForEach1"
        type = "ForEach"
        typeProperties = {
          activities = [
            {
              dependsOn = []
              inputs = [
                {
                  parameters = {
                    base_path = {
                      type  = "Expression"
                      value = "@variables('source_base_path')"
                    }
                    file_name = {
                      type  = "Expression"
                      value = "@item().name"
                    }
                  }
                  referenceName = "SFTPBinarySource"
                  type          = "DatasetReference"
                },
              ]
              name = "Copy data1"
              outputs = [
                {
                  parameters = {
                    base_path = {
                      type  = "Expression"
                      value = "raw/@{variables('sink_base_path')}"
                    }
                    file_name = "@item().name"
                  }
                  referenceName = "SFTPBinarySink"
                  type          = "DatasetReference"
                },
              ]
              policy = {
                retry                  = 0
                retryIntervalInSeconds = 30
                secureInput            = false
                secureOutput           = false
                timeout                = "7.00:00:00"
              }
              type = "Copy"
              typeProperties = {
                enableStaging = false
                sink = {
                  storeSettings = {
                    type = "AzureBlobStorageWriteSettings"
                  }
                  type = "BinarySink"
                }
                source = {
                  formatSettings = {
                    compressionProperties = null
                    type                  = "BinaryReadSettings"
                  }
                  storeSettings = {
                    disableChunking = false
                    recursive       = true
                    type            = "SftpReadSettings"
                  }
                  type = "BinarySource"
                }
              }
              userProperties = [
                {
                  name  = "Source"
                  value = "@{variables('source_base_path')}/@{item().name}"
                },
                {
                  name  = "Destination"
                  value = "bronze/@{concat('raw/', variables('sink_base_path'))}/@{item().name}"
                },
              ]
            },
            {
              dependsOn = [
                {
                  activity = "Copy data1"
                  dependencyConditions = [
                    "Succeeded",
                  ]
                },
              ]
              linkedServiceName = {
                referenceName = "AzureFunction1"
                type          = "LinkedServiceReference"
              }
              name = "Azure Function1"
              policy = {
                retry                  = 0
                retryIntervalInSeconds = 30
                secureInput            = false
                secureOutput           = false
                timeout                = "7.00:00:00"
              }
              type = "AzureFunctionActivity"
              typeProperties = {
                body = {
                  type = "Expression"
                  value = jsonencode(
                    {
                      input  = "raw/@{variables('sink_base_path')}/@{item().name}"
                      output = "decrypted/@{variables('sink_base_path')}"
                    }
                  )
                }
                functionName = "DecryptFunction"
                headers      = {}
                method       = "POST"
              }
              userProperties = []
            },
          ]
          items = {
            type  = "Expression"
            value = "@activity('Get Metadata1').output.childItems"
          }
        }
        userProperties = []
      },
      {
        dependsOn = []
        name      = "Set Source Base Path"
        type      = "SetVariable"
        typeProperties = {
          value        = "OtherFiles"
          variableName = "source_base_path"
        }
        userProperties = []
      },
      {
        dependsOn = []
        name      = "Set Sink Base Path"
        type      = "SetVariable"
        typeProperties = {
          value        = "VIIS"
          variableName = "sink_base_path"
        }
        userProperties = []
      },
    ]
  )
}
