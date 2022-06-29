# 10. FHIRServer

Date: 2022-06-28

## Status

Accepted

## Context and Problem Statement

FHIR is a standardized data format that is used nationally to report health data. 

A FHIRServer assists in bringing together data from various systems into one common, readable dataset. The FHIRServer itself does not do any analytical work, but aims to normalize public health data. In the case of this project, public health data will be reported from a variety of sources such as prisons, pharamacies, schools, and hospitals. A FHIRServer will ingest the records and become a single source of truth for a public health agency's data. 

## Decision Drivers

**Integration with Existing Systems** - The CDC has an existing cloud environment so being able to work well with their existing system helps the development process. 

**Flexiblility** - 
While the team is developing the solution, flexibility is important as requirements are discovered. 

## Considered Options

### Google Cloud FHIR Server

Pros:
- Pay as you go
- Access to tools such as BigQuery

Cons:
- 

### Mircrosoft Azure FHIR Server

Pros:
- Robust documentation
- Support for both NoSQL (CosmoDB) and SQL 

Cons:
- If using CosmoDB, users must manage partitioning and set number of request units
- Pay-for-what-you-might-use model

### AWS FHIR Server

## Decision Outcome

Microsoft Azure FHIR Server

THe CDC's cloud environment is primarily in Azure so Azure FHIR Server would help speed up the development process. In addition, Azure FHIR Server supports both NoSQL and SQL solutions. Specifically, a SQL solution may fit best with our project as it helps maintain data integrity and table joins. 

## Appendix (OPTIONAL)

- [Virginia Department of Health White Paper](https://docs.google.com/document/d/17_AWGAPPdV-m7jZ0VZYtU1CtPt63Ri0zLNoorId5Gqc/edit?usp=sharing)
- [Microsoft FHIRServer](https://github.com/microsoft/fhir-server)
- [Are all FHIRServers the same?](https://vneilley.medium.com/are-all-fhir-apis-the-same-v2-e8d8359e1412)