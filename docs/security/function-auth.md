# Function Authentication

## Auth Restrictions

Managed identity authentication is required to connect to the PHI data storage accounts, as [account key/SAS auth has been disabled](data-access.md).

## Function Provisioning

It is important to make sure all the necessary files to test authentication locally are provisioned.

While in VSCode, install the Azure Functions extension and follow either to help lay the appropriate foundation:
 1. Follow the [function provisioning instructions](https://github.com/microsoft/vscode-azurefunctions#create-your-first-serverless-app). 
 2. Enter `CTRL+SHIFT+P` and select `Azure Functions: Create Function...`.
    * The first run will create a new project with an HTTP trigger function. **Run again** to create another function with a different trigger (e.g. Blob trigger).

## Auth Solutions

### Http Trigger

Use DefaultAzureCredential:
 * [Java](https://docs.microsoft.com/en-us/java/api/overview/azure/identity-readme?view=azure-java-stable#authenticating-with-defaultazurecredential)
 * [Python](https://docs.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python#authenticate-with-defaultazurecredential)

### Blob Trigger

Requires [Azure function core tools v4](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local#v2), [extension version 5.0.0 or later (Bundle v3.x)](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference?tabs=blob#configure-an-identity-based-connection) and the following app config/`local.settings.json` [settings](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference?tabs=blob#common-properties-for-identity-based-connections):

  *
    ```json
    "<CONNECTION_NAME_PREFIX>__blobServiceUri": "<blobServiceUri>"
    "<CONNECTION_NAME_PREFIX>__queueServiceUri": "<queueServiceUri>"
    ```
[Local development](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference?tabs=blob#local-development-with-identity-based-connections) requires RBAC roles [Storage Account Contributor, Storage Blob Data Owner, and Storage Queue Data Contributor](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference?tabs=blob#connecting-to-host-storage-with-an-identity-preview) (queue is used for [Blob receipts](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-blob-trigger?tabs=in-process%2Cextensionv5&pivots=programming-language-java#blob-receipts)), as well as adding the following changes to above in `local.settings.json`:

  *
      ```json
      "<CONNECTION_NAME_PREFIX>__tenantId": "<tenantId>"
      "<CONNECTION_NAME_PREFIX>__clientId": "<clientId>"
      "<CONNECTION_NAME_PREFIX>__clientSecret": "<clientSecret>"
      ```