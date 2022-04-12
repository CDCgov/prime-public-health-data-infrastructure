PATIENT_COLUMNS = [
    "patient_hash",
    "given_name",
    "family_name",
    "birthDate",
    "gender",
    "street",
    "city",
    "state",
    "postalCode",
    "latitude",
    "longitude",
    "race",
    "ethnicity",
]


def parse_patient_resource(pt_rsc: dict) -> str:
    """Given a FHIR patient resource return a comma deliminated string of the following form:
    '<patient_hash>,<given_name>,<family_name>,<birthDate>,<gender>,<street>,<city>,<state>,<postalCode>,<latitude>,<longitude>,<race>,<ethnicity>'"""

    return ",".join(
        [
            get_id(pt_rsc),
            get_name(pt_rsc),
            pt_rsc["resource"].get("birthDate", ""),
            pt_rsc["resource"].get("gender", ""),
            get_address(pt_rsc),
            get_race_ethnicity(pt_rsc),
        ]
    )


def get_id(pt_rsc: dict) -> str:
    """Given a patient resource retrun the hashed identifier added previously in the PHDI pipeline."""

    hash = ""
    identifiers = pt_rsc["resource"].get("identifier")
    if identifiers:
        for id in identifiers:
            if id.get("system") == "urn:ietf:rfc:3986":
                hash = id.get("value")

    return hash


def get_name(pt_rsc: dict) -> str:
    """Given a patient resource return a string on the form '<given_name>,<family_name>'.
    When present the first name designated as 'official' is used, otherwise the first name listed is used."""

    names = pt_rsc["resource"].get("name")
    if names:
        name_str = ""
        for name in names:
            if name.get("use") == "official":
                name_str = extract_name(name)
        if not name_str:
            name_str = extract_name(names[0])
    else:
        name_str = ","

    return name_str


def extract_name(name: dict) -> str:
    """Given a an entry in a list of names from a patient resource return a string on the form '<first_name>,<last_name>'."""

    return f"{get_value(name, 'given')},{get_value(name, 'family')}"


def get_address(pt_rsc: dict) -> str:
    """Given a patient resource return a string on the form '<street>,<city>,<state>,<postalCode>,<latitude>,<longitude>'.
    When present the first address designated as 'home' address is used, otherwise the first address listed is used."""

    addrs = pt_rsc["resource"].get("address")
    if addrs:
        addr_str = ""
        for addr in addrs:
            if addr.get("use") == "home":
                addr_str = extract_address(addr)
        if not addr_str:
            addr_str = extract_address(addrs[0])
    else:
        addr_str = ",,,,,"

    return addr_str


def extract_address(addr: dict) -> str:
    """Given a an entry in a list of addresses from a patient resource return a string on the form '<street>,<city>,<state>,<postalCode>,<latitude>,<longitude>'."""

    addr_parts = ["line", "city", "state", "postalCode", "latitude", "longitude"]
    addr_str = ""
    for part in addr_parts:
        if part not in ["latitude", "longitude"]:
            addr_str += get_value(addr, part) + ","
        else:
            addr_str += get_coordinate(addr, part)
            if part == "latitude":
                addr_str += ","

    return addr_str


def get_coordinate(addr: dict, coord: str) -> str:
    """Given an entry in a list of addresses from a patient resource return latitude or longitude (specified by coord) as a string."""

    value = ""
    if "extension" in addr:
        for extension in addr["extension"]:
            if (
                extension.get("url")
                == "http://hl7.org/fhir/StructureDefinition/geolocation"
            ):
                for coordinate in extension["extension"]:
                    if coordinate.get("url") == coord:
                        value = str(coordinate.get("valueDecimal"))

    return value


def get_race_ethnicity(pt_rsc: dict) -> str:
    """Given a patient resource return the patients race and ethnicity in a string of the form '<race>,<ethnicity>'."""

    race = ""
    ethnicity = ""
    if "extension" in pt_rsc["resource"]:
        for extension in pt_rsc["resource"]["extension"]:
            if (
                extension["url"]
                == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"
            ):
                race = extension["extension"][0]["valueCoding"]["display"]
            elif (
                extension["url"]
                == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
            ):
                ethnicity = extension["extension"][0]["valueCoding"]["display"]

    return f"{race},{ethnicity}"


def get_value(dictionary: dict, key: str) -> str:
    """Given a dictionary and key return the value of the key. If the key is not present return an empty string. If the value is a list return the first element."""

    if key in dictionary:
        value = dictionary[key]
        if type(value) == list:
            value = value[0]
    else:
        value = ""

    return value
