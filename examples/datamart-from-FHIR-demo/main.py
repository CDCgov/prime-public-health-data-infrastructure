from pathlib import Path
from phdi_building_blocks.schemas import (
    generate_schema,
    load_schema,
    get_schema_summary,
)

# Set required parameters
schema_path = "example_schema.yaml"  # Path to a schema config file. Included example used by default.
output_path = "."  # Path to directory where files will be written
output_format = "parquet"  # File format of tables
fhir_url = "placeholder URL"  # The URL for a FHIR server
access_token = (
    "placeholder access token"  # Access token for authentication with FHIR server.
)

# Make Schema
schema_path = Path(schema_path)
output_path = Path(output_path)
generate_schema(schema_path, output_path, output_format, fhir_url, access_token)

# Display Schema Summary
schema = load_schema(schema_path)
schema_directory = output_path / list(schema.keys())[0]
get_schema_summary(schema_directory, "." + output_format, display_head=True)
