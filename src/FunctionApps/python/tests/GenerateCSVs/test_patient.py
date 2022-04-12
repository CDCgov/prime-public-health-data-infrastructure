from GenerateCSVs.patient import parse_patient_resource


def test_parse_patient_resource():

    patient = {
        "fullUrl": "urn:uuid:c53f9ad8-34c1-ce05-c0f6-7a0ea7bd8483",
        "resource": {
            "resourceType": "Patient",
            "id": "c53f9ad8-34c1-ce05-c0f6-7a0ea7bd8483",
            "identifier": [
                {"value": "E42308111"},
                {
                    "value": "292561276fcdefab6a2a1545abf7aa9bf30906ba6f0d4f8faff652efc3b4ab3c",
                    "system": "urn:ietf:rfc:3986",
                    "use": "temp",
                },
            ],
            "name": [{"family": "DOE", "given": ["JANE"], "use": "official"}],
            "birthDate": "1950-01-28",
            "gender": "female",
            "address": [
                {
                    "line": ["123 Main Street"],
                    "city": "Gotham",
                    "state": "XY",
                    "postalCode": "12345",
                    "use": "home",
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                            "extension": [
                                {"url": "latitude", "valueDecimal": 3.14159},
                                {"url": "longitude", "valueDecimal": 2.71828},
                            ],
                        }
                    ],
                }
            ],
            "telecom": [{"system": "phone", "use": "home"}],
            "extension": [
                {
                    "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                    "extension": [
                        {
                            "url": "ombCategory",
                            "valueCoding": {
                                "code": "2054-5",
                                "display": "Black or African American",
                                "system": "urn:oid:2.16.840.1.113883.6.238",
                            },
                        },
                        {"url": "text", "valueString": "Black or African American"},
                    ],
                },
                {
                    "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                    "extension": [
                        {
                            "url": "ombCategory",
                            "valueCoding": {
                                "code": "2186-5",
                                "display": "Non Hispanic or Latino",
                                "system": "urn:oid:2.16.840.1.113883.6.238",
                            },
                        },
                        {"url": "text", "valueString": "Non Hispanic or Latino"},
                    ],
                },
            ],
        },
        "request": {
            "method": "PUT",
            "url": "Patient/c53f9ad8-34c1-ce05-c0f6-7a0ea7bd8483",
        },
    }

    patient_empty = {
        "fullUrl": "urn:uuid:c53f9ad8-34c1-ce05-c0f6-7a0ea7bd8483",
        "resource": {
            "resourceType": "Patient",
            "id": "c53f9ad8-34c1-ce05-c0f6-7a0ea7bd8483",
        },
        "request": {
            "method": "PUT",
            "url": "Patient/c53f9ad8-34c1-ce05-c0f6-7a0ea7bd8483",
        },
    }

    assert (
        parse_patient_resource(patient)
        == "292561276fcdefab6a2a1545abf7aa9bf30906ba6f0d4f8faff652efc3b4ab3c,JANE,DOE,1950-01-28,female,123 Main Street,Gotham,XY,12345,3.14159,2.71828,Black or African American,Non Hispanic or Latino"
    )
    assert parse_patient_resource(patient_empty) == ",,,,,,,,,,,,"
