import logging

from typing import Tuple

import azure.functions as func

from IntakePipeline.transform import transform_bundle
from IntakePipeline.linkage import add_patient_identifier
from IntakePipeline.fhir import (
    upload_bundle_to_fhir_server,
    store_bundle,
    store_message,
    get_fhirserver_cred_manager,
    AzureFhirserverCredentialManager,
)
from IntakePipeline.conversion import (
    convert_batch_messages_to_list,
    convert_message_to_fhir,
)

from config import get_required_config

from phdi_transforms.geo import get_smartystreets_client


def run_pipeline(
    bundle: dict,
    datatype: str,
    cred_manager: AzureFhirserverCredentialManager,
):
    salt = get_required_config("HASH_SALT")
    geocoder = get_smartystreets_client(
        get_required_config("SMARTYSTREETS_AUTH_ID"),
        get_required_config("SMARTYSTREETS_AUTH_TOKEN"),
    )

    transform_bundle(geocoder, bundle)
    add_patient_identifier(salt, bundle)
    store_bundle(
        get_required_config("INTAKE_CONTAINER_URL"),
        get_required_config("VALID_OUTPUT_CONTAINER_PATH"),
        bundle,
        datatype,
    )
    upload_bundle_to_fhir_server(cred_manager, bundle)


def convert_to_fhir(
    blob: func.InputStream,
    fhir_url: str,
    container_url: str,
    invalid_output_path: str,
    cred_manager: AzureFhirserverCredentialManager,
) -> Tuple[str, dict]:
    if blob.name[-3:].lower() not in ("hl7", "xml"):
        raise Exception(f"invalid file extension for {blob.name}")

    filetype = blob.name.split("/")[-2].lower()

    if filetype == "elr":
        message_type = "oru_r01"
        message_format = "hl7v2"
        bundle_type = "ELR"
    elif filetype == "vxu":
        message_type = "vxu_v04"
        message_format = "hl7v2"
        bundle_type = "VXU"
    elif filetype == "eICR":
        message_type = "ccda"
        message_format = "ccda"
        bundle_type = "ECR"
    else:
        raise Exception(f"Found an unidentified message_format: {filetype}")

    # VA sends \\u000b & \\u001c in real data, ignore for now
    messages = convert_batch_messages_to_list(
        blob.read().decode("utf-8", errors="ignore")
    )

    for i, message in enumerate(messages):
        token = cred_manager.get_access_token()
        response = convert_message_to_fhir(
            message=message,
            message_format=message_format,
            message_type=message_type,
            access_token=token.token,
            fhir_url=fhir_url,
        )

        if response.status_code == 200:
            return bundle_type, response.json()
        else:
            ftype, fname = blob.name.split("/")[-2:]
            fname, ext = fname.rsplit(".", 1)
            filename = f"{ftype.lower()}-{fname}-{i}.{ext}"
            store_message(container_url, invalid_output_path, filename, message)


def main(blob: func.InputStream) -> func.HttpResponse:
    logging.info("Triggering intake pipeline")
    try:
        fhir_url = get_required_config("FHIR_URL")
        container_url = get_required_config("INTAKE_CONTAINER_URL")
        invalid_output_path = get_required_config("INVALID_OUTPUT_CONTAINER_PATH")
        cred_manager = get_fhirserver_cred_manager(fhir_url)

        bundles = convert_to_fhir(
            blob, fhir_url, container_url, invalid_output_path, cred_manager
        )
        for bundle, datatype in bundles:
            run_pipeline(bundle, datatype, cred_manager)
    except Exception:
        logging.exception("exception caught while running the intake pipeline")
        return func.HttpResponse(
            "error while running the intake pipeline", status_code=500
        )

    return func.HttpResponse("pipeline run successfully")
