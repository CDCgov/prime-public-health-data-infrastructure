from azure.storage.blob import ContainerClient
from azure.identity import DefaultAzureCredential
import azure.functions as func
import os

def main(req: func.HttpRequest) -> func.HttpResponse:

    container = req.params.get('container')

    if container:
        creds = DefaultAzureCredential()

        storage_account=os.getenv('DataStorageAccount')
        container_service_client = ContainerClient.from_container_url(container_url=f"https://{storage_account}.blob.core.windows.net/{container}", credential=creds)
        properties = list(container_service_client.list_blobs(maxresults=50))

        return func.HttpResponse(f"{storage_account} : {properties}")
    else:
        return func.HttpResponse(
            "Please pass a container name on the query string",
            status_code=400
        )
