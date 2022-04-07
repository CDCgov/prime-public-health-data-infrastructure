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
    # Default fhir_location to be the input file
    fhir_location = file

    # If input file is a zip file, unzip it, and process the resulting directory
    if zipfile.is_zipfile(file):
        fhir_location = _unzip_input_file(file)
    
    # Process input FHIR file or directory
    process_fhir(fhir_location)


def _unzip_input_file(zip_filepath: str) -> str:
    with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
        zip_ref.extractall(unzipped_directory)
        return unzipped_directory

def process_fhir(path: str):
    path = os.fsencode(path)
    if os.isdir(path):
        for file in os.listdir(path):
            filename = os.fsdecode(file)
            #; Recursively call on files within directory
            process_fhir(filename)
    elif(path.endswith(".ndjson")):
        process_fhir_ndjson(path)
    else:
        process_fhir_resource(path)
        
def process_fhir_ndjson(filename: str):
    with open(filename) as fp:
        for line in fp:
            import_to_fhir(line)

def process_fhir_resource(fhir_filepath: str = "", fhir_string: str = ""):
    if os.path.exists(fhir_filepath):
        fhir_string = open(fhir_filepath).read()

    import_to_fhir(fhir_string)
    

def import_to_fhir(json_string: str, method: str = "PUT"):
    try:
        token = get_access_token()
    except Exception:
        logging.exception("Failed to get access token")
        raise requests.exceptions.HTTPError("Authorization error occurred while processing information into FHIR server.")
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
        json_object = json.loads(json_string)
        resource_id = json_object["id"]
        resource_type = json_object["resourceType"]

        if resource_type == "Bundle":
            transaction_json = _ensure_bundle_transaction(json_object,method,fhir_url)
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
                data=json_string,
            )
            print(f"status={resp.status_code} message={resource_id}")
        elif method == "PUT":
            resp = requests.put(
                f"{fhir_url}/{resource_type}/{resource_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/fhir+json",
                    "Content-Type": "application/fhir+json",
                },
                data=json_string
            )

    except Exception:
        logging.exception("Request using method " + method + " failed for json: " + json_string)
        return 

def _ensure_bundle_transaction(json_object : dict, method: str, fhir_url: str) -> dict:
    if json_object["resourceType"] != "Bundle":
        raise ValueError("_ensure_bundle_transaction called on non-Bundle resource: " + json_object["resourceType"])

    if method not in ("PUT","POST"):
        raise ValueError("_ensure_bundle_transaction only supports PUT and POST methods")

    new_bundle = copy.deepcopy(json_object)
    new_bundle["type"] = "transaction"

    for entry in new_bundle["entry"]:
        url = fhir_url + "/" + entry["resource"]["resourceType"]

        # PUT requires the URL to contain the resource ID, POST does not.
        if method == "PUT":
            url += "/" + entry["resource"]["id"]

        entry["request"] = { "method": method,
                            "url": url}
        
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
