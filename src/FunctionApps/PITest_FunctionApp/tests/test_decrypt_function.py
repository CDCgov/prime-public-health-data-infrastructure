import json
from pathlib import Path

import azure.functions as func
import pgpy.errors
import pytest
from azure.storage.blob import BlobServiceClient
from DecryptFunction import decrypt
from DecryptFunction.settings import DecryptSettings

"""
Note: These tests require a running Azurite container to work locally. 
See instructions [here](https://docs.microsoft.com/en-us/azure/storage/blobs/use-azurite-to-run-automated-tests)

Confirmed that these run by running `Azurite:Start` in VSCode

"""


@pytest.fixture(scope="session")
def encrypted_file(blob_service_client: BlobServiceClient, container_name: str) -> str:
    """Upload a file to the blob storage container using a neutral Microsoft-provided lib.

    Args:
        blob_service_client (BlobServiceClient): Azure blob storage client, fixture

    Returns:
        str: file name of local file
    """
    file_name = "encrypted.txt"
    test_file_path = Path("DecryptFunction").parent / "tests" / "assets" / file_name

    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=file_name
        )
        blob_client.upload_blob(data=test_file_path.read_bytes())
    except:
        pytest.skip("Could not upload test file to blob storage")
    yield file_name
    blob_client.delete_blob()


def get_blob_contents(
    file_path: str, blob_service_client: BlobServiceClient, container_name: str
) -> bytes:
    """Helper method to get blob contents from blob storage

    Args:
        file_path (str): path to file in blob storage
        blob_service_client (BlobServiceClient): (Fixture) Azure blob storage client
        container_name (str): (Fixture) Name of blob storage container

    Returns:
        bytes: contents of blob
    """
    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=file_path
    )
    stream_downloader = blob_client.download_blob()
    blob_data = stream_downloader.readall()
    return blob_data


def test_decrypt_message_success(local_settings: DecryptSettings):
    """Tests decrypting a message using a specified private key in base64 encoded format.

    Args:
        local_settings (DecryptSettings): passed automatically via above fixture
    """
    test_file_path = (
        Path("DecryptFunction").parent / "tests" / "assets" / "encrypted.txt"
    )
    blob_data = test_file_path.read_bytes()
    input_stream = func.blob.InputStream(data=blob_data, name="input test")
    result = decrypt.decrypt_message(
        input_stream.read(),
        local_settings.private_key,
        local_settings.private_key_password,
    )
    assert result == b"TESTING EICR ENCRYPTION"


def test_decrypt_message_failure_wrong_receiver(local_settings: DecryptSettings):
    """Attempt to decrypt a message that was not intended for us.

    Args:
        local_settings (DecryptSettings): passed automatically via above fixture
    """
    test_file_path = (
        Path("DecryptFunction").parent
        / "tests"
        / "assets"
        / "encrypted_to_someone_else.txt"
    )
    blob_data = test_file_path.read_bytes()
    input_stream = func.blob.InputStream(data=blob_data, name="input test")

    with pytest.raises(pgpy.errors.PGPError) as exc_info:
        decrypt.decrypt_message(
            input_stream.read(),
            local_settings.private_key,
            local_settings.private_key_password,
        )

    assert "Cannot decrypt the provided message with this key" in str(exc_info.value)


def test_trigger_success(
    local_settings: DecryptSettings,
    encrypted_file: str,
    blob_service_client: BlobServiceClient,
    container_name: str,
):
    """Test Trigger success

    Args:
        local_settings (_type_): (Fixture) pre-configured test settings
        encrypted_file (str): (Fixture) path to local encrypted file
        blob_service_client (BlobServiceClient): (Fixture) Microsoft azure blob storage client
        container_name (str): (Fixture) Name of blob storage container
    """
    output_base_path = "decrypted"
    output_path = Path(output_base_path) / encrypted_file

    body = {"input": encrypted_file, "output": output_base_path}
    req_success = func.HttpRequest(
        method="POST",
        body=json.dumps(body),
        url="/",
    )
    resp = decrypt.main_with_overload(req_success, local_settings)
    assert resp.status_code == 200

    blob_contents = get_blob_contents(
        str(output_path), blob_service_client, container_name
    )
    assert blob_contents == b"TESTING EICR ENCRYPTION"


def test_trigger_missing_body(local_settings: DecryptSettings):
    """Test trigger with missing body

    Args:
        local_settings (DecryptSettings): passed automatically via above fixture
    """
    req_success = func.HttpRequest(
        method="POST",
        body="",
        headers={"Content-Type": "application/octet-stream"},
        url="/",
    )
    resp = decrypt.main_with_overload(req_success, local_settings)
    assert (
        resp.status_code == 400
        and b"Please pass the encrypted message in the body of the request"
        in resp.get_body()
    )


def test_malformed_json(local_settings: DecryptSettings):
    """Test trigger with malformed json body

    Args:
        local_settings (DecryptSettings): passed automatically via above fixture
    """
    req_success = func.HttpRequest(
        method="POST",
        body="{lol",
        headers={"Content-Type": "application/octet-stream"},
        url="/",
    )
    resp = decrypt.main_with_overload(req_success, local_settings)
    assert resp.status_code == 400 and b"Failed to parse JSON" in resp.get_body()


def test_trigger_missing_settings():
    """Test missing settings object"""
    body = {
        "input": "encrypted.txt",
        "output": "decrypted",
    }
    req_success = func.HttpRequest(
        method="POST",
        body=json.dumps(body),
        headers={"Content-Type": "application/octet-stream"},
        url="/",
    )
    resp = decrypt.main_with_overload(req_success, {})
    assert (
        resp.status_code == 500
        and b"Failed to create storage client" in resp.get_body()
    )


def test_trigger_missing_params(local_settings: DecryptSettings):
    """Test missing parameters

    Args:
        local_settings (DecryptSettings): (Fixture) pre-configured test settings
    """
    body = {
        "output": "decrypted",
    }
    req_success = func.HttpRequest(
        method="POST",
        body=json.dumps(body),
        headers={"Content-Type": "application/octet-stream"},
        url="/",
    )
    resp = decrypt.main_with_overload(req_success, {})
    assert resp.status_code == 400 and b"Missing required parameters" in resp.get_body()

    body = {
        "input": "decrypted",
    }
    req_success = func.HttpRequest(
        method="POST",
        body=json.dumps(body),
        headers={"Content-Type": "application/octet-stream"},
        url="/",
    )
    resp = decrypt.main_with_overload(req_success, {})
    assert resp.status_code == 400 and b"Missing required parameters" in resp.get_body()
