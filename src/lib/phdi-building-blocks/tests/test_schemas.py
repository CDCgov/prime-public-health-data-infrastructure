import json
from os import access
import yaml
import pathlib
from unittest import mock

from phdi_building_blocks.schemas import (
    load_schema,
    apply_selection_criteria,
    apply_schema_to_resource,
    make_resource_type_table,
    make_tables_from_schema,
    write_schema_table,
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
@mock.patch("phdi_building_blocks.schemas.fhir_server_get")
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
    fhir_url = "some_fhir_server_url"
    access_token = "some_access_token"

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
        fhir_url,
        access_token,
    )

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


@mock.patch("phdi_building_blocks.schemas.write_schema_table")
@mock.patch("phdi_building_blocks.schemas.fhir_server_get")
def test_make_resource_type_table_fail(patch_query, patch_write):

    resource_type = "some_resource_type"

    schema = {}

    output_path = mock.Mock()
    output_path.__truediv__ = (  # Redefine division operator to prevent failure.
        lambda x, y: x
    )

    output_format = "parquet"

    fhir_url = "some_fhir_server_url"
    access_token = "some_access_token"

    response = mock.Mock()
    response.status_code = 400
    patch_query.return_value = response

    make_resource_type_table(
        resource_type,
        schema,
        output_path,
        output_format,
        fhir_url,
        access_token,
    )

    assert len(patch_write.call_args_list) == 0


@mock.patch("phdi_building_blocks.schemas.make_resource_type_table")
@mock.patch("phdi_building_blocks.schemas.load_schema")
def test_make_tables_from_schema(patched_load_schema, patched_make_resource_type_table):

    schema_path = mock.Mock()
    output_path = mock.Mock()
    output_path.__truediv__ = (  # Redefine division operator to prevent failure.
        lambda x, y: x
    )
    output_format = "parquet"
    fhir_url = "some_fhir_url"
    access_token = "some_access_token"

    schema = yaml.safe_load(
        open(pathlib.Path(__file__).parent / "assets" / "test_schema.yaml")
    )

    patched_load_schema.return_value = schema

    make_tables_from_schema(
        schema_path, output_path, output_format, fhir_url, access_token
    )

    patched_make_resource_type_table.assert_called_with(
        "Patient",
        schema["my_table"],
        output_path,
        output_format,
        fhir_url,
        access_token,
    )


@mock.patch("phdi_building_blocks.schemas.pq.ParquetWriter")
@mock.patch("phdi_building_blocks.schemas.pa.Table")
def test_write_schema_table_no_writer(patched_pa_table, patched_writer):

    data = [{"some_column": "some value", "some_other_column": "some other value"}]
    output_file_name = mock.Mock()
    file_format = "parquet"

    write_schema_table(data, output_file_name, file_format)
    patched_pa_table.from_pylist.assert_called_with(data)
    table = patched_pa_table.from_pylist(data)
    patched_writer.assert_called_with(output_file_name, table.schema)
    patched_writer(output_file_name, table.schema).write_table.assert_called_with(
        table=table
    )


@mock.patch("phdi_building_blocks.schemas.pq.ParquetWriter")
@mock.patch("phdi_building_blocks.schemas.pa.Table")
def test_write_schema_table_with_writer(patched_pa_table, patched_writer):

    data = [{"some_column": "some value", "some_other_column": "some other value"}]
    output_file_name = mock.Mock()
    file_format = "parquet"
    writer = mock.Mock()

    write_schema_table(data, output_file_name, file_format, writer)
    patched_pa_table.from_pylist.assert_called_with(data)
    table = patched_pa_table.from_pylist(data)
    writer.write_table.assert_called_with(table=table)
    assert len(patched_writer.call_args_list) == 0
