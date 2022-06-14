from typing import List, Union
from urllib3 import Retry
import requests
from requests.adapters import HTTPAdapter
import json
import logging


def find_resource_by_type(bundle: dict, resource_type: str) -> List[dict]:
    """
    Collect all patient resources in a given bundle of FHIR data and
    return references to them in a list.

    :param bundle: The FHIR bundle to find patients in
    :param resource_type: The type of FHIR resource to find
    :return: A list of references to patient dictionaries
    """
    return [
        resource
        for resource in bundle.get("entry")
        if resource.get("resource").get("resourceType") == resource_type
    ]


def get_one_line_address(address: dict) -> str:
    """
    Extract a one-line string representation of an address from a
    FHIR-type dictionary holding address information.

    :param address: The address bundle
    :return: The one-line string of the address
    """
    raw_one_line = " ".join(address.get("line", []))
    raw_one_line += f" {address.get('city')}, {address.get('state')}"
    if "postalCode" in address and address["postalCode"]:
        raw_one_line += f" {address['postalCode']}"
    return raw_one_line


def get_field(resource: dict, field: str, use: str, default_field: int) -> str:
    """
    For a given field (such as name or address), find the first-occuring
    instance of the field in a given patient JSON dict such that the
    instance is associated with a particular "use" case or qualifier (use
    case here referring to the FHIR-based usage of classifying how a
    value is used in reporting). For example, find the first name for a
    patient that has a "use" of "official" (meaning the name is used
    for official reports). If no instance of a field with the requested
    use case can be found, instead return a specified default field.

    :param resource: Resource from a FHIR bundle
    :param field: The field to extract
    :param use: The use the field must have to qualify
    :param default_field: The index of the field type to treat as
        the default return type if no field with the requested use case is
        found
    :return: The requested use-case-type field
    """
    # The next function returns the "next" (in our case first) item from an
    # iterator that meets a given condition; if non exists, we index the
    # field for a default value
    return next(
        (item for item in resource[field] if item.get("use") == use),
        resource[field][default_field],
    )


def http_request_with_retry(
    url: str,
    retry_count: int,
    request_type: str,
    allowed_methods: List[str],
    headers: dict,
    data: dict = None,
) -> Union[None, requests.Response]:
    """
    Carryout an HTTP Request using a specific retry strategy. Essentially
    a wrapper function around the retry strategy implementation of a
    mounted HTTP request.
    :param url: The url at which to make the HTTP request
    :param retry_count: The number of times to re-try the request, if the
    first attempt fails
    :param request_type: The type of request to be made. Currently supports
    GET and POST.
    :param allowed_methods: The list of allowed HTTP request methods (i.e.
    POST, PUT, etc.) for the specific URL and query
    :param headers: JSON-type dictionary of headers to make the request with,
    including Authorization and content-type
    :param data: JSON data in the case that the request requires data to be
    posted. Defaults to none.
    :return: None, or Response
    """
    # Configure the settings of the 'requests' session we'll make
    # the API call with
    retry_strategy = Retry(
        total=retry_count,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=allowed_methods,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)

    # Now, actually try to complete the API request
    if request_type == "POST":
        try:
            requests.post(
                url,
                headers=headers,
                data=json.dumps(data),
            )
        except Exception:
            logging.exception(
                "POST request to " + url + " failed for data: " + str(data)
            )
            return
    elif request_type == "GET":
        try:
            response = requests.get(
                url,
                headers=headers,
            )
            return response
        except Exception:
            logging.exception("GET request to " + url + " failed.")
