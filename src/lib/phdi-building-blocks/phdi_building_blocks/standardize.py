from phdi_building_blocks.utils import find_patient_resources
from typing import Callable
import copy


def non_numeric_caps_standardization(raw_name: str) -> str:
    """
    Perform standardization on a provided name string. Name
    standardization performs:
    - removal of all numeric characters
    - trimming of extra whitespace
    - converting all characters to uppercase
    For example, standardize_name(" JohN Doe ") is 'JOHN DOE'.
    :param str raw: The raw string to standardize
    :return: The standardized name string
    :rtype: str
    """
    raw_name = [x for x in raw_name if not x.isnumeric()]
    raw_name = "".join(raw_name)
    raw_name = raw_name.upper()
    raw_name = raw_name.strip()
    return raw_name


def standardize_patient_names_in_bundle(
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
    :param dict bundle: The FHIR bundle to standardize patients in
    :param str standardization_mode: The type of standardization to perform.
    Options include: "non_numeric_caps"
    :param bool add_name_metrics: Whether to store tracking data about
    if any names were changed in the patient resources
    :param bool overwrite: Whether to overwrite the original data with
    the transformed values. Default is yes.
    :return: The bundle with all patients having transformed names
    :rtype: dict
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
    standardize_patient_names_in_bundle. Default behavior is to use the simple
    non-numeric, space-trimming, full capitalization standardization.
    :param dict patient: The Patient resource to standardize all names for
    :param Callable transform_func: The particular standardization function
    to invoke for these transforms
    :param bool add_metrics_extensions: Whether to store values in the patient
    extension array for if our standardization functions transformed the names
    to different values than their raw strings
    :return: None
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
    :param dict patient: The Patient to add data for
    :param bool given_name_was_changed: Did the transforms standardize
    the given name string to something different than the raw form
    :param bool family_name_was_Changed: Did the transforms standardize
    the family name string to something different than the raw form
    :return: None
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


def phone_truncation_standardization(raw_phone: str) -> str:
    """
    Truncate a given phone number string to exactly ten digits, after
    removing any special characters. For example,
    standardize_phone("(555) 555-1212") would return '5555551212'. If
    the provided phone number is less than ten digits, then the
    function simply returns None, as this is not a valid phone number.
    :param str raw_phone: The phone number to standardize
    :return: The truncated phone number
    :rtype: str
    """
    raw_phone = [x for x in raw_phone if x.isnumeric()]
    raw_phone = "".join(raw_phone)
    if len(raw_phone) < 10:
        raw_phone = None
    elif len(raw_phone) > 10:
        raw_phone = raw_phone[:10]
    return raw_phone


def standardize_all_phones_in_bundle(
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
    :param dict bundle: The FHIR bundle to standardize patients in
    :param str standardization_mode: The type of standardization to
    perform. Valid options include: "truncation"
    :param bool add_phone_metrics: Whether to store tracking metrics
    for changed phone numbers. Default is yes.
    :param bool overwrite: Whether to overwrite the original data
    with the transformed values. Default is yes.
    :return: The bundle with all phone numbers transformed
    :rtype: dict
    """
    if not overwrite:
        bundle = copy.deepcopy(bundle)
    for resource in find_patient_resources(bundle):
        patient = resource.get("resource")
        if standardization_mode == "truncation":
            standardize_phone_numbers_for_patient(
                patient, phone_truncation_standardization, add_phone_metrics
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
    :param dict patient: The patient to standardize all numbers for
    :param Callable transform_func: The specific standardization
    function to invoke on the numbers. Default behavior is truncation
    standardization.
    :param bool add_metrics_extensions: Whether to add tracking data in
    our pseud-FHIR-standard extensions around if any numbers were changed.
    Default behavior is yes, do this.
    :return: None
    """
    # We can determine if phones were altered by using logical ORs
    phone_was_altered = False
    for telecom in patient.get("telecom", []):
        if telecom.get("system") == "phone" and "value" in telecom:

            # Transform the number and check if it's different
            transformed_phone = transform_func(telecom.get("value", ""))
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
