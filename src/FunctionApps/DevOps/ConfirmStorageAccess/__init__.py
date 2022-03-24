from azure.storage.blob import BlobServiceClient
from azure.identity import ManagedIdentityCredential
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:

    creds = ManagedIdentityCredential ()

    blob_service_client = BlobServiceClient(account_url="https://pidevdatasa.blob.core.windows.net/", credential=creds)
    containers = blob_service_client.list_containers()

    return func.HttpResponse(f"Containers: {containers}")
