import collections
import json
import logging
import socket

import azure.functions as func
import requests

logger = logging.getLogger(__name__)

URL_IP_CHECK = 'https://api.ipify.org/?format=json'

Check = collections.namedtuple('Check', ['name', 'status', 'message'])


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

    # task 4: can I write to blob storage?

    # task 5: can I read from key vault?

    return func.HttpResponse(
        body=json.dumps({'checks': [c._asdict() for c in checks]}, indent=4, sort_keys=True),
        headers={'Content-Type': 'application/json'},
        status_code=200,
    )
