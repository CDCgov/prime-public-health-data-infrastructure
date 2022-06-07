import json
import yaml
import pathlib
from unittest import mock

from phdi_building_blocks.schemas import (
    load_schema,
    apply_selection_criteria,
    apply_schema_to_resource,
    make_resource_type_table,
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


@mock.patch("phdi_building_blocks.schemas.write_schema_table")
@mock.patch("phdi_building_blocks.schemas.query_fhir_server")
def test_make_resource_type_table_success(patch_query, patch_write):

    resource_type = "some_resource_type"

    schema = yaml.safe_load(
        open(pathlib.Path(__file__).parent / "assets" / "test_schema.yaml")
    )

    output_path = mock.Mock()
    output_path.__truediv__ = (  # Redefine division operator to prevent failure.
        lambda x, y: x
    )

    output_format = "parquet"

    credential_manager = mock.Mock()

    fhir_server_responses = json.load(
        open(
            pathlib.Path(__file__).parent
            / "assets"
            / "FHIR_server_query_response_200_example.json"
        )
    )

    query_response_1 = mock.Mock()
    query_response_1.status_code = fhir_server_responses["status_code_1"]
    query_response_1.content = json.dumps(fhir_server_responses["content_1"])

    query_response_2 = mock.Mock()
    query_response_2.status_code = fhir_server_responses["status_code_2"]
    query_response_2.content = json.dumps(fhir_server_responses["content_2"])

    patch_query.side_effect = [query_response_1, query_response_2]

    make_resource_type_table(
        resource_type,
        schema["my_table"],
        output_path,
        output_format,
        credential_manager,
    )
    writer = mock.Mock()

    assert len(patch_write.call_args_list[0]) == 2

    assert patch_write.call_args_list[0][0] == (
        [
            apply_schema_to_resource(
                fhir_server_responses["content_1"]["entry"][0]["resource"],
                schema["my_table"],
            )
        ],
        output_path,
        output_format,
        None,
    )
    assert patch_write.call_args_list[1][0] == (
        [
            apply_schema_to_resource(
                fhir_server_responses["content_2"]["entry"][0]["resource"],
                schema["my_table"],
            )
        ],
        output_path,
        output_format,
        patch_write(
            (
                [
                    apply_schema_to_resource(
                        fhir_server_responses["content_1"]["entry"][0]["resource"],
                        schema["my_table"],
                    )
                ],
                output_path,
                output_format,
                None,
            )
        ),
    )


@mock.patch("phdi_building_blocks.schemas.log_fhir_server_error")
@mock.patch("phdi_building_blocks.schemas.query_fhir_server")
def test_make_resource_type_table_fail(patch_query, patch_logger):

    resource_type = "some_resource_type"

    schema = {}

    output_path = mock.Mock()
    output_path.__truediv__ = (  # Redefine division operator to prevent failure.
        lambda x, y: x
    )

    output_format = "parquet"

    credential_manager = mock.Mock()

    fhir_server_responses = json.load(
        open(
            pathlib.Path(__file__).parent
            / "assets"
            / "FHIR_server_query_response_200_example.json"
        )
    )

    response = mock.Mock()
    response.status_code = 400
    patch_query.return_value = response

    make_resource_type_table(
        resource_type,
        schema,
        output_path,
        output_format,
        credential_manager,
    )

    patch_logger.assert_called_once_with(response.status_code)
