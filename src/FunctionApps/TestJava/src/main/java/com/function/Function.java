package com.function;

import com.azure.core.http.rest.PagedIterable;
import com.azure.identity.DefaultAzureCredential;
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.microsoft.azure.functions.ExecutionContext;
import com.microsoft.azure.functions.HttpMethod;
import com.microsoft.azure.functions.HttpRequestMessage;
import com.microsoft.azure.functions.HttpResponseMessage;
import com.microsoft.azure.functions.HttpStatus;
import com.microsoft.azure.functions.annotation.AuthorizationLevel;
import com.microsoft.azure.functions.annotation.FunctionName;
import com.microsoft.azure.functions.annotation.HttpTrigger;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import com.azure.storage.blob.*;
import com.azure.storage.blob.models.*;

/*
Description:
Poorly written function to validate storage account access via Managed identity.

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
    "DATA_STORAGE_ACCOUNT": "pitestdatasa"
  }
}
*/
public class Function {

    @FunctionName("HttpExample")
    public HttpResponseMessage run(

            @HttpTrigger(name = "req", methods = { HttpMethod.GET,
                    HttpMethod.POST }, authLevel = AuthorizationLevel.FUNCTION) HttpRequestMessage<Optional<String>> request,
            final ExecutionContext context) {

        context.getLogger().info("Java HTTP trigger processed a request.");

        final String account = System.getenv("AzureWebJobsStorage__accountName");
        final String query = request.getQueryParameters().get("container");
        final String containerName = request.getBody().orElse(query);
        final String endpoint = "https://" + account + ".blob.core.windows.net";
        final String container = containerName;

        String access;

        DefaultAzureCredential defaultCredential = new DefaultAzureCredentialBuilder().build();
        final BlobContainerClientBuilder clientBuilder = new BlobContainerClientBuilder()
                .endpoint(endpoint)
                .containerName(container)
                .credential(defaultCredential);
        BlobContainerClient client = clientBuilder.buildClient();

        try {

            PagedIterable<BlobItem> blobs = client.listBlobsByHierarchy("/");
            List target = new ArrayList<>();
            blobs.forEach(target::add);

            access = "1";
        } catch (Exception e) {

            access = "0";

        }

        return request.createResponseBuilder(HttpStatus.OK).body("{\"access\":" + access + "}").build();
    }
}