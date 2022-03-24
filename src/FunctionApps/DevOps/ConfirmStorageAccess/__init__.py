from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import azure.functions as func
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:

    creds = DefaultAzureCredential()

    storage_account=os.getenv('AzureWebJobsStorage__accountName')
    print (f"Storage account name: {storage_account}")
    blob_service_client = BlobServiceClient(account_url=f"https://{storage_account}.blob.core.windows.net/", credential=creds)

    containers = list(blob_service_client.list_containers())

    return func.HttpResponse(f"{storage_account} : {containers}")
