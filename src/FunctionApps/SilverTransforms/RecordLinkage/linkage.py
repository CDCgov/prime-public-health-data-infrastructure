from typing import Callable
import pandas as pd


def create_linking_identifier(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Creates a basic identifier used to check duplicates in an incoming
    batch of data. The basic identifier for the prototype is
      FIRSTNAME-LASTNAME-YYYY-MM-DD
    This identifier is joined to the dataframe proper for use in future
    computation, as well as potential future use in generating/referencing
    a master ID.
    '''
    last_names = df['name'].map(lambda x: x[0]['family'])
    first_names = df['name'].map(lambda x: '-'.join(x[0]['given']))
    df['linking_identifier'] = first_names + '-' + last_names + '-' + df['birthDate']
    return df


def find_matches(df: pd.DataFrame, dupe_field: str) -> dict:
    '''
    From a dataframe containing a column to use as the unique identifier
    field, identify any and all duplicate records using strict, EXACT
    match criteria. Returns a dictionary whose keys are the ids of 
    patients found to be duplicates of some record, and whose values
    are the new ids to store in the linked resources of these duplicate
    patients.
    '''
    dupes = {}
    for _, group in df.groupby([dupe_field]):
        grouped_ids = list(group['id'])
        dupes[grouped_ids[0]] = list(grouped_ids[1:])
    ids_to_replace = {}
    for pid in dupes:
        if len(dupes[pid]) != 0:
            for oid in dupes[pid]:
                ids_to_replace[oid] = pid
    return ids_to_replace


def record_combination_func(x: pd.Series) -> str:
    '''
    Aggregation function applied behind the scenes when performing
    de-duplicating linkage. Automatically filters for blank, null,
    and NaN values to facilitate squashing duplicates down into one
    consolidated record, such that, for any column X:
      - if records 1, ..., n-1 are empty in X and record n is not,
        then n(X) is used as a single value
      - if some number of records 1, ..., j <= n have the same value 
        in X and all other records are blank in X, then the value
        of the matching columns 1, ..., j is used as a singleton
      - if some number of non-empty in X records 1, ..., j <= n have 
        different values in X, then all values 1(X), ..., j(X) are
        concatenated into a unique list of values delimited by |
    '''
    non_nans = set([x for x in x.astype(str).to_list() if x != ''])
    return '|'.join(non_nans)


def merge_duplicates(
        df: pd.DataFrame,
        dupe_field: str,
        group_func: Callable
    ) -> pd.DataFrame:
    '''
    Perform de-duplication linkage on a dataframe of patient records. 
    All records that have an *EXACT* match in dupe_field are linked
    according to the provided group_func. Grouped records are consolidated
    into single rows, and the de-duplicated dataframe is returned.
    '''
    df2 = df.groupby(dupe_field).agg(group_func).reset_index()
    df2.fillna('')
    df2['id'] = df2['id'].str.split("|").str[0]
    return df2


def get_patient_col(resource: pd.DataFrame) -> str:
    '''
    Given a dataframe of a particular type of resource, determine the
    name of the column that holds a reference to the patient that
    the resource relates to. Note some resource types do not reference
    a patient at all; these are returned as blank strings.
    '''
    resource_type = resource['resourceType'][0]
    if resource_type == 'Organization' or resource_type == 'Practitioner':
        return ''
    if resource_type == 'ExplanationOfBenefit':
        return ['patient', 'subject']
    if resource_type == 'Observation' or resource_type == 'Condition' \
        or resource_type == 'DiagnosticReport' or resource_type == 'Encounter' \
            or resource_type == 'MedicationRequest' or resource_type == 'Procedure':
        return 'subject'
    return 'patient'


def replace_id(patient_ref: dict, dupes: dict) -> str:
    '''
    Given a single entry in a reference column for a non-patient
    FHIR resource, replace this generated ID with the "de-duplicated"
    ID contained in the index mapping, if the ID is indeed a 
    duplicate.
    '''
    pid = patient_ref['reference']
    parts = [x.strip() for x in pid.split('/')]
    if parts[1] in dupes:
        parts[1] = dupes[parts[1]]
        return { 'reference': '/'.join(parts) }
    return patient_ref
