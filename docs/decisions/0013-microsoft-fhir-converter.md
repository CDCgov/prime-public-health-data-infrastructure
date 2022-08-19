# 12. Initial Supported File Format

Date: 2022-08-19

## Status

Accepted

## Context and Problem Statement

Given that we have decided to design our buildings blocks around FHIR data, we need a solution for converting Hl7v2 and C-CDA to FHIR. Until recently, this was accomplished by using the `$convert-data` endpoint on the managed implementation of the [Microsoft FHIR server](https://github.com/microsoft/fhir-server) in Azure. However, we have begun porting our ingestion pipeline to Google Cloud Platform (GCP) where an implementation of the Microsoft FHIR server is not available. GCP refers to their implementation of a FHIR server as a [FHIR Store](https://cloud.google.com/healthcare-api/docs/reference/rest/v1/projects.locations.datasets.fhirStores) which does not have a `$convert-data` or similar endpoint. The reason for this is that a `$convert-data` endpoint is not specified as part of the [FHIR API](https://hl7.org/fhir/http.html) standard. In order to fully implement our pipeline in GCP and other platforms in the future we need a solution for FHIR conversion that can be used in any cloud environment or with on-prem infrastructure.     

## Decision Drivers

**Robustness** - The convert must be able to reliably and accurately convert data to FHIR. 

**Hl7v2 Support** - The converter must support the conversion of Hl7v2 to FHIR. 

**C-CDA Support** - The converter must support conversion of C-CDA to FHIR.

**Platform Agnostic** The converter should not depend on any functionality specific to an infrastructure provider.

**Ease of Implementation** - Ideally the converter will be easy implement in a variety of locations.


## Considered Options

### Microsoft FHIR Converter CLI

The [Microsoft FHIR Converter](https://github.com/microsoft/FHIR-Converter) is the conversion utility behind the `$convert-data` endpoint on the Microsoft FHIR server and also offers a CLI implementation.

Pros:
- The same conversion tool we are already familiar with
- Support for both Hl7v2 and C-CDA
- Can be installed on Windows, MacOS, and Linux systems.
- Open source and actively maintained by Microsoft.

Cons:
- Installation requires building from source.
- Written in C# with .NET framework making integration with PHDI's primarily Python based work challenging.

### LinuxForHealth FHIR Converter

The [LinuxForHealth FHIR Converter](https://github.com/LinuxForHealth/hl7v2-fhir-converter) is an open source Hl7v2 to FHIR conversion utility written in Java.

Pros:
- Supports Hl7v2
- Open source 
- Can be built on any system with a JVM.

Cons:
- Does not support C-CDA
- Installation process is non-trivial

### Report Stream Fhirengine

The Report Stream project is developing a FHIR conversion tool called [fhirengine](https://github.com/CDCgov/prime-reportstream/tree/master/prime-router/src/main/kotlin/fhirengine). It is open source, written in Kotlin, and supports bi-directional Hl7v2 and FHIR conversion.

Pros:
- Supports Hl7v2
- Supports conversion from FHIR back to Hl7v2.
- Can be built on any system with a JVM.
- Designed, built, and maintained by another project with in PRIME.

Cons:
- Does not support C-CDA.
- Installation process is non-trivial.
 

### CDC eCR Team FHIR Converter

The Electronic Case Reporting team at CDC is developing a FHIR conversion tool.

Pros:
- Supports C-CDA
- Developed by another team at CDC.

Cons:
- We believe that it does not support Hl7v2, but have not be able to confirm this.
- The eCR team has not be responsive to setting up a meeting to dsicuss their converter.

### GCP Healthcare Data Harmonization

The [GCP Healthcare Data Harmonization](https://github.com/GoogleCloudPlatform/healthcare-data-harmonization) engine offers tools for conversion from Hl7v2 and C-CDA to FHIR.

Pros:
- Supports Hlv2
- Supports C-CDA
- Open source

Cons:
- Documentation and examples do not seem to cover C-CDA conversion although reviewing the code base shows that C-CDA conversion is supported.
- Installation has several dependencies and is non-trivial


## Decision Outcome

**Microsoft FHIR Converter** 

Our need for conversion of both Hl7v2 and C-CDA eliminates all options except the Microsoft FHIR Converter and GCP Healthcare Data Harmonization engine. We have elected to move forward with Microsoft FHIR Converter for the following reasons:

- As a team we are already familiar with the Microsoft FHIR Converter.
- Although non-trivial the installation process is simpler than the GCP Healthcare Data Harmonization engine and has fewer dependencies.
- After installation the CLI makes the tool easy to use.
- We have been able to build a containerized application around this converter that makes its functionality availabe via an HTTP API and can be run on any platform that supports Docker containers.