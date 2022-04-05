# Introduction
This file describes required authorization processing for authorizing to the PHDI FHIR server.

## Client Credentials
The OAuth2 client credentials flow is used to authorize to the FHIR server.  References:
* RFC - section 4.4: (https://www.ietf.org/rfc/rfc6749.txt)
* Simplified documentation: (https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow)
* Microsoft documentation: (https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow)

In order to request a token, you must have the client_id and client_secret of the confidential client.  Make the following call to obtain an access token:

POST <tokenEndpoint> - for the Microsoft Authorization server, this is:
`https://login.microsoftonline.com/<tenant_id>/oauth2/token` where `<tenant_id>` is the implementation-specific tenant ID.
Headers: 
* Content-Type: application/x-www-form-urlencoded

Body: 
* grant_type: client_credentials
* client_id: *as appropriate*
* client_secret: *as appropriate*
* resource: *FHIR Server's base url*

Response: 
JSON body with the following fields:
* token_type: "Bearer"
* expires_in: numer of seconds the token is valid
* ext_expires_in: numer of seconds the token is valid
* expires_on: Unix epoch (UTC) that the token expires
* not_before: Unix epoch (UTC) that the token becomes valid
* resource: FHIR Server's base url
* access_token: Access token