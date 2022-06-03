from azure.identity import DefaultAzureCredential
import pathlib
import requests
import yaml
from typing import Literal, List
import json
import pyarrow as pa
import pyarrow.parquet as pq
import logging
import numpy as np
import random
from phdi_building_blocks.fhir import (
    AzureFhirserverCredentialManager,
    query_fhir_server,
    log_fhir_server_error,
)
import os


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


def parse_value(
    value: list,
    path: List[str],
    selection_criteria: Literal["first", "last", "random", "all"],
) -> str:
    """
    Given a list containing all the values stored in a top level key in a FHIR resource,
    follow the provided path and apply the selection criteria to extract the desired
    value.

    :param list value: A list containing the values stored in a top level key in a FHIR
    resource.
    :param str path: A list were each element represents one parsing step.
    :param str selection_criteria: A string indicating which element of list to select
    when one is encountered during parsing.
    """
    num_steps = len(path)
    for index, step in enumerate(path):

        if type(value) == list:

            # When a list of dictionaries is encountered select the relevant subset
            # ensuring that at a minimum the next step in the path is a key in the
            # dictionary, and when specified the dictionary contains a desired key:value
            # pair.

            all_dicts = all(isinstance(element, dict) for element in value)
            if num_steps == 1:
                last_step = True
            else:
                last_step = index < num_steps - 2

            if all_dicts and not last_step:
                next_step = path[index + 1]
                parts = next_step.split("|")
                if len(parts) == 2:
                    required_pair = parts[1].split(":")
                    if len(required_pair) == 2:
                        required_key = required_pair[0]
                        required_value = required_pair[1]
                        value = [
                            x for x in value if x.get(required_key) == required_value
                        ]
                        next_key = parts[0]
                        path[index + 1] = next_key
                    else:
                        logging.error(
                            "Encountered improperly formatted fhir_path in schema."
                        )
                        return ""
                elif len(parts) >= 3:
                    logging.error(
                        "Encountered improperly formatted fhir_path in schema."
                    )
                    return ""

            # Apply selection criteria
            if selection_criteria == "first":
                value = value[0]
            elif selection_criteria == "last":
                value = value[-1]
            elif selection_criteria == "random":
                value = random.choice(value)
            elif selection_criteria == "all":
                break
        elif type(value) == dict:
            value = value.get(step, "")

        if np.isscalar(value):
            break

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
        path = path.split("/")
        path = path[path.index(resource.get("resourceType")) + 1 :]
        value = resource.get(path[0], "")

        if np.isscalar(value):
            data[resource_schema[field]["new_name"]] = value
        else:
            selection_criteria = resource_schema[field]["selection_criteria"]
            if type(value) == list:
                value = parse_value(value, path, selection_criteria)
            elif type(value) == dict:
                value = parse_value(value, path[1:], selection_criteria)
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


if __name__ == "__main__":

    # Make Schema
    fhir_url = "https://phdi-pilot.azurehealthcareapis.com"
    schema_path = pathlib.Path("schema.yml")
    output_path = pathlib.Path("")
    output_format = "parquet"
    generate_schema(fhir_url, schema_path, output_path, output_format)

    # Display Schema Summary
    schema = load_schema(schema_path)
    schema_directory = output_path / list(schema.keys())[0]
    get_schema_summary(schema_directory, ".parquet")
