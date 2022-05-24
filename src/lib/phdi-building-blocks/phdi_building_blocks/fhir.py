import io
import json
import logging
import polling
import requests

from requests.adapters import HTTPAdapter
from typing import Union, Iterator, Tuple, TextIO
from urllib3 import Retry

from azure.identity import DefaultAzureCredential
from azure.storage.blob import download_blob_from_url
from phdi_building_blocks.classes.creds_manager import AzureFhirserverCredentialManager


def generate_filename(blob_name: str, message_index: int) -> str:
    """
    Strip the file type suffix from the blob name, and instead
    append the message index.
    :param str blob_name: The name of the blob to modify
    :param int message_index: The index of this message in the batch
    :return: The derived filename
    :rtype: str
    """
    filename = blob_name.split("/")[-1]
    root_name, _ = filename.rsplit(".", 1)
    return f"{root_name}-{message_index}"


def get_fhirserver_cred_manager(fhir_url: str) -> AzureFhirserverCredentialManager:
    """
    Get an instance of the Azure FHIR Server credential manager configured
    for a given FHIR server url.
    :param str fhir_url: The url of the FHIR server to access
    :return: The credentials manager
    :rtype: AzureFhirserverCredentialManager
    """
    return AzureFhirserverCredentialManager(fhir_url)


def upload_bundle_to_fhir_server(
    bundle: dict, access_token: str, fhir_url: str
) -> None:
    """
    Import a FHIR resource to the FHIR server.
    The submissions may be Bundles or individual FHIR resources.

    :param dict bundle: FHIR bundle (type "batch") to post
    :param str access_token: FHIR Server access token
    :param str fhir_url: The url of the FHIR server to upload to
    """

    # Configure the settings of the 'requests' session we'll make
    # the API call with
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "PUT", "POST", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)

    # Now, actually try to complete the API request
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
    access_token: str,
    fhir_url: str,
    export_scope: str = "",
    since: str = "",
    resource_type: str = "",
    container: str = "",
    poll_step: float = 30,
    poll_timeout: float = 300,
) -> dict:
    """
    Initiate a FHIR $export operation, and poll until it completes.
    If the export operation is in progress at the end of poll_timeout,
    use the default polling behavior to do the last function check
    before shutting down the request.
    :param str access_token: Access token string used to connect to FHIR server
    :param str fhir_url: FHIR Server base URL
    :param str export_scope: Either `Patient` or `Group/[id]` as specified in the FHIR
    spec
    (https://hl7.org/fhir/uv/bulkdata/export/index.html#bulk-data-kick-off-request)
    :param str since: A FHIR instant (https://build.fhir.org/datatypes.html#instant)
    instructing the export to include only resources created or modified after the
    specified instant.
    :param str resource_type: A comma-delimited list of resource types to include.
    :param str container: The name of the container used to store exported files.
    :param float poll_step: the number of seconds to wait between poll requests, waiting
    for export files to be generated.
    :param float poll_timeout: the maximum number of seconds to wait for export files to
    be generated.
    :return: The response from the FHIR export, containing the records that were
    processed
    :rtype: Dict
    """

    # Combine template variables into export endpoint
    logging.debug("Initiating export from FHIR server.")
    export_url = _compose_export_url(
        fhir_url=fhir_url,
        export_scope=export_scope,
        since=since,
        resource_type=resource_type,
        container=container,
    )
    logging.debug(f"Composed export URL: {export_url}")

    # Open connection to the export operation and kickoff process
    response = requests.get(
        export_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/fhir+json",
            "Prefer": "respond-async",
        },
    )
    logging.info(f"Export request completed with status {response.status_code}")

    if response.status_code == 202:

        # Repeatedly poll the endpoint the FHIR server creates for us
        # until either the connection times out (as we configured) or
        # we have the response in hand
        poll_response = export_from_fhir_server_poll(
            poll_url=response.headers.get("Content-Location"),
            access_token=access_token,
            poll_step=poll_step,
            poll_timeout=poll_timeout,
        )

        # We successfully completed the full export
        if poll_response.status_code == 200:
            logging.debug(f"Export content: {poll_response.text}")
            return poll_response.json()

        # Didn't complete / encountered unexpected behavior
        else:
            logging.exception("Unexpected response code during export download.")
            raise requests.HTTPError(response=poll_response)


def _compose_export_url(
    fhir_url: str,
    export_scope: str = "",
    since: str = "",
    resource_type: str = "",
    container: str = "",
) -> str:
    """
    Generate a query string for the export request.  Details in the FHIR spec:
    https://hl7.org/fhir/uv/bulkdata/export/index.html#query-parameters
    :param str fhir_url: The url of the FHIR server to export from
    :param str export_scope: The data we want back (e.g. Patients)
    :param str since: We'll get all FHIR resources that have been updated
    since this given timestamp
    :param str resource_type: Comma-delimited list of resource types we want
    back
    :param str container: The container where we want to store the uploaded
    files
    :return: The url built with our desired export endpoitn criteria
    :rtype: str
    """
    export_url = fhir_url
    if export_scope == "Patient" or export_scope.startswith("Group/"):
        export_url += f"/{export_scope}/$export"
    elif export_scope == "":
        export_url += "/$export"
    else:
        raise ValueError("Invalid scope {scope}.  Expected 'Patient' or 'Group/[ID]'.")

    # Start with ? url argument separator, and change it to & after the first parameter
    # is appended to the URL
    separator = "?"
    if since:
        export_url += f"{separator}_since={since}"
        separator = "&"

    if resource_type:
        export_url += f"{separator}_type={resource_type}"
        separator = "&"

    if container:
        export_url += f"{separator}_container={container}"
        separator = "&"

    return export_url


def __export_from_fhir_server_poll_call(
    poll_url: str, access_token: str
) -> Union[requests.Response, None]:
    """
    Helper method to see if the export files are ready based on received status
    code. If export is still in progress, then we should return null so polling
    continues. If the response is 200, then the export files are ready, and we
    return the HTTP response. Any other status either indicates an error or
    unexpected condition. In this case raise an error.
    :param str poll_url: The endpoint the FHIR server gave us to query for if
    our files are ready
    :param str access_token: The access token we use to authenticate with the
    FHIR server
    :return: None if the files didn't get processed in time, OR a response with
    the relevant status codes and exported records if the files did get processed
    :rtype: Either None, or a Response from Requests
    """
    logging.debug(f"Polling endpoint {poll_url}")
    response = requests.get(
        poll_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/fhir+ndjson",
        },
    )
    if response.status_code == 202:
        # In progress - return None to keep polling
        return
    elif response.status_code == 200:
        # Complete
        return response
    else:
        raise requests.HTTPError(response=response)


def export_from_fhir_server_poll(
    poll_url: str, access_token: str, poll_step: float = 30, poll_timeout: float = 300
) -> requests.Response:
    """
    The main polling function that determines export file avialability after
    an export run has been initiated.
    :param str poll_url: URL to poll for export information
    :param str access_token: Bearer token used for authentication
    :param float poll_step: the number of seconds to wait between poll requests, waiting
    for export files to be generated. defaults to 30
    :param float poll_timeout: the maximum number of seconds to wait for export files to
    be generated. defaults to 300
    :raises polling.TimeoutException: If the FHIR server continually returns a 202
    status indicating in progress until the timeout is reached.
    :raises requests.HTTPError: If an unexpected status code is returned.
    :return: The export response obtained from the FHIR server (200 status code)
    :rtype: requests.Response
    """
    response = polling.poll(
        target=__export_from_fhir_server_poll_call,
        args=[poll_url, access_token],
        step=poll_step,
        timeout=poll_timeout,
    )

    # Handle error conditions
    if response.status_code != 200:
        raise requests.HTTPError(
            f"Encountered status {response.status_code} when requesting status"
            + "of export `{poll_url}`"
        )

    # If no error conditions, return response
    return response


def download_from_export_response(
    export_response: dict,
) -> Iterator[Tuple[str, TextIO]]:
    """
    Accepts the export response content as specified here:
    https://hl7.org/fhir/uv/bulkdata/export/index.html#response---complete-status

    Loops through the "output" array and yields the resource_type (e.g. Patient)
    along with TextIO wrapping ndjson content.

    :param dict export_response: JSON-type dictionary holding the response from
    the export URL the FHIR server set up.
    :yield: tuple containing resource type (e.g. Patient) AND the TextIO of the
    downloaded ndjson content for that resource type
    """
    # TODO: Handle error array that could be contained in the response content.

    for export_entry in export_response.get("output", []):
        resource_type = export_entry.get("type")
        blob_url = export_entry.get("url")
        yield (resource_type, _download_export_blob(blob_url=blob_url))


def _download_export_blob(blob_url: str, encoding: str = "utf-8") -> TextIO:
    """
    Download an export file blob.

    :param str blob_url: Blob URL location to download from Azure Blob storage
    :param str encoding: encoding to apply to the ndjson content, defaults to "utf-8"
    :return: Downloaded content wrapped in TextIO
    :rtype: TextIO
    """
    bytes_buffer = io.BytesIO()
    cred = DefaultAzureCredential()
    download_blob_from_url(blob_url=blob_url, output=bytes_buffer, credential=cred)
    text_buffer = io.TextIOWrapper(buffer=bytes_buffer, encoding=encoding, newline="\n")
    text_buffer.seek(0)
    return text_buffer
