import logging
import os
import traceback

import pytest
from DecryptFunction.settings import StorageClientSettings
from DecryptFunction.storage_client import PHDIStorageClient


# Fixtures run before each test and can be passed as arguments to individual tests to enable accessing the variables they define. More info: https://docs.pytest.org/en/latest/fixture.html#fixtures-scope-sharing-and-autouse-autouse-fixtures
@pytest.fixture(scope="session", autouse=True)
def initialize_env_vars():
    # get storage account settings
    storage_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("STORAGE_CONTAINER")
    return storage_connection_string, container_name


@pytest.fixture(scope="session")
def storage_client(initialize_env_vars):
    storage_connection_string, _ = initialize_env_vars
    settings = StorageClientSettings()
    settings.connection_string = storage_connection_string
    storage_client = PHDIStorageClient(settings)
    yield storage_client


def test_create_container(storage_client):
    result = storage_client.create_container()
    assert result == True


def test_list_blobs(storage_client):
    storage_connection_string, container_name = initialize_env_vars
    result = storage_client.list_blobs_in_container(container_name)
    assert result == []
