from phdi_building_blocks.utils import find_patient_resources, get_one_line_address

from smartystreets_python_sdk import StaticCredentials, ClientBuilder
from smartystreets_python_sdk import us_street
from smartystreets_python_sdk.us_street.lookup import Lookup

from typing import Tuple, Union
import copy

from phdi_building_blocks.classes.geocode_result import GeocodeResult


def get_geocoder_result(
    client: us_street.Client, address: str
) -> Union[GeocodeResult, None]:
    """
    Given an API client and an address, attempt to call the smartystreets API
    and use our wrapper class to return a succinctly encapsulated result. If
    a valid result is found, it will be returned. Otherwise, the function
    returns None.
    :param us_street.Client client: the SmartyStreets API Client suitable
    for use with street addresses in the US
    :param str address: The address to perform a geocoding lookup for
    :return: The geocoded result wrapped in our result class, or None
    :rtype: GeocodeResult, or None
    """

    # Make the API call
    lookup = Lookup(street=address)
    client.send_lookup(lookup)

    # Valid responses have results with lat/long
    if lookup.result and lookup.result[0].metadata.latitude:
        smartystreets_result = lookup.result[0]
        coded_address = [smartystreets_result.delivery_line_1]
        if smartystreets_result.delivery_line_2:
            coded_address.append(smartystreets_result.delivery_line_2)

        return GeocodeResult(
            address=coded_address,
            city=smartystreets_result.components.city_name,
            state=smartystreets_result.components.state_abbreviation,
            zipcode=smartystreets_result.components.zipcode,
            county_fips=smartystreets_result.metadata.county_fips,
            county_name=smartystreets_result.metadata.county_name,
            lat=smartystreets_result.metadata.latitude,
            lng=smartystreets_result.metadata.longitude,
            precision=smartystreets_result.metadata.precision,
        )

    return


def get_smartystreets_client(auth_id: str, auth_token: str) -> us_street.Client:
    """
    Build a smartystreets api client from an auth id and token.
    :param str auth_id: Authentication ID to build the client with
    :param str auth_token: The token that allows us to access the client
    :return: Built smartystreets API client
    :rtype: us_street.Client
    """

    creds = StaticCredentials(auth_id, auth_token)
    return (
        ClientBuilder(creds)
        .with_licenses(["us-standard-cloud"])
        .build_us_street_api_client()
    )


def geocode_patients_in_bundle(
    bundle: dict,
    client: us_street.Client,
    add_address_metrics: bool = True,
    overwrite: bool = True,
) -> dict:
    """
    Given a FHIR bundle and a SmartyStreets client, geocode all patient addresses
    across all patient resources in the bundle. The function makes a deep copy
    of the data before operating so that the source data is unchanged and the
    new standardized bundle may be passed by value to other building blocks.
    :param dict bundle: A FHIR resource bundle
    :param us_street.Client client: The smartystreets API client to geocode
    with
    :param bool add_address_metrics: Whether to add tracking information into
    the patient resource denoting whether one or more addresses were
    standardized
    :param bool overwrite: Whether to write the new standardizations directly
    into the given bundle, changing the original data (True is yes)
    :return: The standardized bundle of data
    :rtype: dict
    """
    # Copy the data if we don't want to alter the original
    if not overwrite:
        bundle = copy.deepcopy(bundle)

    # Standardize each patient in turn
    for resource in find_patient_resources(bundle):
        patient = resource.get("resource")
        standardize_addresses_for_patient(patient, client, add_address_metrics)
    return bundle


def geocode_single_address(
    client: us_street.Client, address: dict
) -> Tuple[GeocodeResult, bool]:
    """
    Helper method to perform geocoding on a single address from a patient
    resource. Here, the address is expressed in dictionary form, as it comes
    straight out of a FHIR bundle. This function also determines whether the
    geocoded standardized address is different from the raw address.
    :param us_street.Client client: The API client to geocode with
    :param dict address: A patient's address in FHIR / JSON
    :return: Tuple containing the standardized geocoding result as well as
    whether the information in the result is different than the information
    held in the raw address
    :rtype: Tuple[GeocodeResult, bool]
    """

    raw_one_line = get_one_line_address(address)
    geocoded_result = get_geocoder_result(client, raw_one_line)

    # Determine if standardized result is different from raw data
    # Default assumption is addresses are same, in case there's no
    # valid geocoder result
    address_is_different = False
    if geocoded_result:
        std_one_line = f"{geocoded_result.address} {geocoded_result.city}, {geocoded_result.state} {geocoded_result.zipcode}"  # noqa
        address_is_different = raw_one_line != std_one_line

    return (geocoded_result, address_is_different)


def standardize_addresses_for_patient(
    patient: dict, client: us_street.Client, add_metrics_extension: bool = True
) -> None:
    """
    Helper function to handle the standardizing of all addresses belonging to
    a single patient in a FHIR resource bundle. This function also determines
    whether any of that patient's addresses were improved through geocoding and
    tracks this in an extension on the patient profile.
    :param dict patient: A Patient resource FHIR profile
    :param us_street.Client client: The API client to geocode with
    :param bool add_metrics_extension: Whether to add tracking metrics into the
    patient resource denoting that one or more addresses was standardized.
    :return: None
    """

    # We can track whether geocoding improved addresses by taking the logical
    # OR everytime we geocode a new address
    any_address_was_changed = False
    for address in patient.get("address", []):
        standardized_address, address_is_different = geocode_single_address(
            client, address
        )
        any_address_was_changed = any_address_was_changed or address_is_different

        # Update fields with new, standardized information
        if standardized_address:
            address["line"] = standardized_address.address
            address["city"] = standardized_address.city
            address["state"] = standardized_address.state
            address["postalCode"] = standardized_address.zipcode

            # Need an extension to track lat/long
            if "extension" not in address:
                address["extension"] = []
            address["extension"].append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                    "extension": [
                        {
                            "url": "latitude",
                            "valueDecimal": standardized_address.lat,
                        },
                        {
                            "url": "longitude",
                            "valueDecimal": standardized_address.lng,
                        },
                    ],
                }
            )

    # Need an extension to track whether geocoding improved any addresses
    if add_metrics_extension:
        if "extension" not in patient:
            patient["extension"] = []
        patient["extension"].append(
            {
                "url": "http://usds.gov/fhir/phdi/StructureDefinition/address-was-standardized",  # noqa
                "valueBoolean": any_address_was_changed,
            }
        )
