# Introduction
The purpose of this document is to highlight the sections of the FHIR documentation outlining FHIR Server query operations:
https://build.fhir.org/http.html

# Read
`GET https://<server>/<resourceType>/<resourceId>`
Params: None
Body: None
Response: FHIR Resource of specified `<resourceType>`

Example: `GET https://phdi-pilot.onmicrosoft.com/Patient/12345`

Description:
Gets a Patient resource given the specified `<resourceId>`

# Search (GET with parameters)
`GET https://<server>/<resourceType>?<param1>=<value1>[&<param2>=<value2>...]`
Params: Search parameter(s) appropriate for resource type.  These are documented on the FHIR website.  Here's an example: https://www.hl7.org/fhir/patient.html#search
Body: None
Response: FHIR Bundle resource with ResourceType="searchset".  The "entry" property contains an array of search results.

Example: `GET https://phdi-pilot.onmicrosoft.com/Patient?family=doe&given=john`

Description:
This query performs a search on the specified resource type.  Result is a "Bundle" resource containing a collection of search results.

# Update (PUT)
`PUT https://<server>/<resourceType>/<resourceId>`
Params: None
Body: The FHIR resource to update.  The "id" element of the submitted resource must match the `<resourceId>` specified in the URL.
Response: 202 for successful update

Example: `GET https://phdi-pilot.onmicrosoft.com/Patient/12345`
```
{ 
    "resourceType": "Patient",
    "id": "12345",
    ...
}
```

Description:
This replaces the resource with the specified ID with the resource supplied in the body of the request.  Depending on the FHIR server's settings, it might create the record if one with the specified ID doesn't already exist.
