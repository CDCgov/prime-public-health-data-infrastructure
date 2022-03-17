import json
import logging
import uuid
from pathlib import Path

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from DecryptFunction.settings import DecryptSettings, StorageClientSettings


# This fixture runs before all tests and can be passed as arguments to individual
# tests to enable accessing the variables they define.
# More info: https://docs.pytest.org/en/latest/fixture.html#fixtures-scope-sharing-and-autouse-autouse-fixtures  # noqa: E501
@pytest.fixture(scope="session", autouse=True)
def local_settings() -> DecryptSettings:
    """Local settings relevant for running these tests.
    Note, unlike running the function itself, we manually parse this file,
    because it is not loaded automatically by the test runner.

    Returns:
        DecryptSettings: settings object describing relevant subset of settings for this function
    """  # noqa: E501
    local_settings_path = (
        Path("DecryptFunction").parent / "tests" / "assets" / "test.settings.json"
    )
    local_json_config = json.loads(local_settings_path.read_text())
    local_settings_vals = local_json_config.get("Values")
    settings = DecryptSettings()
    settings.private_key = local_settings_vals.get("PRIVATE_KEY")
    settings.private_key_password = local_settings_vals.get("PRIVATE_KEY_PASSWORD")

    storage_client_settings = StorageClientSettings()
    storage_client_settings.connection_string = local_settings_vals.get(
        "AZURE_STORAGE_CONNECTION_STRING"
    )
    storage_client_settings.container_name = str(uuid.uuid4())

    settings.storage_client_settings = storage_client_settings
    return settings


@pytest.fixture(scope="session")
def blob_service_client(local_settings: DecryptSettings) -> BlobServiceClient:
    """Neutral, MSFT-provided service client for testing purposes.

    Args:
        local_settings (DecryptSettings): fixture (see above)

    Returns:
        BlobServiceClient: A Microsoft Azure Blob Service client
    """
    # Create a container for Azurite for the first run
    blob_service_client = BlobServiceClient.from_connection_string(
        local_settings.storage_client_settings.connection_string
    )
    return blob_service_client


@pytest.fixture(scope="session")
def container_name(
    blob_service_client: BlobServiceClient, local_settings: DecryptSettings
) -> str:
    container_name = local_settings.storage_client_settings.container_name
    blob_service_client.create_container(container_name)
    yield container_name
    try:
        blob_service_client.delete_container(container_name)
    except ResourceNotFoundError:
        logging.info("Container already deleted.")
