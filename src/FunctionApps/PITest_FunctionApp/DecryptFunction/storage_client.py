import logging
import uuid
from io import BytesIO
from typing import List, Optional

from azure.storage.blob import BlobServiceClient

from DecryptFunction.settings import StorageClientSettings


logger = logging.getLogger(__name__)


class PHDIStorageClient:
    def __init__(self, settings: StorageClientSettings):
        self._settings = settings
        self._blob_service_client = self._setup_blob_client()

    def _setup_blob_client(self) -> BlobServiceClient:
        logging.info("Setting up blob client")
        if self._settings.connection_string is None:
            raise TypeError
        blob_service_client = BlobServiceClient.from_connection_string(
            self._settings.connection_string
        )
        return blob_service_client

    def read_blob(self, blob_path: str) -> Optional[BytesIO]:
        # Download the blob
        logging.info(f"Fetching blob {blob_path}")
        blob_client = self._blob_service_client.get_blob_client(
            container=self._settings.container_name, blob=blob_path
        )

        stream_downloader = blob_client.download_blob()
        data = stream_downloader.readall()
        logging.info("Download to stream complete")
        return data

    def create_container(self, name=None) -> bool:
        if not name:
            name = str(uuid.uuid4())
        # Create the container
        logging.info(f"Creating container {name}")
        self._blob_service_client.create_container(name)
        return True

    def list_blobs_in_container(self, container_name: str) -> List[str]:
        container_client = self._blob_service_client.get_container_client(
            container_name
        )
        # List the blobs in the container
        return container_client.list_blobs()

    def upload_data_to_blob(self, data: BytesIO, blob_path: str) -> bool:
        container_name = self._settings.container_name
        # Upload a blob to the container
        logging.info(
            f"""Uploading passed-in file object to container
            {container_name} at {blob_path}"""
        )
        blob_client = self._blob_service_client.get_blob_client(
            container=container_name, blob=blob_path
        )
        blob_client.upload_blob(data)
        return True
