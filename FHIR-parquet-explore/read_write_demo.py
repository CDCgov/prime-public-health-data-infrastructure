from azure.identity import DefaultAzureCredential
import requests
import yaml
from typing import Literal, List
import json
import pyarrow as pa
import pyarrow.parquet as pq
import logging

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

def query_fhir_server(base_url: str, query: str = "", auth_method: Literal["azure"] = "azure") -> requests.models.Response:
    """
    Given the url for a FHIR server, a desired resource type, and an authentication 
    method execute a query of the server for all resources of the specified type and 
    return the response.

    :param str url: Url of the FHIR server to be queried.
    :param str resource_type: The FHIR resource type to be queried for.
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

def get_next_page(base_url: str, next_page: str, auth_method: Literal["azure"] = "azure") -> requests.models.Response:
    if auth_method == "azure":
        cred = DefaultAzureCredential()
        access_token = cred.get_token(f"{base_url}/.default").token
        response = requests.get(
                url=next_page, headers={"Authorization": f"Bearer {access_token}"}
                )
    return response

def apply_schema_to_patient(patient: dict, schema: dict) -> List:
    """
    Given a patient resource and a schema return a list of values specified by the 
    schema.

    :param dict patient: A patient FHIR resource on which to apply a schema.
    :param dict schema: A schema specifying the desired values by FHIR resource type.
    :return list data: A list containing the data extracted from the patient resource.
    """
    patient = patient["resource"]
    data = {}
    specified_fields = schema["Patient"]

    if "patient_id" in specified_fields:
        patient_id = patient.get("id", "")
        data["patient_id"] = patient_id
    
    if "first_name" in specified_fields:
        try:
            first_name = patient.get("name")[0].get("given")[0]
        except Exception:
            first_name = ""
        data["first_name"] = first_name

    if "last_name" in specified_fields:
        try:
            last_name = patient.get("name")[0].get("family")
        except Exception:
            last_name = ""
        data["last_name"] = last_name
    
    if "dob" in specified_fields:
        dob = patient.get("dob", "")
        data["dob"] = dob       

    if "gender" in specified_fields:
        gender = patient.get("gender", "")
        data["gender"] = gender

    if "phone_number" in specified_fields:
        try:
            phone_number = patient.get("telecom")[0].get('value')
        except Exception:
            phone_number = ""
        data["gender"] = gender
    
    if "street" in specified_fields:
        try:
            street = patient.get("address")[0].get('line')[0]
        except Exception:
            street = ""
        data["street"] = street

    if "city" in specified_fields:
        try:
            city = patient.get("address")[0].get('city')
        except Exception:
            city = ""
        data["city"] = city

    if "state" in specified_fields:
        try:
            state = patient.get("address")[0].get('state')
        except Exception:
            state = ""
        data["state"] = state

    if "country" in specified_fields:
        try:
            country = patient.get("address")[0].get('country')
        except Exception:
            country = ""
        data["country"] = country
    
    return data

if __name__ == "__main__":

    schema = load_schema("schema.yml")

    base_url = "https://phdi-pilot.azurehealthcareapis.com"
    query = "/Patient"
    output_file_name = "patient.parquet"
    response = query_fhir_server(base_url, query)

    additional_page = True
    writer = None

    while additional_page:
        if response.status_code == 200:
            query_result = json.loads(response.content)
            raw_schema_data = [apply_schema_to_patient(patient, schema) for patient in query_result["entry"]]
            table = pa.Table.from_pylist(raw_schema_data)

            if writer is None:
                writer = pq.ParquetWriter(output_file_name, table.schema)
            writer.write_table(table=table)

            for link in query_result.get('link'):
                if link.get("relation") == "next":
                    next_page_url = link.get("url")
                    response = get_next_page(base_url, next_page_url)
                    break
                else:
                    response = None
            
            if response is None:
                additional_page = False

        elif response.status_code == 401:
            logging.error("Status Code 401: Failed to authenticate with the FHIR server.")
            additional_page = False

        elif response.status_code == 404:
            logging.error("Status Code 404: FHIR server not found.")
            additional_page = False

    if writer is not None:
        writer.close()

    parquet_file = pq.ParquetFile(output_file_name)
    print(parquet_file.metadata)

    parquet_table = pq.read_table(output_file_name)
    df = parquet_table.to_pandas()
    print(df.head())
    print(df.info())
    breakpoint()