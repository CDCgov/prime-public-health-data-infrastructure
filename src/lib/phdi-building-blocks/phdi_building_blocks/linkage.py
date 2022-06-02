import hashlib
import copy
from phdi_building_blocks.utils import find_patient_resources, get_one_line_address


def add_linking_identifier_to_patients(
    bundle: dict, salt_str: str, overwrite: bool = True
) -> dict:
    """
    Given a FHIR resource bundle:

    * identify all patient resource(s) in the bundle
    * extract standardized name, DOB, and address information for each
    * compute a unique hash string based on these fields
    * add the hash string to the list of identifiers held in that patient resource

    :param bundle: The FHIR bundle for whose patients to add a
        linking identifier
    :param salt_str: The suffix string added to prevent being
        able to reverse the hash into PII
    :param overwrite: Whether to write the new standardizations
        directly into the given bundle, changing the original data (True
        is yes)
    :return: The bundle of data with patients having unique identifiers
    """
    # Copy the data if we don't want to overwrite the original
    if not overwrite:
        bundle = copy.deepcopy(bundle)

    for resource in find_patient_resources(bundle):
        patient = resource.get("resource")

        # Combine given and family name
        recent_name = get_field_with_use(patient, "name", "official", 0)
        name_parts = recent_name.get("given", []) + [recent_name.get("family")]
        name_str = "-".join([n for n in name_parts if n])

        # Compile one-line address string
        address_line = ""
        if "address" in patient:
            address = get_field_with_use(patient, "address", "home", 0)
            address_line = get_one_line_address(address)

        # Generate and store unique hash code
        link_str = name_str + "-" + patient["birthDate"] + "-" + address_line
        hashcode = generate_hash_str(link_str, salt_str)

        if "identifier" not in patient:
            patient["identifier"] = []

        patient["identifier"].append(
            {
                "value": hashcode,
                # Note: this system value corresponds to the FHIR specification
                # for a globally used / generated ID or UUID--the standard here
                # is to make the use "temporary" even if it's not
                "system": "urn:ietf:rfc:3986",
                "use": "temp",
            }
        )
    return bundle


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


def generate_hash_str(linking_identifier: str, salt_str: str) -> str:
    """
    Given a string made of concatenated patient information, generate
    a hash for this string to serve as a "unique" identifier for the
    patient.

    :param linking_identifier: The concatenation of a patient's name,
        address, and date of birth, delimited by dashes
    :param salt_str: The salt to concatenate onto the end to prevent
        being able to reverse-engineer PII
    :return: The unique patient hash
    """
    hash_obj = hashlib.sha256()
    to_encode = (linking_identifier + salt_str).encode("utf-8")
    hash_obj.update(to_encode)
    return hash_obj.hexdigest()
