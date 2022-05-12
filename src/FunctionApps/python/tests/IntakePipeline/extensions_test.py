import pytest
from unittest import mock
import json
import pathlib

from phdi_building_blocks.geo import GeocodeResult, geocode_patient_address
from phdi_building_blocks.name_standardization import standardize_patient_name
from phdi_building_blocks.phone_standardization import standardize_patient_phone


@pytest.fixture()
def bundle():
    return json.load(
        open(pathlib.Path(__file__).parent / "assets" / "patient_bundle.json")
    )


@mock.patch("phdi_building_blocks.geo.geocode")
def test_add_extensions_to_patient(patched_geocode, bundle):
    patched_geocode.return_value = GeocodeResult(
        key="123 Fake St New York, NY 10001",
        address=["123 FAKE ST", "UNIT 3"],
        city="NEW YORK",
        state="NY",
        zipcode="10001",
        fips="36061",
        lat=45.123,
        lng=-70.234,
        county_fips="dunno",
        county_name="no idea",
        precision="close-ish",
    )

    expected_extensions = [
        {
            "url": "http://usds.gov/fhir/phdi/StructureDefinition/family-name-was-standardized",  # noqa
            "valueBoolean": False,
        },
        {
            "url": "http://usds.gov/fhir/phdi/StructureDefinition/given-name-was-standardized",  # noqa
            "valueBoolean": True,
        },
        {
            "url": "http://usds.gov/fhir/phdi/StructureDefinition/phone-was-standardized",  # noqa
            "valueBoolean": True,
        },
        {
            "url": "http://usds.gov/fhir/phdi/StructureDefinition/address-was-standardized",  # noqa
            "valueBoolean": True,
        },
    ]

    standardize_patient_name(bundle)
    standardize_patient_phone(bundle)
    geocode_patient_address(bundle, mock.Mock())
    assert (
        bundle.get("entry")[1].get("resource").get("extension") == expected_extensions
    )
