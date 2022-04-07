import copy
import io
import json
import logging
import pathlib
import uuid
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from typing import Iterator, IO

from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient


def get_blob_client(container_url: str) -> ContainerClient:
    """Use whatever creds Azure can find to authenticate with the storage container"""
    creds = DefaultAzureCredential()
    return ContainerClient.from_container_url(container_url, credential=creds)


def get_blobs(container_url: str, container_prefix: str) -> Iterator[IO]:
    """Grabs blob files from the container as a readable file-like iterator"""
    client = get_blob_client(container_url)
    for props in client.list_blobs(name_starts_with=container_prefix):
        logging.info(f"reading blob {props.name}")
        if props.size > 0:
            # If it's an actual file, download it and yield out the individual records
            blob_client = client.get_blob_client(props)
            yield io.BytesIO(blob_client.download_blob().content_as_bytes())
    return


def read_fhir_bundles(container_url: str, container_prefix: str) -> Iterator[dict]:
    """Reads FHIR bundle dicts from Azure blob storage as an iterator"""
    for fp in get_blobs(container_url, container_prefix):
        for line in fp:
            try:
                yield json.loads(line)
            except Exception:
                logging.exception("failed to read json contents in line, skipping file")
                break


def store_bundle(container_url: str, prefix: str, bundle: dict) -> None:
    """Store the given bundle in the output container, in FHIR format"""
    client = get_blob_client(container_url)
    blob = client.get_blob_client(str(pathlib.Path(prefix) / f"{uuid.uuid4()}.fhir"))
    blob.upload_blob(json.dumps(bundle).encode("utf-8"))


def upload_bundle_to_fhir_server(bundle: dict) -> None:
    """Upload a FHIR bundle to FHIR server"""
    process_fhir_resource(bundle)


def process_fhir_resource(
    fhir_json: dict = {}, fhir_string: str = "", fhir_filepath: str = ""
):
    """Process a file containing FHIR resource(s) enclosed by ndjson
    :param str filename: FHIR resource(s) enclosed by ndjson
    """
    if len(fhir_json) > 0:
        pass
    elif os.path.exists(fhir_filepath):
        fhir_string = open(fhir_filepath).read()
        fhir_json = json.loads(fhir_string)
    else:
        fhir_json = json.loads(fhir_string)

    import_to_fhir(fhir_json)


def import_to_fhir(fhir_json: dict, method: str = "PUT"):
    """Import a FHIR resource to the FHIR server.
    The submissions may Bundles or individual FHIR resources.

    See :py:func:`_ensure_bundle_batch` for details about Bundle
    conversion and handling.

    :param dict fhir_json: FHIR resource in json format.
    :param str method: HTTP method to use (currently PUT or POST supported)
    """
    try:
        token = get_access_token()
    except Exception:
        logging.exception("Failed to get access token")
        raise requests.exceptions.HTTPError(
            "Authorization error occurred while processing information into \
            FHIR server."
        )
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "PUT", "POST", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    fhir_url = os.environ.get("FHIR_URL", "")
    try:
        resource_type = fhir_json["resourceType"]

        if resource_type == "Bundle":
            transaction_json = _ensure_bundle_batch(fhir_json, method)
            requests.post(
                fhir_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/fhir+json",
                    "Content-Type": "application/fhir+json",
                },
                data=json.dumps(transaction_json),
            )
        elif method == "POST":
            requests.post(
                f"{fhir_url}/{resource_type}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/fhir+json",
                    "Content-Type": "application/fhir+json",
                },
                data=json.dumps(fhir_json),
            )
        elif method == "PUT":
            resource_id = fhir_json["id"]
            requests.put(
                f"{fhir_url}/{resource_type}/{resource_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/fhir+json",
                    "Content-Type": "application/fhir+json",
                },
                data=json.dumps(fhir_json),
            )

    except Exception:
        logging.exception(
            "Request using method " + method + " failed for json: " + str(fhir_json)
        )
        return


def _ensure_bundle_batch(fhir_json: dict, method: str) -> dict:
    """Convert a FHIR Bundle of any type to a "batch" bundle.

    The received bundle will be converted to a "batch" type.
    A new "request" will be built for each resource in the Bundle
    with the following content:
    { "method" = method (from param)
      "url" = resource["resourceType"] (for post),
              resource["resourceType"]/resource["id"] (for put)}
    }

    :param dict fhir_json: FHIR Bundle
    :param str method: PUT for update or POST for create.
    PUT can also create, and will use the submitted id
    POST will always create a new resource and assign a new id
    """
    if fhir_json["resourceType"] != "Bundle":
        raise ValueError(
            "_ensure_bundle_transaction called on non-Bundle resource: "
            + fhir_json["resourceType"]
        )

    if method not in ("PUT", "POST"):
        raise ValueError(
            "_ensure_bundle_transaction only supports PUT and POST methods"
        )

    new_bundle = copy.deepcopy(fhir_json)
    new_bundle["type"] = "transaction"

    for entry in new_bundle["entry"]:
        url = entry["resource"]["resourceType"]

        # PUT requires the URL to contain the resource ID, POST does not.
        if method == "PUT":
            url += "/" + entry["resource"]["id"]

        entry["request"] = {"method": method, "url": url}

    return new_bundle


def get_access_token() -> str:
    """Get the access token based on creds in the environment"""
    tenant_id = os.environ.get("TENANT_ID")
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
    resp = requests.post(
        url,
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ.get("CLIENT_ID", ""),
            "client_secret": os.environ.get("CLIENT_SECRET", ""),
            "resource": os.environ.get("FHIR_URL", ""),
        },
    )

    if resp.ok and "access_token" in resp.json():
        return resp.json().get("access_token")

    logging.error(
        f"access token request failed status={resp.status_code} message={resp.text}"
    )
    raise Exception("access token request failed")
