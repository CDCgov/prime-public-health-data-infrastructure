import io
import json
import logging
import requests

from azure.storage.blob import download_blob_from_url
from azure.identity import DefaultAzureCredential
from requests.adapters import HTTPAdapter
from typing import TextIO, Tuple
from urllib3 import Retry


def upload_bundle_to_fhir_server(bundle: dict, access_token: str, fhir_url: str):
    """Import a FHIR resource to the FHIR server.
    The submissions may be Bundles or individual FHIR resources.

    :param AzureFhirserverCredentialManager fhirserver_cred_manager: Credential manager.
    :param dict fhir_json: FHIR resource in json format.
    :param str method: HTTP method to use (currently PUT or POST supported)
    """
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "PUT", "POST", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    try:
        requests.post(
            fhir_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            },
            data=json.dumps(bundle),
        )
    except Exception:
        logging.exception("Request to post Bundle failed for json: " + str(bundle))
        return


def export_from_fhir_server(
    access_token: str, fhir_url: str, export_scope: str, since: str, resource_type: str
) -> dict:
    """ """
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    try:
        export_url = _compose_export_url(
            fhir_url=fhir_url,
            export_scope=export_scope,
            since=since,
            resource_type=resource_type,
        )
        response = requests.get(
            export_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/fhir+json",
                "Prefer": "respond-async",
            },
        )

        if response.status_code == 202:

            poll_response = _export_fhir_server_poll(
                response.headers.get("Content-Location")
            )

            if poll_response.status_code == 200:
                return poll_response.json

    except Exception:
        logging.exception("Exception occurred while attempting export.")
        return


def _compose_export_url(
    fhir_url: str, export_scope: str = "", since: str = "", resource_type: str = ""
) -> str:
    export_url = fhir_url
    if export_scope == "Patient" or export_scope.startswith("Group/"):
        export_url += f"/{export_scope}/$export"
    elif export_scope == "":
        export_url += f"{fhir_url}/$export"
    else:
        raise ValueError("Invalid scope {scope}.  Expected 'Patient' or 'Group/[ID]'.")

    # Start with ? url argument separator, and change it to & after the first parameter
    # is appended to the URL
    separator = "?"
    if since:
        export_url += f"{separator}_since={since}"
        separator = "&"

    if resource_type:
        export_url += f"{separator}_since={resource_type}"
        separator = "&"

    return export_url


def _export_fhir_server_poll(poll_url: str, access_token: str) -> requests.Response:
    http_session = requests.Session()
    retry_strategy = Retry(
        total=20,
        backoff_factor=1,
        status_forcelist=[202],
        allowed_methods=["GET"],
    )
    http_session.mount("https://", HTTPAdapter(retry_strategy))

    response = http_session.get(
        poll_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/fhir+json",
            "Prefer": "respond-async",
        },
    )

    # Handle error conditions
    if response.status_code == 202:
        raise requests.HTTPError(
            f"Request timed out waiting for export request to `{poll_url}` to complete."
        )
    elif response.status_code != 200:
        raise requests.HTTPError(
            f"Encountered status {response.status_code} when requesting status"
            + "of export `{poll_url}`"
        )

    # If no error conditions, return response
    return response


def download_from_export_response(export_response: dict) -> Tuple[str, TextIO]:
    for export_entry in export_response.get("output", []):
        resource_type = export_entry.get("type")
        blob_url = export_entry.get("url")
        yield (resource_type, _download_blob(blob_url=blob_url))


def _download_blob(blob_url: str) -> TextIO:
    text_buffer = io.TextIOWrapper()
    cred = DefaultAzureCredential()
    download_blob_from_url(blob_url=blob_url, output=text_buffer, credential=cred)
    return text_buffer
