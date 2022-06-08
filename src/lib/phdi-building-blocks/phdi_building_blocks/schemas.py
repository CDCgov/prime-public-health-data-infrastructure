import pathlib
import os
import yaml
import json
import random
from typing import Literal, List, Union
import pyarrow as pa
import pyarrow.parquet as pq
import fhirpathpy

from phdi_building_blocks.fhir import (
    AzureFhirserverCredentialManager,
    fhir_server_get,
)


def load_schema(path: str) -> dict:
    """
    Given the path to local YAML files containing a user-defined schema read the file
    and return the schema as a dictionary.

    :param path: Path specifying the location of a YAML file containing a schema.
    :return schema: A user-defined schema
    """
    try:
        with open(path, "r") as file:
            schema = yaml.safe_load(file)
        return schema
    except FileNotFoundError:
        return {}


def apply_selection_criteria(
    value: list,
    selection_criteria: Literal["first", "last", "random", "all"],
) -> Union[str, List[str]]:
    """
    Given a list of values parsed from a FHIR resource, return value(s) according to the
    selection criteria. In general a single value is returned, but when
    selection_criteria is set to "all" a list containing all of the parsed values is
    returned.

    :param value: A list containing the values parsed from a FHIR resource.
    :param selection_criteria: A string indicating which element(s) of a list to select.
    """

    if selection_criteria == "first":
        value = value[0]
    if selection_criteria == "last":
        value = value[-1]
    if selection_criteria == "random":
        value = random.choice(value)

    # Temporary hack to ensure no structured data is written using pyarrow.
    # Currently Pyarrow does not support mixing non-structured and structured data.
    # https://github.com/awslabs/aws-data-wrangler/issues/463
    # Will need to consider other methods of writing to parquet if this is an essential
    # feature.
    if type(value) == dict:
        value = json.dumps(value)
    elif type(value) == list:
        value = ",".join(value)
    return value


def apply_schema_to_resource(resource: dict, schema: dict) -> dict:
    """
    Given a resource and a schema, return a dictionary with values of the data
    specified by the schema and associated keys defined by the variable name provided
    by the schema.

    :param resource: A FHIR resource on which to apply a schema.
    :param schema: A schema specifying the desired values by FHIR resource type.
    """

    data = {}
    resource_schema = schema.get(resource.get("resourceType", ""))
    if resource_schema is None:
        return data
    for field in resource_schema.keys():
        path = resource_schema[field]["fhir_path"]
        value = fhirpathpy.evaluate(resource, path)

        if len(value) == 0:
            data[resource_schema[field]["new_name"]] = None
        else:
            selection_criteria = resource_schema[field]["selection_criteria"]
            value = apply_selection_criteria(value, selection_criteria)
            data[resource_schema[field]["new_name"]] = value

    return data


def make_resource_type_table(
    resource_type: str,
    schema: dict,
    output_path: pathlib.Path,
    output_format: Literal["parquet"],
    credential_manager: AzureFhirserverCredentialManager,
):
    """
    Given a FHIR resource type, schema, and FHIR server credential manager create a
    table containing the fields from the resource type specified in the schema.

    :param resource_type: A FHIR resource type.
    :param schema: A schema specifying the desired values by FHIR resource type.
    :param output_path: A path specifying where the table should be written.
    :param output_format: A string indicating the file format to be used.
    :param credential_manager: A credential manager for a FHIR server.
    """

    output_path.mkdir(parents=True, exist_ok=True)
    output_file_name = output_path / f"{resource_type}.{output_format}"

    query = f"/{resource_type}"
    url = credential_manager.fhir_url + query
    access_token = credential_manager.get_access_token().token
    response = fhir_server_get(url, access_token)

    writer = None
    while response is not None:
        if response.status_code != 200:
            break

        # Load queried data.
        query_result = json.loads(response.content)
        data = []

        # Extract values specified by schema from each resource.
        # values_from_resource is a dictionary of the form:
        # {field1:value1, field2:value2, ...}.

        for resource in query_result["entry"]:
            values_from_resource = apply_schema_to_resource(
                resource["resource"], schema
            )
            if values_from_resource != {}:
                data.append(values_from_resource)

        # Write data to file.
        writer = write_schema_table(data, output_file_name, output_format, writer)

        # Check for an additional page of query results.
        for link in query_result.get("link"):
            if link.get("relation") == "next":
                url = link.get("url")
                access_token = credential_manager.get_access_token().token
                response = fhir_server_get(url, access_token)
                break
            else:
                response = None

    if writer is not None:
        writer.close()


def make_tables_from_schema(
    fhir_url: str,
    schema_path: pathlib.Path,
    output_path: pathlib.Path,
    output_format: Literal["parquet"],
):
    """
    Given the url for a FHIR server, the location of a schema file, and and output
    directory generate the specified schema and store the tables in the desired
    location.

    :param fhir_url: URL to a FHIR server.
    :param schema_path: A path to the location of a YAML schema config file.
    :param output_path: A path to the directory where tables of the schema should be written.
    :param output_format: Specifies the file format of the tables to be generated.
    """

    schema = load_schema(schema_path)
    schema_name = list(schema.keys())[0]
    schema = schema[schema_name]
    output_path = output_path / schema_name

    credential_manager = AzureFhirserverCredentialManager(fhir_url)

    for resource_type in schema.keys():
        make_resource_type_table(
            resource_type, schema, output_path, output_format, credential_manager
        )


def write_schema_table(
    data: List[dict],
    output_file_name: pathlib.Path,
    file_format: Literal["parquet"],
    writer: pq.ParquetWriter = None,
):
    """
    Write data extracted from the FHIR Server to a file.

    :param data: A list of dictionaries specifying the data for each row of a table
    where the keys of each dict correspond to the columns, and the values contain the
    data for each entry in a row.
    :param output_file_name: Full name for the file where the table is to be written.
    :param output_format: Specifies the file format of the table to be written.
    :param writer: A writer object that can be kept open between calls of this function
    to support file formats that cannot be appended to after being written
    (e.g. parquet).
    """

    if file_format == "parquet":
        table = pa.Table.from_pylist(data)
        if writer is None:
            writer = pq.ParquetWriter(output_file_name, table.schema)
        writer.write_table(table=table)
        return writer


def print_schema_summary(
    schema_directory: pathlib.Path,
    file_format: Literal["parquet"],
    display_head: bool = False,
):
    """
    Given a directory containing tables of the specified file format, print a summary of
    each table.

    :param schema_directory: Path specifying location of schema tables.
    :param file_format: Format of files in schema.
    :param display_head: Print the head of each table when true. Note depending on the
    file format this may require reading large amounts of data into memory.
    """

    all_file_names = next(os.walk(schema_directory))[2]
    parquet_file_names = [
        file_name for file_name in all_file_names if file_name.endswith(file_format)
    ]

    for file_name in parquet_file_names:
        if file_format.endswith("parquet"):
            # Read metadata from parquet file without loading the actual data.
            parquet_file = pq.ParquetFile(schema_directory / file_name)
            print(parquet_file.metadata)

            # Read data from parquet and convert to pandas data frame.
            if display_head is True:
                parquet_table = pq.read_table(schema_directory / file_name)
                df = parquet_table.to_pandas()
                print(df.head())
                print(df.info())
