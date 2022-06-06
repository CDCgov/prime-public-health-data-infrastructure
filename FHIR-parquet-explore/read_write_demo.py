from pathlib import Path
from phdi_building_blocks.schemas import (
    generate_schema,
    load_schema,
    get_schema_summary,
)

if __name__ == "__main__":

    # Make Schema
    fhir_url = "https://phdi-pilot.azurehealthcareapis.com"
    schema_path = Path("schema.yml")
    output_path = Path("")
    output_format = "parquet"
    generate_schema(fhir_url, schema_path, output_path, output_format)

    # Display Schema Summary
    schema = load_schema(schema_path)
    schema_directory = output_path / list(schema.keys())[0]
    get_schema_summary(schema_directory, ".parquet", display_head=True)
