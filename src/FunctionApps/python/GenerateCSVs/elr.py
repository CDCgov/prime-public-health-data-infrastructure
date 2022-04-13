from typing import List, Any
from GenerateCSVs.patient import PATIENT_COLUMNS, parse_patient_resource


ELR_COLUMNS = PATIENT_COLUMNS + ["loinc_code", "result", "effective_date"]


def extract_covid_test(observation: dict) -> dict:
    """
    Given an observation FHIR profile, determine whether the profile
    contains information related to a COVID test or COVID status.
    If yes, collect the relevant lab code, test result, and test
    date into a list.
    """
    print(observation)
    code = observation["code"]["coding"][0]
    if "loinc" in code["system"] and "valueCodeableConcept" in observation:
        obs_date = observation["effectiveDateTime"]
        result = observation["valueCodeableConcept"]["coding"][0]["display"]
        return [code["code"], result, obs_date]
    return []


def elr_to_csv(bundle: dict) -> List[Any]:
    """
    Given a FHIR bundle containing a patient resource and one or more
    ELR lab observations, identify the labs related to COVID and turn
    them into patient-identified rows for use in a CSV.
    """
    rows_to_write = []
    row_root = []
    for resource in bundle["entry"]:
        if resource["resource"]["resourceType"] == "Patient":
            row_root.extend(parse_patient_resource(resource))
        elif resource["resource"]["resourceType"] == "Observation":
            obs_info = extract_covid_test(resource["resource"])
            if len(obs_info) > 0:
                rows_to_write.append(row_root + obs_info)
    return rows_to_write
