import json
import logging

import azure.functions as func
import requests

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('Python HTTP trigger function processing a request.')

    # task 1: can I reach the internet? if so, what is my IP?
    out = {"ip_check": {}}
    try:
        response = requests.get('https://api.ipify.org/?format=json', timeout=10)
        myip = "Unknown"
        if ip := response.json().get('ip'):
            myip = ip
        out['ip_check'] = {'status': 'ok', 'ip': myip}
    except Exception as e:
        out['ip_check'] = {'status': 'error', 'message': str(e)}

    # task 2: can I read from blob storage?

    # task 3: can I write to blob storage?

    # task 4: can I read from key vault?

    return func.HttpResponse(
        body=json.dumps(out),
        headers={'Content-Type': 'application/json'},
        status_code=200
    )
