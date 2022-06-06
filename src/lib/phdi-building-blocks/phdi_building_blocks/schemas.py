import pathlib
import os
import yaml
import json
import random
from typing import Literal, List
import pyarrow as pa
import pyarrow.parquet as pq
from fhirpathpy import evaluate

from phdi_building_blocks.fhir import (
    AzureFhirserverCredentialManager,
    query_fhir_server,
    log_fhir_server_error,
)


def load_schema(path: str) -> dict:
    """
    Given the path to local YAML files containing a user-defined schema read the file
    and return the schema as a dictionary.

    :param str path: Path specifying the location of a YAML file containing a schema.
    :return dict schema: A user-defined schema
    """

    with open(path, "r") as file:
        schema = yaml.safe_load(file)
    return schema


def apply_selection_criteria(
    value: list,
    selection_criteria: Literal["first", "last", "random", "all"],
) -> str:
    """
    Given a list of value parsed from a FHIR resource and selection criteria return a
    single value.

    :param value: A list containing the values stored in a top level key in a FHIR
    resource.
    :param selection_criteria: A string indicating which element of list to select
    when one is encountered during parsing.
    """

    if selection_criteria == "first":
        value = value[0]
    elif selection_criteria == "last":
        value = value[-1]
    elif selection_criteria == "random":
        value = random.choice(value)
    elif selection_criteria == "all":
        value = value

    # Temporary hack to ensure no structured data is written using pyarrow.
    # Currently Pyarrow does no support mixing non structure and structured data.
    # https://github.com/awslabs/aws-data-wrangler/issues/463
    # Will need to consider other methods of writing to parquet if this is and essential
    # feature.
    if type(value) == dict:
        value = json.dumps(value)
    elif type(value) == list:
        value = ",".join(value)
    return value


def apply_schema_to_resource(resource: dict, schema: dict) -> dict:
    """
    Given a resource and a schema return a dictionary with values of the data
    specified by the schema and associated keys defined by the variable name provided
    by the schema.

    :param dict resource: A FHIR resource on which to apply a schema.
    :param dict schema: A schema specifying the desired values by FHIR resource type.
    :return dict data: A dictionary containing the data extracted from the patient along
    with specified variable names.
    """

    data = {}
    resource_schema = schema.get(resource.get("resourceType", ""))
    if resource_schema is None:
        return data
    for field in resource_schema.keys():

        path = resource_schema[field]["fhir_path"]
        value = evaluate(resource, path)

        if len(value) == 0:
            data[resource_schema[field]["new_name"]] = ""
        else:
            selection_criteria = resource_schema[field]["selection_criteria"]
            value = apply_selection_criteria(value, selection_criteria)
            data[resource_schema[field]["new_name"]] = value

    return data


def make_resource_type_table(
    resource_type: str,
    schema: dict,
    output_path: pathlib.PosixPath,
    output_format: Literal["parquet"],
    credential_manager: AzureFhirserverCredentialManager,
):
    """
    Given a FHIR resource type, schema, and FHIR server credential manager create a
    table containing the field from resource type specified in the the schema.

    :param str resource_type: A FHIR resource type.
    :param dict schema: A schema specifying the desired values by FHIR resource type.
    :param AzureFhirserverCredentialManager credential_manager: A credential manager for
    a FHIR server.
    """

    output_path.mkdir(parents=True, exist_ok=True)
    output_file_name = output_path / f"{resource_type}.{output_format}"

    query = f"/{resource_type}"
    response = query_fhir_server(credential_manager, query)

    additional_page = True
    writer = None
    while additional_page:
        if response.status_code != 200:
            log_fhir_server_error(response.status_code)
            break

        # Load queried data.
        query_result = json.loads(response.content)
        raw_schema_data = []

        # Extract values specified by schema from each resource.
        for resource in query_result["entry"]:
            values_from_resource = apply_schema_to_resource(
                resource["resource"], schema
            )
            if values_from_resource != {}:
                raw_schema_data.append(values_from_resource)

        # Write data to parquet
        writer = write_schema_table(
            raw_schema_data, output_file_name, output_format, writer
        )

        # Check for an additional page of query results.
        for link in query_result.get("link"):
            if link.get("relation") == "next":
                next_page_url = link.get("url")
                response = query_fhir_server(
                    credential_manager, specific_url=next_page_url
                )
                break
            else:
                response = None

        if response is None:
            additional_page = False
    if writer is not None:
        writer.close()


def generate_schema(
    fhir_url: str,
    schema_path: pathlib.PosixPath,
    output_path: pathlib.PosixPath,
    output_format: Literal["parquet"],
):
    """
    Given the url for a FHIR server, the location of a schema file, and and output
    directory generate the specified schema and store the tables in the desired
    location.
    """
    schema = load_schema(schema_path)
    schema_name = list(schema.keys())[0]
    schema = schema[schema_name]
    output_path = pathlib.Path(schema_name)

    credential_manager = AzureFhirserverCredentialManager(fhir_url)

    for resource_type in schema.keys():
        make_resource_type_table(
            resource_type, schema, output_path, output_format, credential_manager
        )


def write_schema_table(
    data: List[dict],
    output_file_name: pathlib.PosixPath,
    file_format: Literal["parquet"],
    writer: pq.ParquetWriter = None,
):
    """
    Write schema data to a file given the data, a path to the file including the file
    name, and the file format.
    """

    if file_format == "parquet":
        table = pa.Table.from_pylist(data)
        if writer is None:
            writer = pq.ParquetWriter(output_file_name, table.schema)
        writer.write_table(table=table)
        return writer


def get_schema_summary(schema_directory: pathlib.PosixPath, file_extension: str):
    """
    Given a directory containing the tables comprising a schema and the appropriate file
    extension print a summary of each table.
    """
    all_file_names = next(os.walk(schema_directory))[2]
    parquet_file_names = [
        file_name for file_name in all_file_names if file_name.endswith(file_extension)
    ]

    for file_name in parquet_file_names:
        if file_extension.endswith("parquet"):
            # Read metadata from parquet file without loading the actual data.
            parquet_file = pq.ParquetFile(schema_directory / file_name)
            print(parquet_file.metadata)

            # Read data from parquet and convert to pandas data frame.
            parquet_table = pq.read_table(schema_directory / file_name)
            df = parquet_table.to_pandas()
            print(df.head())
            print(df.info())
