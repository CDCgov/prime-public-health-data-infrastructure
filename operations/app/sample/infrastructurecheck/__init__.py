import collections
import json
import logging
import os
import re
import socket

import azure.functions as func
import requests
from azure.storage.blob import BlobServiceClient


logger = logging.getLogger(__name__)

URL_IP_CHECK = 'https://api.ipify.org/?format=json'
STORAGE_ACCOUNT_CONNECTION = os.environ.get('APPSETTING_AzureWebJobsStorage')

Check = collections.namedtuple('Check', ['name', 'status', 'message'])


def is_blank(v):
    return v is None or v.strip() == ''


def verify_blob_storage():
    checks = []
    try:
        service_client = BlobServiceClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION)
        checks.append(Check('Storage client', 'ok', ''))
    except Exception as e:
        return [Check('Storage client', 'error', f'Failed to create BlobServiceClient: {e}')]

    blob_by_container = {}
    containers = ["bronze", "silver", "gold"]

    for container_name in containers:
        try:
            container_client = service_client.get_container_client(container_name)
            checks.append(Check(f'Container client: {container_name}', 'ok', ''))
        except Exception as e:
            checks.append(
                Check(f'Container client: {container_name}', 'error', f'Failed to create container client: {e}')
            )
            continue
        try:
            blob_client = container_client.get_blob_client('_test.txt')
            checks.append(Check(f'Blob client: {container_name}', 'ok', ''))
        except Exception as e:
            checks.append(
                Check(f'Blob client: {container_name}', 'error', f'Failed to create blob client: {e}')
            )
            continue

        try:
            blob = blob_client.download_blob()
            checks.append(Check(f'Blob download: {container_name}', 'ok', ''))
            checks.append(
                Check(f'Blob read: {container_name}', 'ok', f'Read {len(blob)} into type {type(blob)}')
            )
            blob_by_container[container_name] = blob.content_as_text()
        except Exception as e:
            checks.append(
                Check(f'Blob read: {container_name}', 'error', f'Failed to get blob: {e}')
            )
            continue

    return checks


def verify_dns():
    try:
        google_ip = socket.gethostbyname('google.com')
        return Check('DNS lookup', 'ok', f'Found IP "{google_ip}" for google.com')
    except Exception as e:
        return Check('DNS lookup', 'error', str(e))


def verify_my_ip():
    try:
        response = requests.get(URL_IP_CHECK, timeout=10)
        ip = response.json().get('ip') or 'Unknown IP'
        return Check('IP Check', 'ok', ip)
    except Exception as e:
        return Check('IP Check', 'error', str(e))


def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('APP: Python HTTP trigger function processing a request.')
    checks = []

    # task 1: can I lookup IPs? checks whether the DNS from CDC is working
    checks.append(verify_dns())

    # task 2: can I reach the internet? if so, what is my IP?
    checks.append(verify_my_ip())

    if is_blank(STORAGE_ACCOUNT_CONNECTION):
        checks.append(Check('Blob *', 'error', 'No connection string defined'))
    else:
        checks.extend(verify_blob_storage())

    # task 4: can I write to blob storage?

    # task 5: can I read from key vault?

    accept_header = re.split(r'\s+,\s+', req.headers.get('Accept', ''))

    # just check the first one
    is_text = len(accept_header) > 0 and 'text' in accept_header[0]

    if is_text:
        headers = {'Content-Type': 'text/plain'}
        body = "Checks:\n"
        for c in checks:
            body += f"* {c.name}: {c.status}"
            if c.message != "":
                body += f" - {c.message}"
            body += "\n"

        body += "\nEnvironment:\n"
        for k in sorted(os.environ.keys()):
            body += f"{k}={os.environ[k]}\n"

    else:
        response = {
            'checks': [c._asdict() for c in checks],
            'env': {k: v for k, v in os.environ.items()},
        }
        body = json.dumps(response, indent=4, sort_keys=True)
        headers = {'Content-Type': 'application/json'}

    return func.HttpResponse(
        body=body,
        headers=headers,
        status_code=200,
    )
