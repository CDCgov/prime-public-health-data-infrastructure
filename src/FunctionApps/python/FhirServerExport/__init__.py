import azure.functions as func
import config
import json
import logging

from phdi_building_blocks import fhir


def main(req: func.HttpRequest) -> func.HttpResponse:
    fhir_url = config.get_required_config("FHIR_URL")

    poll_step = float(config.get_required_config("FHIR_EXPORT_POLL_INTERVAL", 30))
    poll_timeout = float(config.get_required_config("FHIR_EXPORT_POLL_TIMEOUT", 300))

    cred_manager = fhir.AzureFhirserverCredentialManager(fhir_url=fhir_url)

    access_token = cred_manager.get_access_token()

    try:
        export_response = fhir.export_from_fhir_server(
            access_token=access_token,
            fhir_url=fhir_url,
            export_scope=req.params.get("export_scope", ""),
            since=req.params.get("since", ""),
            resource_type=req.params.get("type", ""),
            poll_step=poll_step,
            poll_timeout=poll_timeout,
        )
        logging.debug(f"Export response received: {json.dumps(export_response)}")
    except Exception as exception:
        # Log and re-raise so it bubbles up as an execution failure
        logging.exception("Error occurred while performing export operation.")
        raise exception

    for resource_type, export_content in fhir.download_from_export_response(
        export_response
    ):
        logging.info(f"Processing resource file for type {resource_type}")
        for line_number, line in enumerate(export_content):
            try:
                resource = json.loads(line)
                process_resource(resource=resource)
            except Exception:
                logging.exception(
                    f"Failed to process resource {line_number} of type {resource_type}"
                )

    return func.HttpResponse(status_code=202)


def process_resource(resource: dict):
    if "resourceType" not in resource or "id" not in resource:
        raise ValueError("Resource encountered without full information.")

    logging.debug(
        f"Processing resource {resource['id']} of type {resource['resourceType']}"
    )
