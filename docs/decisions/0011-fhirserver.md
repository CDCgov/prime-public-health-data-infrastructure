# 11. FHIR Server

Date: 2022-06-28

## Status

Accepted

## Context and Problem Statement

FHIR is a standardized data format that is used nationally to report health data. 

A FHIR Server assists in bringing together data from various systems into one common, readable dataset. The FHIR Server itself does not do any analytical work, but aims to normalize public health data. In the case of this project, public health data will be reported from a variety of sources such as prisons, pharamacies, schools, and hospitals. A FHIR Server will ingest the records and become a single source of truth for a public health agency's data. 


## Decision Drivers

**Integration with Existing Systems** - The CDC has an existing cloud environment (Azure) so being able to work well with their existing system helps the development process. The team is working to get the first version into production so ease of maintainability and integration are important. 

**Flexiblility** - While the team is developing the solution, flexibility is important as requirements are being discovered. 

## Considered Options

### Google Cloud FHIR Server

Google Cloud FHIR service has tight integration with other GCP products such as BigQuery, Storage, Pub/Sub Integration

Pros:
- In GCP FHIR Server, you pay for what you use. This advantage would be key if demand is unpredictable or high variance. 
- Access to tools such as BigQuery for data analytics. 
- Supports all versions of FHIR

Cons:
- More expensive for storage and API calls

### AWS FHIR Works

AWS FHIRWorks is Amazon's FHIR Server product that integrates with AWS services such as DynamoDB, Elasticsearch, Lambda, etc.

Pros:
- FHIR Works is the cheapest of the three options 
- Integrates with natural language processing services for specific medical use cases.

Cons:
- Does not support certain key features such as patch calls, bundles, or conditionals

### Mircrosoft Azure FHIR Server

Azure FHIR server is Azure's FHIR server product that allows developers to create FHIR applications using Azure products.

Pros:
- Since the CDC already uses Azure, using Azure FHIR server will be easier to integrate with their existing system. 
- Azure FHIR server supports both NoSQL (CosmoDB) and SQL. Azure is pushing more features on to their SQL solution. 

Cons:
- If using CosmoDB, users must manage partitioning and set number of request units
- Pay-for-what-you-might-use model. Currently Azure is running on a prepaid system which may be worse for unpredictable demand.
- Certain search and API features are missing in Azure that is supported by GCP


## Decision Outcome

Microsoft Azure FHIR Server

THe CDC's cloud environment is primarily in Azure so Azure FHIR Server would help speed up the development process. In addition, Azure FHIR Server supports both NoSQL and SQL solutions. Specifically, a SQL solution may fit best with our project as it helps maintain data integrity and table joins. 

Should the team learn that there is certain key features missing in Azure FHIR Server, re-evaluating GCP FHIR Server may be the next best option.

## Appendix 

- [Virginia Department of Health White Paper](https://docs.google.com/document/d/17_AWGAPPdV-m7jZ0VZYtU1CtPt63Ri0zLNoorId5Gqc/edit?usp=sharing)
- [Microsoft FHIR Server](https://github.com/microsoft/fhir-server)
- [Are all FHIR APIs the same?](https://vneilley.medium.com/are-all-fhir-apis-the-same-v2-e8d8359e1412)