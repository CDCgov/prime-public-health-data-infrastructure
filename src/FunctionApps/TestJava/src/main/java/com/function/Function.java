package com.function;

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

import java.util.Locale;
import java.util.Optional;

/**
 * Azure blob storage v12 SDK quickstart
 */
import com.azure.storage.blob.*;
import com.azure.storage.blob.models.*;

/**
 * Azure Functions with HTTP Trigger.
 */
public class Function {
    @FunctionName("HttpExample")
    public HttpResponseMessage run(
            @HttpTrigger(name = "req", methods = { HttpMethod.GET,
                    HttpMethod.POST }, authLevel = AuthorizationLevel.ANONYMOUS) HttpRequestMessage<Optional<String>> request,
            final ExecutionContext context) {
        context.getLogger().info("Java HTTP trigger processed a request.");

        final String query = request.getQueryParameters().get("name");
        final String name = request.getBody().orElse(query);

        final String endpoint = "https://pidevfunctionapps.blob.core.windows.net";
        final String container = "azure-webjobs-hosts";
        DefaultAzureCredential defaultCredential = new DefaultAzureCredentialBuilder().build();
        final BlobContainerClientBuilder clientBuilder = new BlobContainerClientBuilder()
                .endpoint(endpoint)
                .containerName(container)
                .credential(defaultCredential);
        BlobContainerClient client = clientBuilder.buildClient();

        ListBlobsOptions blobOptions = new ListBlobsOptions();
        final String a = blobOptions.toString();

        if (name == null) {
            return request.createResponseBuilder(HttpStatus.BAD_REQUEST)
                    .body("Please pass a name on the query string or in the request body").build();
        } else {
            return request.createResponseBuilder(HttpStatus.OK).body("Hello, " + name).build();
        }
    }
}