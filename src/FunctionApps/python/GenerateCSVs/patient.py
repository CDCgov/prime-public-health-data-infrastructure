from curses import pair_content


def parse_patient_resource(pt_rsc: dict) -> str:
    """ Given a FHIR patient resource as a dict return a comma deliminated string containing the following values:
    frist_name
    """
    return ','.join([get_name(pt_rsc), pt_rsc['resource'].get('birthDate'), pt_rsc['resource'].get('gender'), get_address(pt_rsc), get_race_ethnicity(pt_rsc)])

def get_name(pt_rsc: dict) -> str:
    """ Given a patient resource return a string on the form '<first_name>,<last_name>'. 
    When present the first name designated as 'official' is used, otherwise the first name listed is used."""

    names = pt_rsc['resource'].get('name')
    if names:
        name_str = ''
        for name in names:
            if name.get('use') == 'official':
                name_str = extract_name(name)
        if not name_str:
            name_str = extract_name(names[0])
    else:
        name_str = ","

    return name_str

def extract_name(name: dict) -> str:
    """ Given a an entry in a list of names from a patient resource return a string on the form '<first_name>,<last_name>'."""

    return f"{get_value(name, 'given')},{get_value(name, 'family')}"

def get_address(pt_rsc: dict) -> str:
    """ Given a patient resource return a string on the form '<street address>,<city>,<state>,<zip code>,<lat>,<long>'. 
    When present the first address designated as 'home' address is used, otherwise the first address listed is used. """

    addrs = pt_rsc['resource'].get('address')
    if addrs:
        addr_str = ''
        for addr in addrs:
            if addr.get('use') == 'home':
                addr_str = extract_address(addr)
        if not addr_str:
            addr_str = extract_address(addrs[0])
    else:
        addr_str = ',,,,,'

    return addr_str

def extract_address(addr: dict) -> str:
    """ Given a an entry in a list of addresses from a patient resource return a string on the form '<street address>,<city>,<state>,<zip code>,<lat>,<long>'."""

    addr_parts = ['line', 'city', 'state', 'postalCode', 'latitude', 'longitude']
    addr_str = ''
    for part in addr_parts:
        if part not in ['latitude', 'longitude']:
            addr_str += get_value(addr, part) + ","
        else:
            addr_str += get_coordinate(addr, part)
            if part == 'latitude':
                addr_str += ','
    return addr_str

def get_coordinate(addr: dict, coord:str) -> str:
    """Given an entry in a list of addresses from a patient resource return latitude or longitude (specified by coord) as a string."""
    value = ''
    if 'extension' in addr:
        for extension in addr['extension']:
            if extension.get('url') == "http://hl7.org/fhir/StructureDefinition/geolocation":
                for coordinate in extension['extension']:
                    if coordinate.get('url') == coord:
                        value = str(coordinate.get('valueDecimal'))
    return value

def get_race_ethnicity(pt_rsc: dict) -> str:
    """ Given a patient resource return the patients race and ethnicity in a string of the form '<race>,<ethnicity>'."""
    race = ''
    ethnicity = ''
    if 'extension' in pt_rsc['resource']:
        for extension in pt_rsc['resource']['extension']:
            if extension['url'] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race":
                race = extension['extension'][0]['valueCoding']['display']
            elif extension['url'] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity":
                ethnicity = extension['extension'][0]['valueCoding']['display']
    return f"{race},{ethnicity}"

def get_value(dictionary: dict, key: str) -> str:
    """Given a dictionary and key return the value of the key. If the key is not present return an empty string. If the value is a list return the first element."""

    if key in dictionary:
        value = dictionary[key]
        if type(value) == list:
            value = value[0]
    else:
        value = ''

    return value    


if __name__ == "__main__":
    patient = {'fullUrl': 'urn:uuid:c53f9ad8-34c1-ce05-c0f6-7a0ea7bd8483', 
                'resource': {'resourceType': 'Patient', 
                'id': 'c53f9ad8-34c1-ce05-c0f6-7a0ea7bd8483', 
                'identifier': [{'value': 'E42308111'}, {'value': '292561276fcdefab6a2a1545abf7aa9bf30906ba6f0d4f8faff652efc3b4ab3c', 'system': 'urn:ietf:rfc:3986', 'use': 'temp'}], 
                'name': [{'family': 'DOE', 'given': ['JANE'], 'use': 'official'}], 
                'birthDate': '1950-01-28', 
                'gender': 'female', 
                'address': [{'line': ['123 Main Street'], 'city': 'Gotham', 'state': 'XY', 'postalCode': '12345', 'use': 'home', 'extension': [{'url': 'http://hl7.org/fhir/StructureDefinition/geolocation', 'extension': [{'url': 'latitude', 'valueDecimal': 3.14159}, {'url': 'longitude', 'valueDecimal': 2.71828}]}]}], 
                'telecom': [{'system': 'phone', 'use': 'home'}], 
                'extension': [{'url': 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-race', 'extension': [{'url': 'ombCategory', 'valueCoding': {'code': '2054-5', 'display': 'Black or African American', 'system': 'urn:oid:2.16.840.1.113883.6.238'}}, {'url': 'text', 'valueString': 'Black or African American'}]}, {'url': 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity', 'extension': [{'url': 'ombCategory', 'valueCoding': {'code': '2186-5', 'display': 'Non Hispanic or Latino', 'system': 'urn:oid:2.16.840.1.113883.6.238'}}, {'url': 'text', 'valueString': 'Non Hispanic or Latino'}]}]}, 
                'request': {'method': 'PUT', 'url': 'Patient/c53f9ad8-34c1-ce05-c0f6-7a0ea7bd8483'}
                }
    print(parse_patient_resource(patient))
    