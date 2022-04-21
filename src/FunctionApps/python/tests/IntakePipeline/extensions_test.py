import pytest
from unittest import mock

import json
import pathlib

from phdi_transforms.geo import GeocodeResult

from IntakePipeline.transform import find_patient_resources, transform_bundle


@pytest.fixture()
def bundle():
    return json.load(
        open(pathlib.Path(__file__).parent / "assets" / "patient_bundle.json")
    )


@mock.patch("IntakePipeline.transform.geocode")
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
    patient = find_patient_resources(bundle)[0]

    expected = {
        "resourceType": "Patient",
        "id": "some-uuid",
        "identifier": patient.get("resource").get("identifier"),
        "name": [{"family": "DOE", "given": ["JOHN", "DANGER"], "use": "official"}],
        "telecom": [
            {"system": "phone", "use": "home", "value": None},
            {"system": "email", "value": "johndanger@doe.net"},
        ],
        "birthDate": "1983-02-01",
        "gender": "female",
        "address": [
            {
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                        "extension": [
                            {"url": "latitude", "valueDecimal": 45.123},
                            {"url": "longitude", "valueDecimal": -70.234},
                        ],
                    },
                ],
                "line": ["123 FAKE ST", "UNIT 3"],
                "city": "NEW YORK",
                "state": "NY",
                "postalCode": "10001",
                "country": "USA",
                "use": "home",
            }
        ],
        "extension": [
            {
                "url": "http://usds.gov/fhir/phdi/StructureDefinition/family-name-was-standardized",
                "valueBoolean": False,
            },
            {
                "url": "http://usds.gov/fhir/phdi/StructureDefinition/given-name-was-standardized",
                "valueBoolean": True,
            },
            {
                "url": "http://usds.gov/fhir/phdi/StructureDefinition/phone-was-standardized",
                "valueBoolean": True,
            },
            {
                "url": "http://usds.gov/fhir/phdi/StructureDefinition/address-was-standardized",
                "valueBoolean": True,
            },
        ],
    }

    transform_bundle(mock.Mock(), bundle, add_std_extension=True)
    assert bundle.get("entry")[1].get("resource") == expected
