import collections
import json
import logging
import os
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


def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('APP: Python HTTP trigger function processing a request.')
    checks = []

    # task 1: can I lookup IPs? checks whether the DNS from CDC is working
    try:
        google_ip = socket.gethostbyname('google.com')
        checks.append(Check('DNS lookup', 'ok', f'Found IP "{google_ip}" for google.com'))
    except Exception as e:
        checks.append(Check('DNS lookup', 'error', str(e)))

    # task 2: can I reach the internet? if so, what is my IP?
    try:
        response = requests.get(URL_IP_CHECK, timeout=10)
        ip = response.json().get('ip') or 'Unknown IP'
        checks.append(Check('IP Check', 'ok', ip))
    except Exception as e:
        checks.append(Check('IP Check', 'error', str(e)))

    # task 3: can I read from blob storage?
    if is_blank(STORAGE_ACCOUNT_CONNECTION):
        checks.append(Check('Blob read: *', 'error', 'No connection string defined'))
    else:
        service_client = BlobServiceClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION)
        blob_by_container = {}
        containers = ["bronze", "silver", "gold"]

        for container_name in containers:
            container_client = service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client('_test.txt')
            blob = blob_client.download_blob()
            blob_by_container[container_name] = blob
            checks.append(
                Check(f'Blob read: {container_name}', 'ok', f'Read {len(blob)} into type {type(blob)}')
            )

    # task 4: can I write to blob storage?

    # task 5: can I read from key vault?

    # task 0: verify environment
    response = {
        'checks': [c._asdict() for c in checks],
        'env': [f'ENV {k}={v}' for k, v in os.environ.items()],
    }

    return func.HttpResponse(
        body=json.dumps(response, indent=4, sort_keys=True),
        headers={'Content-Type': 'application/json'},
        status_code=200,
    )
