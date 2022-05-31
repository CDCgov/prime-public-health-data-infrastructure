from azure.identity import DefaultAzureCredential
import requests
import yaml
from typing import Literal, List
import json
import pyarrow as pa
import pyarrow.parquet as pq
import logging
import numpy as np
import random


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
    base_url: str, query: str = "", auth_method: Literal["azure"] = "azure"
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

    if auth_method == "azure":
        cred = DefaultAzureCredential()
        access_token = cred.get_token(f"{base_url}/.default").token
        response = requests.get(
            url=full_url, headers={"Authorization": f"Bearer {access_token}"}
        )

    return response


def get_next_page(
    base_url: str, next_page: str, auth_method: Literal["azure"] = "azure"
) -> requests.models.Response:
    """
    Given the url for a FHIR server, the url for the next page of results in query, and
    an authentication method execute a query of the server for all resources of the
    specified type and return the response.

    :param str base_url: The url of the FHIR server to be queried.
    :param str next_page: The url for the next page of results in query.
    :param str auth_method: A string specifying the authentication method to be used
    with the FHIR server.
    :return requests.models.Response response: The response from the FHIR server.
    """

    if auth_method == "azure":
        cred = DefaultAzureCredential()
        access_token = cred.get_token(f"{base_url}/.default").token
        response = requests.get(
            url=next_page, headers={"Authorization": f"Bearer {access_token}"}
        )

    return response


def parse_value(
    value: list,
    path: List[str],
    selection_rule: Literal["first", "last", "random", "all"],
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

    for step in path:
        # Apply selection rule
        if type(value) == list:
            if selection_rule == "first":
                value = value[0]
            elif selection_rule == "last":
                value = value[-1]
            elif selection_rule == "random":
                value = random.choice(value)
            elif selection_rule == "all":
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
        value = " ".join(value)
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
        return
    else:
        for field in resource_schema.keys():

            path = resource_schema[field]["fhir_path"]
            path = path.split("/")
            path = path[path.index(resource.get("resourceType")) + 1 :]
            value = resource.get(path[0], "")

            if np.isscalar(value):
                data[resource_schema[field]["new_name"]] = value
            else:
                selection_criteria = resource_schema[field]["selection_criteria"]
                value = parse_value(value, path, selection_criteria)
                data[resource_schema[field]["new_name"]] = value

    return data


if __name__ == "__main__":

    schema = load_schema("schema.yml")
    schema = schema[list(schema.keys())[0]]

    base_url = "https://phdi-pilot.azurehealthcareapis.com"

    for resource_type in schema.keys():
        query = f"/{resource_type}"
        output_file_name = f"{resource_type}.parquet"
        response = query_fhir_server(base_url, query)

        additional_page = True
        writer = None

        while additional_page:
            if response.status_code == 200:

                # Load queried data.
                query_result = json.loads(response.content)
                raw_schema_data = []

                # Extract values specified by schema from each resource.
                for resource in query_result["entry"]:
                    values_from_resource = apply_schema_to_resource(
                        resource["resource"], schema
                    )
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
                        response = get_next_page(base_url, next_page_url)
                        break
                    else:
                        response = None

                if response is None:
                    additional_page = False

            elif response.status_code == 401:
                logging.error(
                    "Status Code 401: Failed to authenticate with the FHIR server."
                )
                additional_page = False

            elif response.status_code == 404:
                logging.error("Status Code 404: FHIR server not found.")
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
