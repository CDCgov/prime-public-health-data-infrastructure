from typing import Callable
import pandas as pd

PATH_TO_DATA = '/Users/Brandon/Downloads/Archive/Patient-1.ndjson'

def make_test_dedupe_data(df: pd.DataFrame):
    '''
    Turn a bundle of patient data into a small test set for verifying
    efficacy of deduplication. There will be 6 unique records here,
    4 of which are completely dissimilar, one which will have three
    duplicated versions of varying changes, and one which will be a 
    near match for the duplicates but is off by one character.
    '''
    
    # Full match case: everything the same, should be no merge conflicts
    df.loc[6, :] = df.loc[0, :]

    # Most match case: one field blank, one present
    df.loc[7, :] = df.loc[0, :]
    df.loc[7, 'gender'] = ''

    # Multi-match case: store both in ndjson
    df.loc[8, :] = df.loc[0, :]
    df.loc[8, 'address'] = df.loc[10, 'address']

    # Near-match case: not actually a dupe, but off by one char
    df.loc[9, :] = df.loc[0, :]
    dob_list = df.loc[9, 'birthDate'].split('-')
    dob_list[1] = str((int(dob_list[1]) + 1) % 12)
    df.loc[9, 'birthDate'] = '-'.join(dob_list)

    return df[:10]


def create_linking_identifier(df: pd.DataFrame):
    '''
    Creates a basic identifier used to check duplicates in an incoming
    batch of data. The basic identifier for the prototype is
      FIRSTNAME-LASTNAME-YYYY-MM-DD
    This identifier is joined to the dataframe proper for use in future
    computation, as well as potential future use in generating/referencing
    a master ID.
    '''
    df['last_name'] = df['name'].apply(lambda x: x[0]['family'] if type(x[0]['family']) is str else '-'.join(x[0]['family']))
    df['first_name'] = df['name'].apply(lambda x: x[0]['given'] if type(x[0]['given']) is str else '-'.join(list(x[0]['given'])))
    df['linking_identifier'] = df['first_name'] + '-' + df['last_name'] + '-' + df['birthDate']
    df.drop(columns=['first_name', 'last_name'], inplace=True)
    return df


def find_matches(df: pd.DataFrame, dupe_field: str):
    '''
    From a dataframe containing a column to use as the unique identifier
    field, identify any and all duplicate records using strict, EXACT
    match criteria. Returns a dictionary showing the unique identifiers
    mapping to lists of rows in the DF that all slotted into this group.
    Currently not required for linkage, but exists a separate util.
    '''
    dupes = {}
    for id, group in df.groupby([dupe_field]):
        dupes[id] = list(group.index)
    return dupes


def record_combination_func(x: pd.Series):
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
    if x.isnull().values.all():
        return ''
    non_nans = [x for x in list(x.astype(str)) if x != '']
    return '|'.join(set(non_nans)) if len(non_nans) > 1 else non_nans[0]


def merge_duplicates(
        df: pd.DataFrame,
        dupe_field: str,
        group_func: Callable
    ):
    '''
    Perform de-duplication linkage on a dataframe of patient records. 
    All records that have an *EXACT* match in dupe_field are linked
    according to the provided group_func. Grouped records are consolidated
    into single rows, and the de-duplicated dataframe is returned.
    '''
    df2 = df.groupby(dupe_field).agg(group_func).reset_index()
    df2.fillna('')
    return df2


# Don't need this for the prod pipeline, this is just some fake
# data for now
df = pd.read_json(PATH_TO_DATA, lines=True)
df = make_test_dedupe_data(df)

df = create_linking_identifier(df)
dupes = find_matches(df, 'linking_identifier')
print(dupes)
df = merge_duplicates(df, 'linking_identifier', record_combination_func)
df.to_csv('./src/notebooks/out.csv', index=False)