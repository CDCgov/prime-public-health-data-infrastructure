from pathlib import Path
from phdi_building_blocks.schemas import (
    generate_schema,
    load_schema,
    get_schema_summary,
)


# Set required parameters
fhir_url = "placeholder URL"  # The URL for a FHIR server
schema_path = "example_schema.yaml"  # Path to a schema config file. We use an example here by default
output_path = "."  # Path to directory where files should be written
output_format = "parquet"  # File format of tables

# Make Schema
schema_path = Path(schema_path)
output_path = Path(output_path)
generate_schema(fhir_url, schema_path, output_path, output_format)

# Display Schema Summary
schema = load_schema(schema_path)
schema_directory = output_path / list(schema.keys())[0]
get_schema_summary(schema_directory, "." + output_format, display_head=True)
