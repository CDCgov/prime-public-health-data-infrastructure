import os
from dataclasses import dataclass


@dataclass
class StorageClientSettings:
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
