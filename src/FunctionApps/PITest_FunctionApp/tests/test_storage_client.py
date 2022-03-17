import logging
import uuid

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from DecryptFunction.settings import DecryptSettings, StorageClientSettings
from DecryptFunction.storage_client import PHDIStorageClient
from pytest import TempPathFactory


@pytest.fixture(scope="session")
def storage_client(local_settings: DecryptSettings) -> PHDIStorageClient:
    """Storage Client

    Args:
        local_settings (DecryptSettings): (Fixture) Pre-configured Decrypt Settings

    Returns:
        PHDIStorageClient: a pre-configured PHDI Storage Client for use with tests
    """
    storage_client = PHDIStorageClient(local_settings.storage_client_settings)
    yield storage_client


@pytest.fixture(scope="function")
def method_test_file(
    blob_service_client: BlobServiceClient,
    tmp_path_factory: TempPathFactory,
    method_container: str,
) -> str:
    """Create a temporary file for just this method. (Removes after method is complete)

    Args:
        blob_service_client (BlobServiceClient):
            (Fixture) Azure Blob Service Client for confirmation purposes
        tmp_path_factory (TempPathFactory):
            (Fixture) Temporary file path factory for creating a path for this test run
        method_container (str):
            (Fixture) A temporary container for just this method

    Returns:
        str: The path to the just-created temporary file
    """
    file_name = "hello.txt"
    file_path = tmp_path_factory.getbasetemp() / file_name
    with open(file_path, "w") as f:
        f.write("Hello World!")

    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(
        container=method_container, blob=str(file_name)
    )

    logging.info(f"Uploading to Azure Storage as blob: {file_path}")

    # Upload the created file
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data)
    yield file_name
    try:
        blob_client.delete_blob()
    except ResourceNotFoundError:
        logging.info("Blob already deleted.")


@pytest.fixture(scope="function")
def method_container(blob_service_client: BlobServiceClient) -> str:
    """Create a temporary container for just this method. (Removes after method is complete)

    Args:
        blob_service_client (BlobServiceClient): (Fixture) An azure Blob Service Client

    Returns:
        str: The name of the just-created container

    """
    container_name = str(uuid.uuid4())
    blob_service_client.create_container(container_name)
    yield container_name
    try:
        blob_service_client.delete_container(container_name)
    except ResourceNotFoundError:
        logging.info("Container already deleted.")


def test_create_container(
    storage_client: PHDIStorageClient, blob_service_client: BlobServiceClient
) -> None:
    """Create Container

    Args:
        storage_client (PHDIStorageClient):
            (Fixture) Pre-configured PHDI Storage Client
        blob_service_client (BlobServiceClient):
            (Fixture) Azure Blob Service Client for confirmation purposes
    """
    test_name = str(uuid.uuid4())
    result = storage_client.create_container(test_name)
    assert result
    blob_service_client.delete_container(test_name)


def test_list_blobs(
    storage_client: PHDIStorageClient, method_container: str, method_test_file: str
):
    """List blobs

    Args:
        storage_client (PHDIStorageClient):
            (Fixture) Pre-configured PHDI Storage Client
        method_container (str):
            (Fixture) A temporary container for just this method
        method_test_file (str):
            (Fixture) A temporary test file in this container for just this method
    """
    result = [r.name for r in storage_client.list_blobs_in_container(method_container)]
    assert result == [method_test_file]


def test_read_blob(method_container: str, method_test_file: str):
    """Read a blob from Azure Storage.

    Args:
        method_container (str):
            (Fixture) A temporary container for just this method
        method_test_file (str):
            (Fixture) A temporary test file in this container for just this method
    """
    settings = StorageClientSettings()
    settings.connection_string = "AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;DefaultEndpointsProtocol=http;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"  # noqa
    settings.container_name = method_container
    storage_client = PHDIStorageClient(settings)
    result = storage_client.read_blob(method_test_file)
    assert result == b"Hello World!"
