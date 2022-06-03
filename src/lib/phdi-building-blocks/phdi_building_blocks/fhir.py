import io
import json
import logging
import polling
import requests

from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from typing import Union, Iterator, Tuple, TextIO
from urllib3 import Retry

from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential
from azure.storage.blob import download_blob_from_url


class AzureFhirServerCredentialManager:
    """
    A class that manages handling Azure credentials for access to the FHIR server.
    """

    def __init__(self, fhir_url: str):
        self.access_token = None
        self.fhir_url = fhir_url

    def get_fhir_url(self) -> str:
        return self.fhir_url

    def get_access_token(self, token_reuse_tolerance: float = 10.0) -> AccessToken:
        """
        Obtain an access token for the FHIR server the manager is pointed at.
        If the token is already set for this object and is not about to expire
        (within token_reuse_tolerance parameter), then return the existing token.
        Otherwise, request a new one.

        :param token_reuse_tolerance: Number of seconds before expiration; it
        is okay to reuse the currently assigned token
        """
        if not self._need_new_token(token_reuse_tolerance):
            return self.access_token

        # Obtain a new token if ours is going to expire soon
        creds = DefaultAzureCredential()
        scope = f"{self.fhir_url}/.default"
        self.access_token = creds.get_token(scope)
        return self.access_token

    def _need_new_token(self, token_reuse_tolerance: float = 10.0) -> bool:
        """
        Determine whether the token already stored for this object can be reused,
        or if it needs to be re-requested.

        :param token_reuse_tolerance: Number of seconds before expiration
        :return: Whether we need a new token (True means we do)
        """
        try:
            current_time_utc = datetime.now(timezone.utc).timestamp()
            return (
                self.access_token.expires_on - token_reuse_tolerance
            ) < current_time_utc
        except AttributeError:
            # access_token not set
            return True


def generate_filename(blob_name: str, message_index: int) -> str:
    """
    Strip the file type suffix from the blob name, and instead
    append the message index.

    :param blob_name: The name of the blob to modify
    :param message_index: The index of this message in the batch
    :return: The derived filename
    """
    filename = blob_name.split("/")[-1]
    root_name, _ = filename.rsplit(".", 1)
    return f"{root_name}-{message_index}"


def upload_bundle_to_fhir_server(
    bundle: dict, access_token: str, fhir_url: str
) -> None:
    """
    Import a FHIR resource to the FHIR server.
    The submissions may be Bundles or individual FHIR resources.

    :param bundle: FHIR bundle (type "batch") to post
    :param access_token: FHIR Server access token
    :param fhir_url: The url of the FHIR server to upload to
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

    :param access_token: Access token string used to connect to FHIR server
    :param fhir_url: FHIR Server base URL
    :param export_scope: Either `Patient` or `Group/[id]` as specified in the FHIR
        spec
        (https://hl7.org/fhir/uv/bulkdata/export/index.html#bulk-data-kick-off-request)
    :param since: A FHIR instant (https://build.fhir.org/datatypes.html#instant)
        instructing the export to include only resources created or modified after the
        specified instant.
    :param resource_type: A comma-delimited list of resource types to include.
    :param container: The name of the container used to store exported files.
    :param poll_step: the number of seconds to wait between poll requests, waiting
        for export files to be generated.
    :param poll_timeout: the maximum number of seconds to wait for export files to
        be generated.
    :return: The response from the FHIR export, containing the records that were
        processed
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

    :param fhir_url: The url of the FHIR server to export from
    :param export_scope: The data we want back (e.g. Patients)
    :param since: We'll get all FHIR resources that have been updated
    since this given timestamp
    :param resource_type: Comma-delimited list of resource types we want
    back
    :param container: The container where we want to store the uploaded
    files
    :return: The url built with our desired export endpoitn criteria
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

    :param poll_url: The endpoint the FHIR server gave us to query for if
    our files are ready
    :param access_token: The access token we use to authenticate with the
    FHIR server
    :return: None if the files didn't get processed in time, OR a response with
    the relevant status codes and exported records if the files did get processed
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

    :param poll_url: URL to poll for export information
    :param access_token: Bearer token used for authentication
    :param poll_step: the number of seconds to wait between poll requests, waiting
        for export files to be generated. defaults to 30
    :param poll_timeout: the maximum number of seconds to wait for export files to
        be generated. defaults to 300
    :raises polling.TimeoutException: If the FHIR server continually returns a 202
        status indicating in progress until the timeout is reached.
    :raises requests.HTTPError: If an unexpected status code is returned.
    :return: The export response obtained from the FHIR server (200 status code)
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

    :param export_response: JSON-type dictionary holding the response from
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

    :param blob_url: Blob URL location to download from Azure Blob storage
    :param encoding: encoding to apply to the ndjson content, defaults to "utf-8"
    :return: Downloaded content wrapped in TextIO
    """
    bytes_buffer = io.BytesIO()
    cred = DefaultAzureCredential()
    download_blob_from_url(blob_url=blob_url, output=bytes_buffer, credential=cred)
    text_buffer = io.TextIOWrapper(buffer=bytes_buffer, encoding=encoding, newline="\n")
    text_buffer.seek(0)
    return text_buffer
