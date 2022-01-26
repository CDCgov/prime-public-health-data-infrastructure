import logging
import pysftp
import sys
import azure.functions as func
from .settings import settings
from azure.storage.blob import BlobServiceClient
import uuid
from io import BytesIO
from pathlib import Path


def print_tree(sftp: pysftp.Connection, path: str):
    file_names = []
    dir_names = []
    other_names = []

    def store_files(fname: str):
        file_names.append(fname)

    def store_dirs(dirname: str):
        dir_names.append(dirname)

    def store_other(name: str):
        other_names.append(name)

    sftp.walktree(path, store_files, store_dirs, store_other, recurse=True)
    logging.info(
        f"File names: {file_names}\nDirectory names: {dir_names}\nOther names: {other_names}"
    )


def upload_blob(local_file_name: str, data: BytesIO):
    if not settings.connection_string:
        exit(f"Connection string not set")
    blob_service_client = BlobServiceClient.from_connection_string(
        settings.connection_string
    )
    # Create a unique name for the container
    container_name = str(uuid.uuid4())

    # Create the container
    logging.debug(f"Creating container {container_name}")

    container_client = blob_service_client.create_container(container_name)
    logging.debug("\nListing existing blobs...")

    # List the blobs in the container
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        logging.debug("\t" + blob.name)

    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=local_file_name
    )

    logging.info(
        "\nUploading passed-in blob to Azure Storage as blob:\n\t" + local_file_name
    )
    blob_client.upload_blob(data)


def test_decryption(sftp: pysftp.Connection):
    target_file_path = "/eICR/TEST_FILE.TXT"
    target_file_name = Path(target_file_path).name
    file_object = BytesIO()
    sftp.getfo(target_file_path, file_object)
    file_object.seek(0)
    logging.debug(
        f"Uploading {target_file_name} at path {target_file_path} Azure Storage"
    )
    upload_blob(target_file_name, file_object)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    logging.info(f"Settings: {settings}")

    try:
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        sftp = pysftp.Connection(
            settings.hostname,
            username=settings.username,
            password=settings.password,
            cnopts=cnopts,
        )
        logging.info("Top level directory listing:")
        # for file_path in sftp.listdir("/ELR"):
        #     logging.info(f"filename: {file_path}")
        print_tree(sftp, "/")

        return func.HttpResponse(f"This HTTP triggered function executed successfully.")
    except:
        e = sys.exc_info()
        logging.error(f"Exception: {e}, Traceback: {e[2]}")
        return func.HttpResponse(f"Error in response: {e}", status_code=500)
