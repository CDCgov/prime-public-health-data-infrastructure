from typing import List


def find_patient_resources(bundle: dict) -> List[dict]:
    """
    Collect all patient resources in a given bundle of FHIR data and
    return references to them in a list.

    :param bundle: The FHIR bundle to find patients in
    :return: A list of references to patient dictionaries
    """
    return [
        resource
        for resource in bundle.get("entry")
        if resource.get("resource").get("resourceType") == "Patient"
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


def get_field_with_use(patient: dict, field: str, use: str, default_field: int) -> str:
    """
    For a given field (such as name or address), find the first-occuring
    instance of the field in a given patient JSON dict such that the
    instance is associated with a particular use. I.e. find the first
    name for a patient that has an "official" use capacity. If no
    instance of a field with the requested use case can be found, instead
    return a specified default field.

    :param patient: Patient from a FHIR bundle
    :param field: The field to extract
    :param use: The use the field must have to qualify
    :param default_field: The index of the field type to treat as
        the default return type if no field with the requested use case is
        found
    :return: The requested use-case-type field
    """
    return next(
        (item for item in patient[field] if item.get("use") == use),
        patient[field][default_field],
    )
