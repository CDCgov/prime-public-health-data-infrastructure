from asyncore import file_dispatcher
import base64
import json
import logging
from pathlib import Path
import sys
import traceback
from typing import Optional

import azure.functions as func
import pgpy

from DecryptFunction.settings import DecryptSettings
from DecryptFunction.storage_client import PHDIStorageClient


def decrypt_message(message: bytes, private_key_string: str, password: str) -> bytes:
    """Decrypt a message using a specified private key in base64 encoded format.

    Args:
        message (bytes): the message, as byte string
        private_key_string (str): the private string in base64 encoded format
        password (str): the password for the private key

    Returns:
        bytes: the decrypted version of the message
    """
    logging.info("Decrypting message")
    encrypted_message = pgpy.PGPMessage.from_blob(message)
    decoded_key_string = base64.b64decode(private_key_string)
    pgp_key, _ = pgpy.PGPKey.from_blob(decoded_key_string)
    with pgp_key.unlock(password):
        decrypted = pgp_key.decrypt(encrypted_message).message
    logging.info("Decryption complete")
    return decrypted


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get the message from the request and decrypt it.

    Args:
        req (func.HttpRequest): the request object.
        Pass the encrypted text in the body of the request.

    Returns:
        func.HttpResponse: the decrypted message
    """
    return main_with_overload(req, None)


def main_with_overload(
    req: func.HttpRequest, settings_overload: Optional[DecryptSettings]
) -> func.HttpResponse:
    """Get the message from the request and decrypt it.

    Args:
        req (func.HttpRequest): the request object.
        Pass the encrypted text in the body of the request.

    Returns:
        func.HttpResponse: the decrypted message
    """
    settings = settings_overload or DecryptSettings()
    body = json.loads(req.get_body().decode("utf-8"))
    input_file = body.get("input")
    output_base_path = body.get("output")

    if not input_file or not output_base_path:
        return func.HttpResponse("Missing input output parameter", status_code=400)

    sc = PHDIStorageClient(settings)

    logging.info(f"Reading file at path {input_file}")
    encrypted_message = sc.read_blob(input_file)

    if not settings.private_key or not settings.private_key_password:
        logging.error("Error 500: No private key or password provided")
        return func.HttpResponse(
            "Server missing required settings",
            status_code=500,
        )

    if not encrypted_message:
        logging.error(f"Error 500: No encrypted message found at path {input_file}")
        return func.HttpResponse(
            f"No encrypted message found at path {input_file}",
            status_code=500,
        )

    try:
        logging.info(f"File found. Decrypting file at path {input_file}")
        decrypted_message = decrypt_message(
            encrypted_message, settings.private_key, settings.private_key_password
        )
        logging.info(f"Writing file...")
        output_path = str(Path(output_base_path) / Path(input_file).name)
        sc.upload_data_to_blob(decrypted_message, output_path)
        logging.info(f"Blob written to {output_path}")
        return func.HttpResponse(
            f"Message written to path {output_path}", mimetype="text/plain"
        )
    except ValueError:
        tb = traceback.format_exc()
        logging.error(f"Decryption failed. Traceback: {tb}")
        return func.HttpResponse(
            "Decryption failed",
            status_code=500,
        )
