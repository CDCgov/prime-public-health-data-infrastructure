import json
import pathlib
import copy

from phdi_building_blocks.standardize import (
    non_numeric_caps_standardization,
    standardize_patient_names_in_bundle,
    phone_truncation_standardization,
    standardize_all_phones_in_bundle,
)


def test_standardize_name():
    assert "JOHN DOE" == non_numeric_caps_standardization(" JOHN DOE ")
    assert "JOHN DOE" == non_numeric_caps_standardization(" John Doe3 ")


def test_standardize_patient_name():
    raw_bundle = json.load(
        open(pathlib.Path(__file__).parent / "assets" / "patient_bundle.json")
    )
    standardized_bundle = copy.deepcopy(raw_bundle)
    patient = standardized_bundle["entry"][1]["resource"]
    patient["name"][0]["family"] = "DOE"
    patient["name"][0]["given"] = ["JOHN", "DANGER"]
    patient["extension"] = []
    patient["extension"].append(
        {
            "url": "http://usds.gov/fhir/phdi/StructureDefinition/given-name-was-standardized",  # noqa
            "valueBoolean": True,
        }
    )
    patient["extension"].append(
        {
            "url": "http://usds.gov/fhir/phdi/StructureDefinition/family-name-was-standardized",  # noqa
            "valueBoolean": True,
        }
    )
    assert standardize_patient_names_in_bundle(raw_bundle) == standardized_bundle


def test_standardize_phone():
    assert "0123456789" == phone_truncation_standardization("0123456789")
    assert "0123456789" == phone_truncation_standardization("(012)345-6789")
    assert "0123456789" == phone_truncation_standardization("01234567899876543210")
    assert phone_truncation_standardization("345-6789") is None


def test_standardize_patient_phone():
    raw_bundle = json.load(
        open(pathlib.Path(__file__).parent / "assets" / "patient_bundle.json")
    )
    standardized_bundle = copy.deepcopy(raw_bundle.copy())
    patient = standardized_bundle["entry"][1]["resource"]
    patient["telecom"][0]["value"] = "1234567890"
    patient["extension"] = []
    patient["extension"].append(
        {
            "url": "http://usds.gov/fhir/phdi/StructureDefinition/phone-was-standardized",  # noqa
            "valueBoolean": True,
        }
    )
    assert standardize_all_phones_in_bundle(raw_bundle) == standardized_bundle
