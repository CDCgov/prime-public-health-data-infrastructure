from RecordLinkage.linkage import *
import azure.functions as func
import pandas as pd


def main(req: func.HttpRequest) -> func.HttpResponse:
    
    # Extract patient and non-patient ndjson bundles
    try:
        incoming_ndjson = req.get_json()
        patient_resources = pd.DataFrame.from_records(incoming_ndjson['patients'])
        non_patient_resources = [pd.DataFrame.from_records(x) for x in incoming_ndjson['nonpatients']]
    except:
        return func.HttpResponse("Unable to read FHIR resource data from request", status_code=500)

    # Perform intra-batch record linkage and squash duplicates
    try:
        patients = create_linking_identifier(patient_resources)
        dupes = find_matches(patients, 'linking_identifier')
        patients = merge_duplicates(patients, 'linking_identifier', record_combination_func)
    
        # For all other FHIR resources, backpoint patient IDs
        # of de-duped patients to new coalesced record
        for resource in non_patient_resources:
            patient_col = get_patient_col(resource)
            resource[patient_col] = resource[patient_col].map(lambda x: replace_id(x, dupes))

        return func.HttpResponse(f"{len(patient_resources) - len(patients)} records linked via de-duplication", status_code=200)
    
    except:
        return func.HttpResponse("Unable to link records", status_code=500)
