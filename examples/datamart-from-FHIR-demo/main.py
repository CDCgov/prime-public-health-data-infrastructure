<<<<<<< HEAD
from phdi_building_blocks.fhir import AzureFhirserverCredentialManager
=======
>>>>>>> 57cfa7c (Dan/initial fhir to parquet (#129))
from pathlib import Path
from phdi_building_blocks.schemas import (
    make_schema_tables,
    load_schema,
    print_schema_summary,
)

<<<<<<< HEAD

# Set required parameters

# Path to a schema config file. Included example used by default.
schema_path = "demo_schema.yaml"

# Path to directory where files will be written
output_path = "demo_schema"

# File format of tables
output_format = "parquet"

# The URL for a FHIR server
fhir_url = "https://pitest-fhir.azurehealthcareapis.com"
cred_manager = AzureFhirserverCredentialManager(fhir_url=fhir_url)
=======
# Set required parameters
schema_path = "example_schema.yaml"  # Path to a schema config file.
output_path = "example_schema"  # Path to directory where files will be written
output_format = "parquet"  # File format of tables
fhir_url = "your_fhir_url"  # The URL for a FHIR server
access_token = "your_access_token"  # Access token for authentication with FHIR server.
>>>>>>> 57cfa7c (Dan/initial fhir to parquet (#129))

# Make Schema
schema_path = Path(schema_path)
output_path = Path(output_path)
<<<<<<< HEAD
make_schema_tables(schema_path, output_path, output_format, fhir_url, cred_manager)
=======
make_schema_tables(schema_path, output_path, output_format, fhir_url, access_token)
>>>>>>> 57cfa7c (Dan/initial fhir to parquet (#129))

# Display Schema Summary
schema = load_schema(schema_path)
print_schema_summary(output_path, display_head=True)
