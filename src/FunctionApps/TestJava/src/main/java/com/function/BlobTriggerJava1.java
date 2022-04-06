package com.function;

import com.microsoft.azure.functions.annotation.*;
import com.azure.identity.DefaultAzureCredential;
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.microsoft.azure.functions.*;

/*
Description:
Poorly written function to validate storage account access via Managed identity in a blob trigger.

Common commands:
mvn clean package -Denv=test
mvn azure-functions:run -Denv=test
mvn azure-functions:deploy -Denv=test

Example local.settings.json
{
  "IsEncrypted": false,
  "Values": {
    "JAVA_HOME": "/usr",
    "FUNCTIONS_WORKER_RUNTIME": "java",
    "FUNCTIONS_EXTENSION_VERSION": "~4",
    "IdConn__blobServiceUri": "https://pitestdatasa.blob.core.windows.net",
    "IdConn__queueServiceUri": "https://pitestdatasa.queue.core.windows.net",
    "AzureWebJobsStorage__accountName": "pitestdatasa"
  }
}
*/
public class BlobTriggerJava1 {
    /**
     * This function will be invoked when a new or updated blob is detected at the specified path. The blob contents are provided as input to this function.
     */
    @FunctionName("BlobTriggerJava1")
    @StorageAccount("AzureWebJobsStorage__accountName")
    public void run(
        @BlobTrigger(name = "content", path = "silver/{name}", dataType = "binary", connection = "IdConn") byte[] content,
        @BindingName("name") String name,
        final ExecutionContext context
    ) {
        context.getLogger().info("Java Blob trigger function processed a blob. Name: " + name + "\n  Size: " + content.length + " Bytes");
    }

    DefaultAzureCredential defaultCredential = new DefaultAzureCredentialBuilder().build();
}
