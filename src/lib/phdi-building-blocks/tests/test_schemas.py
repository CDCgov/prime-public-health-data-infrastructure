import json
import yaml
import pathlib

from phdi_building_blocks.schemas import (
    load_schema,
    apply_selection_criteria,
    apply_schema_to_resource,
)


def test_load_schema():
    load_schema(
        pathlib.Path(__file__).parent / "assets" / "test_schema.yaml"
    ) == yaml.safe_load(
        open(pathlib.Path(__file__).parent / "assets" / "test_schema.yaml")
    )


def test_apply_selection_criteria():
    test_list = ["one", "two", "three"]
    assert apply_selection_criteria(test_list, "first") == "one"
    assert apply_selection_criteria(test_list, "last") == "three"
    assert apply_selection_criteria(test_list, "random") in test_list
    assert apply_selection_criteria(test_list, "all") == ",".join(test_list)


def test_apply_schema_to_resource():
    resource = json.load(
        open(pathlib.Path(__file__).parent / "assets" / "patient_bundle.json")
    )

    resource = resource["entry"][1]["resource"]

    schema = yaml.safe_load(
        open(pathlib.Path(__file__).parent / "assets" / "test_schema.yaml")
    )
    schema = schema["my_table"]

    assert apply_schema_to_resource(resource, schema) == {
        "patient_id": "some-uuid",
        "first_name": "John ",
        "last_name": "doe",
        "phone_number": "123-456-7890",
    }
