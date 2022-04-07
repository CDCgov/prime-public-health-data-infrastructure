# Function Authentication

## Type

Managed identity authentication is required to connect to the PHI data storage accounts, as [account key/SAS auth has been disabled](data-access.md).

## Trigger Auth Solutions

### Http

Use DefaultAzureCredential:
 * [Java](https://docs.microsoft.com/en-us/java/api/overview/azure/identity-readme?view=azure-java-stable#authenticating-with-defaultazurecredential)
 * [Python](https://docs.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python#authenticate-with-defaultazurecredential)

### Blob

Requires [Azure function core tools v4](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local#v2), [extension version 5.0.0 or later (Bundle v3.x)](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference?tabs=blob#configure-an-identity-based-connection) and the following app config/`local.settings.json` [settings](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference?tabs=blob#common-properties-for-identity-based-connections):

  *
    ```json
    "<CONNECTION_NAME_PREFIX>__blobServiceUri": "<blobServiceUri>"
    "<CONNECTION_NAME_PREFIX>__queueServiceUri": "<queueServiceUri>"
    "<CONNECTION_NAME_PREFIX>__credential": "managedidentity"
    ```
[Local development](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference?tabs=blob#local-development-with-identity-based-connections) requires the following changes from above in `local.settings.json`:

  1. Remove
      ```json
      "<CONNECTION_NAME_PREFIX>__credential": "managedidentity"
      ```

  2. Add
      ```json
      "<CONNECTION_NAME_PREFIX>__tenantId": "<tenantId>"
      "<CONNECTION_NAME_PREFIX>__clientId": "<clientId>"
      "<CONNECTION_NAME_PREFIX>__clientSecret": "<clientSecret>"
      ```