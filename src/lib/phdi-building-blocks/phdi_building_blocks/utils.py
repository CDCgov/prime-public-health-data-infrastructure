from typing import List


def find_patient_resources(bundle: dict) -> List[dict]:
    """
    Collect all patient resources in a given bundle of FHIR data and
    return references to them in a list.
    :param dict bundle: The FHIR bundle to find patients in
    :return: A list of references to patient dictionaries
    :rtype: List[dict]
    """
    return [
        r
        for r in bundle.get("entry")
        if r.get("resource").get("resourceType") == "Patient"
    ]


def get_one_line_address(address: dict) -> str:
    """
    Extract a one-line string representation of an address from a
    FHIR-type dictionary holding address information.
    :param dict address: The address bundle
    :return: The one-line string of the address
    :rtype: str
    """
    raw_one_line = " ".join(address.get("line", []))
    raw_one_line += f" {address.get('city')}, {address.get('state')}"
    if "postalCode" in address and address["postalCode"]:
        raw_one_line += f" {address['postalCode']}"
    return raw_one_line
