import json
import pathlib
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient


def get_blob_client(container_url: str) -> ContainerClient:
    """
    Obtains a client connected to an Azure storage container by
    using whatever credentials can be found to authenticate.

    :param container_url: The url at which to access the container
    :return: An Azure container client for the given container
    """
    creds = DefaultAzureCredential()
    return ContainerClient.from_container_url(container_url, credential=creds)


def store_data(
    container_url: str,
    prefix: str,
    filename: str,
    bundle_type: str,
    message_json: dict = None,
    message: str = None,
) -> None:
    """
    Stores provided data, which is either a FHIR bundle or an HL7 message,
    in an appropriate output container.

    :param container_url: The url at which to access the container
    :param prefix: The "filepath" prefix used to navigate the
      virtual directories to the output container
    :param filename: The name of the file to write the data to
    :param bundle_type: The type of data (FHIR or HL7) being written
    :param message_json: The content of a message encoded in json
      format. Used when the input data type is FHIR.
    :param message: The content of a message encoded as a raw bytestring.
      Used when the input data type is HL7.
    """
    client = get_blob_client(container_url)
    blob = client.get_blob_client(str(pathlib.Path(prefix) / bundle_type / filename))
    if message_json is not None:
        blob.upload_blob(json.dumps(message_json).encode("utf-8"), overwrite=True)
    elif message is not None:
        blob.upload_blob(bytes(message, "utf-8"), overwrite=True)
