# 13. Microsoft FHIR Converter

Date: 2022-08-25

## Status

Accepted

## Context and Problem Statement

Given that we have decided to design our buildings blocks around FHIR data, we need a solution for converting Hl7v2 and C-CDA to FHIR. Until recently, this was accomplished by using the `$convert-data` endpoint on the managed implementation of the [Microsoft FHIR server](https://github.com/microsoft/fhir-server) in Azure. However, we have begun porting our ingestion pipeline to Google Cloud Platform (GCP) where an implementation of the Microsoft FHIR server is not available. GCP refers to their implementation of a FHIR server as a [FHIR Store](https://cloud.google.com/healthcare-api/docs/reference/rest/v1/projects.locations.datasets.fhirStores) which does not have a `$convert-data` or similar endpoint. The reason for this is that a `$convert-data` endpoint is not specified as part of the [FHIR API](https://hl7.org/fhir/http.html) standard. In order to fully implement our pipeline in GCP and other platforms in the future we need a solution for FHIR conversion that can be used in any cloud environment or with on-prem infrastructure.     

## Decision Drivers

**Robustness** - The converter must be able to reliably and accurately convert data to FHIR. It should be as lossless as possible.

**Hl7v2 Support** - The converter must support the conversion of Hl7v2 to FHIR. 

**C-CDA Support** - The converter must support conversion of C-CDA to FHIR.

**Platform Agnostic** - The converter should not depend on features specific to any cloud or on-prem infrastructure provider or implementation.

**Ease of Implementation** - Ideally the converter will be easy to implement in a variety of locations.

**Extensibility** - With proper configuration and/or templates the converter should be able to handle a wide variety of Hl7v2 and C-CDA messages, including those that the PHDI team is not yet aware of.


## Considered Options

### Microsoft FHIR Converter CLI

The [Microsoft FHIR Converter](https://github.com/microsoft/FHIR-Converter) is the conversion utility behind the `$convert-data` endpoint on the Microsoft FHIR server and also offers a CLI implementation.

Pros:
- The same conversion tool that we had success with in our pilot with VA.
- Supports both Hl7v2, C-CDA, and STU3.
- Provides 57 conversion templates for different Hl7v2 messages.
- Provides 10 conversion templates for different C-CDA messages.
- Extensible via the Liquid templating language.
- Can be installed on Windows, MacOS, and Linux systems.
- Open source and actively maintained by Microsoft.

Cons:
- Installation requires building from source.
- Written in C# with .NET framework making integration with PHDI's primarily Python based work challenging.
- Non-Windows users must have .NET installed.

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
- Supports Hl7v2 ORU_R01.
- Supports conversion from FHIR back to Hl7v2 ORU_R01.
- Can be built on any system with a JVM.
- Designed, built, and maintained by another project within PRIME.

Cons:
- Only supports Hl7v2 RU_R01, not the entire Hl7v2 standard.
- Does not support C-CDA.
- Installation process is non-trivial.
 

### CDC eCR Team FHIR Converter

The Electronic Case Reporting team at CDC is developing a FHIR conversion tool.

Pros:
- Supports C-CDA
- Developed by another team at CDC.

Cons:
- Does not support Hl7v2.
- The source code for this tool is not readily available, and the documentation is sparse, making it hard to assess the tool's suitability.

### GCP Healthcare Data Harmonization

The [GCP Healthcare Data Harmonization](https://github.com/GoogleCloudPlatform/healthcare-data-harmonization) offers a generic engine for conversion of data from one format to another, including from Hl7v2 and C-CDA to FHIR.

Pros:
- Supports Hl7v2
- Supports C-CDA
- Open source
- Extensible via the Whistle Data Transformation Language.

Cons:
- Documentation and examples do not seem to cover C-CDA conversion although reviewing the code base shows that C-CDA conversion is supported.
- Templates for conversion of specific Hl7v2 and C-CDA message types are not provided.
- Has several dependencies including Go, Cland, JavaJDK, and Protobuf Complier.
- Installation is non-trivial


## Decision Outcome

**Microsoft FHIR Converter** 

Our need for conversion of both Hl7v2 and C-CDA eliminates all options except the Microsoft FHIR Converter and GCP Healthcare Data Harmonization engine. We have elected to move forward with Microsoft FHIR Converter for the following reasons:

- We had success with the Microsoft FHIR Converter during our pilot with Virginia.
- The 67 provided templates are a valuable assest.
    - These templates have met our needs so far for the conversion of ELR, VXU, and eCR messages.
    - It is reasonable that one of the 26 templates for Hl7v2 ADT messages will meet our needs in our upcommong pilot with LA Country where we plan to begin ingesting ADT data. If none of the ADT templates are sufficient they will be usefull resources for writting our own. 
- Although non-trivial, the installation process is simpler than the GCP Healthcare Data Harmonization engine and has fewer dependencies.
- After installation, the CLI makes the tool easy to use.
