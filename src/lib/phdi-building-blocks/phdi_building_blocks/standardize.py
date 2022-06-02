import phonenumbers
import pycountry
from typing import Callable, Literal, List
from phdi_building_blocks.utils import find_patient_resources
import copy


def non_numeric_caps_standardization(raw_name: str) -> str:
    """
    Perform standardization on a provided name string. Name
    standardization performs:

    * removal of all numeric characters
    * trimming of extra whitespace
    * converting all characters to uppercase

    For example, standardize_name(" JohN Doe ") is 'JOHN DOE'.

    :param raw: The raw string to standardize
    :return: The standardized name string
    """
    raw_name = [x for x in raw_name if not x.isnumeric()]
    raw_name = "".join(raw_name)
    raw_name = raw_name.upper()
    raw_name = raw_name.strip()
    return raw_name


def standardize_patient_names(
    bundle: dict,
    standardization_mode: str = "non_numeric_caps",
    add_name_metrics: bool = True,
    overwrite: bool = True,
) -> dict:
    """
    Given a FHIR bundle and a type of standardization to perform,
    transform all names in all patients in the bundle. The default
    standardization behavior is our defined non-numeric, space-trimming,
    full capitalization standardization, but other modes may be specified.
    Also, augment the patient resources with metrics information about
    whether standardization improved the quality of any names, if
    desired.

    :param bundle: The FHIR bundle to standardize patients in
    :param standardization_mode: The type of standardization to perform.
        Options include: "non_numeric_caps"
    :param add_name_metrics: Whether to store tracking data about
        if any names were changed in the patient resources
    :param overwrite: Whether to overwrite the original data with
        the transformed values. Default is yes.
    :return: The bundle with all patients having transformed names
    """
    # Copy the data if we don't want to overwrite the origina
    if not overwrite:
        bundle = copy.deepcopy(bundle)

    # Handle all patients individually
    for resource in find_patient_resources(bundle):
        patient = resource.get("resource")
        if standardization_mode == "non_numeric_caps":
            standardize_names_for_patient(
                patient, non_numeric_caps_standardization, add_name_metrics
            )
        else:
            raise ValueError("Invalid standardization mode supplied.")
    return bundle


def standardize_names_for_patient(
    patient: dict,
    transform_func: Callable = non_numeric_caps_standardization,
    add_metrics_extensions: bool = True,
) -> None:
    """
    Helper method to standardize all names associated with a single patient.
    Receives a particular standardization function from the calling method
    standardize_patient_names. Default behavior is to use the simple
    non-numeric, space-trimming, full capitalization standardization.

    :param patient: The Patient resource to standardize all names for
    :param transform_func: The particular standardization function
        to invoke for these transforms
    :param add_metrics_extensions: Whether to store values in the patient
        extension array for if our standardization functions transformed the names
        to different values than their raw strings
    """

    # Can track name changes with logical ORs each time a name is updated
    family_name_altered = False
    given_name_altered = False

    for name in patient.get("name", []):

        # Handle family names
        if "family" in name:
            transformed_name = transform_func(name.get("family", ""))
            family_name_altered = family_name_altered or (
                transformed_name != name.get("family", "")
            )
            name["family"] = transformed_name

        # Given names are stored in a list, as there could be multiple,
        # so process them all and take the overall diff for metrics
        if "given" in name:
            transformed_names = [transform_func(g) for g in name.get("given", [])]
            given_name_altered = any(
                [
                    name.get("given", [])[i] != transformed_names[i]
                    for i in range(len(name.get("given", [])))
                ]
            )
            name["given"] = transformed_names

    if add_metrics_extensions:
        add_name_change_metrics_values(patient, given_name_altered, family_name_altered)


def add_name_change_metrics_values(
    patient: dict, given_name_was_changed: bool, family_name_was_changed: bool
) -> None:
    """
    Add information about whether a patient's given or family name was
    changed through the use of our standardization function directly
    to the patient resource as an extension. We define a pseudo-FHIR standard
    URL for this purpose.

    :param patient: The Patient to add data for
    :param given_name_was_changed: Did the transforms standardize
        the given name string to something different than the raw form
    :param family_name_was_Changed: Did the transforms standardize
        the family name string to something different than the raw form
    """
    # Add in the tracking array for extra properties, if not there
    if "extension" not in patient:
        patient["extension"] = []

    patient["extension"].append(
        {
            "url": "http://usds.gov/fhir/phdi/StructureDefinition/given-name-was-standardized",  # noqa
            "valueBoolean": given_name_was_changed,
        }
    )
    patient["extension"].append(
        {
            "url": "http://usds.gov/fhir/phdi/StructureDefinition/family-name-was-standardized",  # noqa
            "valueBoolean": family_name_was_changed,
        }
    )


def country_extractor(
    patient: dict, code_type: Literal["alpha_2", "alpha_3", "numeric"] = "alpha_2"
) -> List[str]:
    """
    Given a patient, build a list containing all of the counries found in the
    patient's addresses in a standard form sepcified by code_type.

    :param patient: A patient from a FHIR resource
    :param code_type: A string equal to 'alpha_2', 'alpha_3', or 'numeric' to
        specify which type of standard country identifier to generate
    :return: A list containing country codes as specified by code_type
        for each country found in resource.
    """
    countries = []
    for address in patient.get("address"):
        country = address.get("country")
        countries.append(standardize_country(country, code_type))
    return countries


def phone_country_standardization(raw: str, countries: List = [None, "US"]) -> str:
    """
    Given a phone number and optionally an associated FHIR resource and country
    extraction function if able to parse the phone number return it in the E.164
    standardard international format. If the phone number is not parseable return none.

    Phone number parsing process:
    A maximum of three attemtps are made to parse any phone number.
    First, we try to parse the phone number without any additional country information.
    If this succeeds then the phone number must have been provided in a standard
    inernational format which is the ideal case. If the first attempt fails and a list
    of country codes indicating possible countries of origin for the phone number has
    been provided we attempt to parse the phone number using that additional country
    information from the resource. Finally, in the case where the second attempt fails
    or a list of countries has not been provided we make a final attempt to parse the
    number assuming it is American.

    :param raw: Raw phone number to be standardized.
    :param countries: A list containing 2 letter ISO country codes for each country
        extracted from resource of the phone number to be standardized that might indicate
        it the phone numbers country of origin.
    :return: The standardized phone number in E.164 format when the raw
        phone number was succesfully parsed and an emptry string otherwise.
    """

    if countries != [None, "US"]:
        countries = [None] + countries + ["US"]

    standardized = ""
    for country in countries:
        try:
            standardized = phonenumbers.parse(raw, country)
            break
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
    raw: str, code_type: Literal["alpha_2", "alpha_3", "numeric"] = "alpha_2"
) -> str:
    """
    Given a country return it in a standard form as specified by code_type.

    :param raw: Country to be standardized.
    :param code_type: A string equal to 'alpha_2', 'alpha_3', or 'numeric' to
        specify which type of standard country identifier to generate.
    :return: Country in standardized form, or None if unable to
        standardize.
    """
    standard = None
    raw = raw.strip().upper()
    if len(raw) == 2:
        standard = pycountry.countries.get(alpha_2=raw)
    elif len(raw) == 3:
        standard = pycountry.countries.get(alpha_3=raw)
        if standard is None:
            standard = pycountry.countries.get(numeric=raw)
    elif len(raw) >= 4:
        standard = pycountry.countries.get(name=raw)
        if standard is None:
            standard = pycountry.countries.get(official_name=raw)

    if standard is not None:
        if code_type == "alpha_2":
            standard = standard.alpha_2
        elif code_type == "alpha_3":
            standard = standard.alpha_3
        elif code_type == "numeric":
            standard = standard.numeric

    return standard


def phone_truncation_standardization(raw_phone: str, *args) -> str:
    """
    Truncate a given phone number string to exactly ten digits, after
    removing any special characters. For example,
    standardize_phone("(555) 555-1212") would return '5555551212'. If
    the provided phone number is less than ten digits, then the
    function simply returns None, as this is not a valid phone number.

    :param raw_phone: The phone number to standardize
    :return: The truncated phone number
    """
    raw_phone = [x for x in raw_phone if x.isnumeric()]
    raw_phone = "".join(raw_phone)
    if len(raw_phone) < 10:
        raw_phone = None
    elif len(raw_phone) > 10:
        raw_phone = raw_phone[:10]
    return raw_phone


def standardize_all_phones(
    bundle: dict,
    standardization_mode: str = "truncation",
    add_phone_metrics: bool = True,
    overwrite: bool = True,
) -> dict:
    """
    Given a FHIR bundle and a type of phone number standardization,
    transform all phone numberes for all patient resources in the
    bundle. The default mode of standardization is "truncation". Also,
    optionally store tracking data around whether any phone numbers
    were transformed in an extension array directly on the patient.

    :param bundle: The FHIR bundle to standardize patients in
    :param standardization_mode: The type of standardization to
        perform. Valid options include: "truncation"
    :param add_phone_metrics: Whether to store tracking metrics
        for changed phone numbers. Default is yes.
    :param overwrite: Whether to overwrite the original data
        with the transformed values. Default is yes.
    :return: The bundle with all phone numbers transformed
    """
    if not overwrite:
        bundle = copy.deepcopy(bundle)
    for resource in find_patient_resources(bundle):
        patient = resource.get("resource")
        if standardization_mode == "truncation":
            standardize_phone_numbers_for_patient(
                patient, phone_truncation_standardization, add_phone_metrics
            )
        elif standardization_mode == "country":
            standardize_phone_numbers_for_patient(
                patient, phone_country_standardization, add_phone_metrics
            )
        else:
            raise ValueError("Invalid standardization mode supplied.")
    return bundle


def standardize_phone_numbers_for_patient(
    patient: dict,
    transform_func: Callable = phone_truncation_standardization,
    add_metrics_extensions: bool = True,
) -> None:
    """
    Helper method to standardize all phone numbers in a single patient
    resource using the caller-supplied transformation function. Also,
    optionally add extensions for metrics tracking around whether any
    phone numbers were different after standardization.

    :param patient: The patient to standardize all numbers for
    :param transform_func: The specific standardization
        function to invoke on the numbers. Default behavior is truncation
        standardization.
    :param add_metrics_extensions: Whether to add tracking data in
        our pseud-FHIR-standard extensions around if any numbers were changed.
        Default behavior is yes, do this.
    """
    # We can determine if phones were altered by using logical ORs
    phone_was_altered = False
    for telecom in patient.get("telecom", []):
        if telecom.get("system") == "phone" and "value" in telecom:

            # Transform the number and check if it's different
            countries = country_extractor(patient)
            transformed_phone = transform_func(telecom.get("value", ""), countries)
            phone_was_altered = phone_was_altered or (
                transformed_phone != telecom.get("value", "")
            )
            telecom["value"] = transformed_phone

    # Store the tracking in an extension array, if desired
    if add_metrics_extensions:
        if "extension" not in patient:
            patient["extension"] = []
        patient["extension"].append(
            {
                "url": "http://usds.gov/fhir/phdi/StructureDefinition/phone-was-standardized",  # noqa
                "valueBoolean": phone_was_altered,
            }
        )
