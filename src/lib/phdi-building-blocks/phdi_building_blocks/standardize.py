import phonenumbers
import pycountry
from typing import Callable, Literal, Generator, List

from phdi_building_blocks.utils import find_patient_resources


def standardize_name(raw: str) -> str:
    """trim spaces and force uppercase

    >>> standardize_name(" JohN Doe ")
    'JOHN DOE'
    """

    raw = [x for x in raw if not x.isnumeric()]
    raw = "".join(raw)
    raw = raw.upper()
    raw = raw.strip()
    return raw


def standardize_patient_name(
    bundle: dict, standardize: Callable = standardize_name
) -> dict:
    """Given a FHIR bundle and a standardization function, standardize the patient names
    in all patient resources in the bundle. By default the standardize_name function
    defined in this module is used, but the user is free to provide their own function
    specifying a standardization process as long as it accepts and returns a string."""

    for resource in find_patient_resources(bundle):
        patient = resource.get("resource")
        if "extension" not in patient:
            patient["extension"] = []

        # Transform names
        for name in patient.get("name", []):
            if "family" in name:
                std_family = standardize(name["family"])
                raw_family = name["family"]
                patient["extension"].append(
                    {
                        "url": "http://usds.gov/fhir/phdi/StructureDefinition/family-name-was-standardized",  # noqa
                        "valueBoolean": raw_family != std_family,
                    }
                )
                name["family"] = std_family

            if "given" in name:
                std_givens = [standardize(g) for g in name["given"]]
                raw_givens = [g for g in name["given"]]
                any_diffs = any(
                    [raw_givens[i] != std_givens[i] for i in range(len(raw_givens))]
                )
                patient["extension"].append(
                    {
                        "url": "http://usds.gov/fhir/phdi/StructureDefinition/given-name-was-standardized",  # noqa
                        "valueBoolean": any_diffs,
                    }
                )
                name["given"] = std_givens

    return bundle


def country_extractor(
    resource: dict, code_type: Literal["alpha_2", "alpha_3", "numeric"] = "alpha_2"
) -> List[str]:
    """
    Given a FHIR resource yield a generator containing all of the counries found in the
    resource in a standard form sepcified by code_type.

    Args:
        resource (dict): A FHIR resource respresented as a dictionary.
        code_type (str): A string equal to 'alpha_2', 'alpha_3', or 'numeric' to specify
                         which type of standard country identifier to generate.
    Returns:
        countries (list): A list containing country codes as specified by code_type for
        each country found in resource.

    We currently only handle extracting countries from patient resources, however as
    need arises is the future funcionality can be expanded.
    """
    countries = []
    resource_type = resource.get("resource").get("resourceType")
    if resource_type == "Patient":
        for address in resource.get("resource").get("address"):
            country = address.get("country")
            countries.append(standardize_country(country, code_type))
    return countries


def standardize_phone(raw: str, countries: List = [None, "US"]) -> str:
    """
    Given a phone number and optionally an associated FHIR resource and country
    extraction function if able to parse the phone number return it in the E.164
    standardard international format. If the phone number is not parseable return none.

    Phone number parsing process:
    A maximum of three attemtps are made to parse any phone number.
    First, we try to parse the phone number without any additional country information.
    If this succeeds it must have been provided in a standard inernational format which
    is the ideal case. If the first attempt fails and a FHIR resource associated with
    the phone number and a country extraction function are provided we make a second
    attempt to parse the phone number using any countries extracted from the resource.
    Finally, in the case where the second attempt fails for a resource and country
    extraction function are not provided we make a final attempt to parse the number
    assuming it is American.

    Args:
        raw (str): Raw phone number to be standardized.

        resource (dict): FHIR resource that the raw phone originated from that possibly
                         contains information indicating which country the phone number
                         is from.

        countries (list): A list containing 2 letter ISO country codes for each country
                          extracted from resource of the phone number to be standardized
                          that might indicate it the phone numbers country of origin.
    Returns:
        standardized (str): The standardized phone number in E.164 format when the raw
                            phone number was succesfully parsed and an emptry string
                            otherwise.
    """

    if countries != [None, "US"]:
        countries = [None] + countries + ["US"]

    standardized = ""
    for country in countries:
        try:
            standardized = phonenumbers.parse(raw, country)
        except phonenumbers.phonenumberutil.NumberParseException:
            continue
    if standardized != "":
        standardized = str(
            phonenumbers.format_number(
                standardized, phonenumbers.PhoneNumberFormat.E164
            )
        )
    return standardized


def standardize_country(
    raw_country: str, code_type: Literal["alpha_2", "alpha_3", "numeric"] = "alpha_2"
) -> str:
    """
    Given a country return it in a standard form as specified by code_type.

    Args:
        raw_country (str): Country to be standardized.
        code_type (str): A string equal to 'alpha_2', 'alpha_3', or 'numeric' to specify
                         which type of standard country identifier to generate.

    Returns:
        standard_country (str): Country in standardized form, or None if unable to 
        standardize.
    """
    standard_country = ""
    if len(raw_country) == 3 and raw_country.isalpha():
        standard_country = pycountry.countries.get(alpha_3=raw_country)
    elif len(raw_country) == 2 and raw_country.isalpha():
        standard_country = pycountry.countries.get(alpha_2=raw_country)
    elif len(raw_country) == 3 and raw_country.isnumeric():
        standard_country = pycountry.countries.get(numeric=raw_country)
    elif len(raw_country) >= 4 and all(x.isalpha() or x.isspace() for x in raw_country):
        possible_countries = pycountry.countries.search_fuzzy(raw_country)
        if len(possible_countries) == 1:
            standard_country = possible_countries[0]

    if standard_country != "":
        if code_type == "alpha_2":
            standard_country = standard_country.alpha_2
        elif code_type == "alpha_3":
            standard_country = standard_country.alpha_3
        elif code_type == "numeric":
            standard_country = standard_country.numeric

    return standard_country


def standardize_patient_phone(
    bundle: dict, standardize: Callable = standardize_phone
) -> dict:
    """Given a FHIR bundle and a standardization function, standardize the phone numbers
    in all patient resources in the bundle. By default the standardize_phone function
    defined in this module is used, but the user is free to provide their own function
    specifying a standardization process as long as it accepts and returns a string."""

    for resource in find_patient_resources(bundle):
        patient = resource.get("resource")
        if "extension" not in patient:
            patient["extension"] = []
        # Transform phone numbers
        raw_phones = []
        std_phones = []
        countries = country_extractor(resource)
        for telecom in patient.get("telecom", []):
            if telecom.get("system") == "phone" and "value" in telecom:
                transformed_phone = standardize(telecom["value"], countries)
                raw_phones.append(telecom["value"])
                std_phones.append(transformed_phone)
                telecom["value"] = transformed_phone
        any_diffs = len(raw_phones) != len(std_phones) or any(
            [raw_phones[i] != std_phones[i] for i in range(len(raw_phones))]
        )
        patient["extension"].append(
            {
                "url": "http://usds.gov/fhir/phdi/StructureDefinition/phone-was-standardized",  # noqa
                "valueBoolean": any_diffs,
            }
        )
    return bundle
