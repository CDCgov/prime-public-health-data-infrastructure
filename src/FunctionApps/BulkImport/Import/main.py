import logging
import os
import zipfile
import io

import requests
import json
import copy
from requests.adapters import HTTPAdapter
from urllib3 import Retry


unzipped_directory = "./FhirResources"


def main(file):
    """ """
    # Default fhir_location to be the input file
    fhir_location = file

    # If input file is a zip file, unzip it, and process the resulting directory
    if zipfile.is_zipfile(file):
        fhir_location = _unzip_input_file(file)

    # Process input FHIR file or directory
    process_fhir(fhir_location)


def _unzip_input_file(zip_filepath: str) -> str:
    """Unzip a file to the unzipped_directory
    :param str zip_filepath: The filepath referencing a zip file.
    """
    with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
        zip_ref.extractall(unzipped_directory)
        return unzipped_directory


def process_fhir(path: str):
    """Process FHIR data contained in the specified file path.

    If the the path points to a directory, all files will be read from that directory recursively.
    Otherwise, a normal file path may be read individually.

    The file(s) found may contain ndjson (file path should end with .ndjson).
    They may also contain standard JSON input (one object per file).
    Whether ndjson or standard JSON, the resource types supported are described in :py:func:`import_to_fhir` documentation.
    :param str path: The path to the file containing FHIR data.
    """
    path = os.fsencode(path)
    if os.isdir(path):
        for file in os.listdir(path):
            filename = os.fsdecode(file)
            # Recursively call on files within directory
            process_fhir(filename)
    elif path.endswith(".ndjson"):
        process_fhir_ndjson(path)
    else:
        process_fhir_resource(path)


def process_fhir_ndjson(filename: str):
    """Process a file containing FHIR resource(s) enclosed by ndjson
    :param str filename: FHIR resource(s) enclosed by ndjson
    """
    with open(filename) as fp:
        for line in fp:
            import_to_fhir(line)


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

    See :py:func:`_ensure_bundle_batch` for details about Bundle conversion and handling.

    :param dict fhir_json: FHIR resource in json format.
    :param str method: HTTP method to use (currently PUT or POST supported)
    """
    try:
        token = get_access_token()
    except Exception:
        logging.exception("Failed to get access token")
        raise requests.exceptions.HTTPError(
            "Authorization error occurred while processing information into FHIR server."
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
            resp = requests.post(
                fhir_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/fhir+json",
                    "Content-Type": "application/fhir+json",
                },
                data=json.dumps(transaction_json),
            )
            print(f"status={resp.status_code} message={resource_id}")
        elif method == "POST":
            resp = requests.post(
                f"{fhir_url}/{resource_type}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/fhir+json",
                    "Content-Type": "application/fhir+json",
                },
                data=json.dumps(fhir_json),
            )
            print(f"status={resp.status_code} message={resource_id}")
        elif method == "PUT":
            resource_id = fhir_json["id"]
            resp = requests.put(
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
    A new "request" will be built for each resource in the Bundle with the following content:
    { "method" = method (from param)
      "url" = resource["resourceType"] (for post), resource["resourceType"]/resource["id"] (for put)}
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
