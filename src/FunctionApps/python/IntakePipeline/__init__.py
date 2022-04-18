import logging

import azure.functions as func

from IntakePipeline.transform import transform_bundle
from IntakePipeline.linkage import add_patient_identifier
from IntakePipeline.fhir import (
    upload_bundle_to_fhir_server,
    store_bundle,
    store_message,
    get_fhirserver_cred_manager,
)
from IntakePipeline.conversion import (
    convert_batch_messages_to_list,
    convert_message_to_fhir,
)

from config import get_required_config

from phdi_transforms.geo import get_smartystreets_client


def run_pipeline(blob: func.InputStream, filetype: str):
    salt = get_required_config("HASH_SALT")
    geocoder = get_smartystreets_client(
        get_required_config("SMARTYSTREETS_AUTH_ID"),
        get_required_config("SMARTYSTREETS_AUTH_TOKEN"),
    )
    fhir_url = get_required_config("FHIR_URL")
    fhirserver_cred_manager = get_fhirserver_cred_manager(fhir_url)

    container_url = get_required_config("INTAKE_CONTAINER_URL")
    valid_output_path = get_required_config("VALID_OUTPUT_CONTAINER_PATH")
    invalid_output_path = get_required_config("INVALID_OUTPUT_CONTAINER_PATH")

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

    # The HL7 messages that VA sent have weird unicode characters at the beginning
    # and end of the files (\\u000b & \\u001c, respectively) that can't be decoded.
    # The quick fix is to ignore the errors.
    # TODO: Properly handle the erroneous unicode characters.
    messages = convert_batch_messages_to_list(
        blob.read().decode("utf-8", errors="ignore")
    )
    for i, message in enumerate(messages):
        token = fhirserver_cred_manager.get_access_token()
        response = convert_message_to_fhir(
            message=message,
            message_format=message_format,
            message_type=message_type,
            access_token=token.token,
            fhir_url=fhir_url,
        )

        if response.status_code == 200:
            bundle = response.json()
            transform_bundle(geocoder, bundle)
            add_patient_identifier(salt, bundle)
            store_bundle(container_url, valid_output_path, bundle, bundle_type)
            upload_bundle_to_fhir_server(fhirserver_cred_manager, bundle)
        # A status code of 400 is returned if the HL7 is invalid
        # We're seeing this a lot for malformed datetimes.
        else:
            # TODO: 76-78 should probably be its own function, but in what module?
            ftype, fname = blob.name.split("/")[-2:]
            fname, ext = fname.rsplit(".", 1)
            filename = f"{ftype.lower()}-{fname}-{i}.{ext}"
            store_message(container_url, invalid_output_path, filename, message)


def main(blob: func.InputStream) -> func.HttpResponse:
    logging.info("Triggering intake pipeline")
    try:
        if blob.name.endswith(".hl7") or blob.name.endswith(".xml"):
            filetype = blob.name.split("/")[-2].lower()
            run_pipeline(blob, filetype)
    except Exception:
        logging.exception("exception caught while running the intake pipeline")
        return func.HttpResponse(
            "error while running the intake pipeline", status_code=500
        )

    return func.HttpResponse("pipeline run successfully")
