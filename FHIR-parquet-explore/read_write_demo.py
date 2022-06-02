from azure.identity import DefaultAzureCredential
from pathlib import Path
import requests
import yaml
from typing import Literal, List
import json
import pyarrow as pa
import pyarrow.parquet as pq
import logging
import numpy as np
import random
from phdi_building_blocks.fhir import AzureFhirserverCredentialManager


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


def query_fhir_server(
    base_url: str, credential_manager: AzureFhirserverCredentialManager, query: str = ""
) -> requests.models.Response:
    """
    Given the url for a FHIR server, a query to execute via the server's API, and an
    authentication method execute a query of the server for all resources of the
    specified type and return the response.

    :param str base_url: Url of the FHIR server to be queried.
    :param str query: The query for the FHIR server to execute.
    :param str auth_method: A string specifying the authentication method to be used
    with the FHIR server.
    :return requests.models.Response response: The response from the FHIR server.
    """

    full_url = base_url + query
    access_token = credential_manager.get_access_token().token
    header = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url=full_url, headers=header)

    return response


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


def log_fhir_server_error(status_code: int):
    """Given a status code from a FHIR server's response log the specified error.

    :param int status_code: Status code returned by a FHIR server
    """
    if response.status_code == 401:
        logging.error(
            "FHIR SERVER ERROR - Status Code 401: Failed to authenticate with the FHIR server."
        )
        additional_page = False

    elif response.status_code == 404:
        logging.error("FHIR SERVER ERROR - Status Code 404: FHIR server not found.")
        additional_page = False


if __name__ == "__main__":

    schema = load_schema("schema.yml")
    table_name = list(schema.keys())[0]
    schema = schema[table_name]

    base_url = "https://phdi-pilot.azurehealthcareapis.com"

    credential_manager = AzureFhirserverCredentialManager(base_url)

    for resource_type in schema.keys():
        query = f"/{resource_type}"
        output_file_name = Path(f"{table_name}/{resource_type}.parquet")
        output_file_name.parent.mkdir(parents=True, exist_ok=True)

        response = query_fhir_server(base_url, credential_manager, query)

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
            table = pa.Table.from_pylist(raw_schema_data)
            if writer is None:
                writer = pq.ParquetWriter(output_file_name, table.schema)
            writer.write_table(table=table)

            # Check for an additional page of query results.
            for link in query_result.get("link"):
                if link.get("relation") == "next":
                    next_page_url = link.get("url")
                    response = query_fhir_server(next_page_url, credential_manager)
                    break
                else:
                    response = None

            if response is None:
                additional_page = False

        if writer is not None:
            writer.close()

        # Read metadata from parquet file without loading the actual data.
        parquet_file = pq.ParquetFile(output_file_name)
        print(parquet_file.metadata)

        # Read data from parquet and convert to pandas data frame.
        parquet_table = pq.read_table(output_file_name)
        df = parquet_table.to_pandas()
        print(df.head())
        print(df.info())
