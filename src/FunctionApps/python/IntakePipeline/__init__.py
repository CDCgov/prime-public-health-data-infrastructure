import logging
import os

import azure.functions as func

from IntakePipeline.transform import transform_bundle
from IntakePipeline.linkage import add_patient_identifier
from IntakePipeline.fhir import read_fhir_bundles, upload_bundle_to_fhir_server

from phdi_transforms.geo import get_smartystreets_client


def get_required_config(varname: str) -> str:
    """Grab a required config val and throw an exception if it's not present"""
    if varname not in os.environ:
        raise Exception(f"Config value {varname} not found in the environment")
    return os.environ[varname]


def run_pipeline():
    geocoder = get_smartystreets_client(
        get_required_config("SMARTYSTREETS_AUTH_ID"),
        get_required_config("SMARTYSTREETS_AUTH_TOKEN"),
    )

    for bundle in read_fhir_bundles(
        get_required_config("INTAKE_CONTAINER_URL"),
        get_required_config("INTAKE_CONTAINER_PREFIX"),
    ):
        transform_bundle(geocoder, bundle)
        add_patient_identifier(bundle)
        upload_bundle_to_fhir_server(bundle)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Triggering intake pipeline")
    try:
        run_pipeline()
    except Exception:
        logging.exception("exception caught while running the intake pipeline")
        return func.HttpResponse(
            "error while running the intake pipeline", status_code=500
        )

    return func.HttpResponse("pipeline run successfully")
