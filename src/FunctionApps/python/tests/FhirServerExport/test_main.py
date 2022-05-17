import io
import logging

from FhirServerExport import main
from phdi_building_blocks.fhir import AzureFhirserverCredentialManager

from unittest import mock

ENVIRONMENT = {
    "FHIR_URL": "https://some-fhir-url",
    "FHIR_EXPORT_POLL_INTERVAL": "0.1",
    "FHIR_EXPORT_POLL_TIMEOUT": "1",
}


@mock.patch("FhirServerExport.process_resource")
@mock.patch("FhirServerExport.fhir.download_from_export_response")
@mock.patch("FhirServerExport.fhir.export_from_fhir_server")
@mock.patch.object(AzureFhirserverCredentialManager, "get_access_token")
@mock.patch.dict("os.environ", ENVIRONMENT)
def test_main(mock_get_access_token, mock_export, mock_download, mock_process):
    logging.basicConfig(level=logging.DEBUG)
    req = mock.Mock()
    req.params = {
        "export_scope": "",
        "since": "",
        "type": "",
    }

    mock_get_access_token.return_value = "some-token"

    export_return_value = {
        "output": [
            {"type": "Patient", "url": "https://some-export-url/_Patient"},
            {"type": "Observation", "url": "https://some-export-url/_Observation"},
        ]
    }

    mock_export.return_value = export_return_value

    patient_response = io.TextIOWrapper(
        io.BytesIO(
            b'{"resourceType": "Patient", "id": "patient-id1"}\n'
            + b'{"resourceType": "Patient", "id": "patient-id2"}'
        ),
        encoding="utf-8",
        newline="\n",
    )
    patient_response.seek(0)

    observation_response = io.TextIOWrapper(
        io.BytesIO(
            b'{"resourceType": "Observation", "id": "observation-id1"}\n'
            + b'{"resourceType": "Observation", "id": "observation-id2"}'
        ),
        encoding="utf-8",
        newline="\n",
    )
    observation_response.seek(0)

    mock_download.return_value = iter(
        [
            (
                "Patient",
                patient_response,
            ),
            (
                "Observation",
                observation_response,
            ),
        ]
    )

    main(req)

    mock_export.assert_called_with(
        access_token="some-token",
        fhir_url="https://some-fhir-url",
        export_scope="",
        since="",
        resource_type="",
        poll_step=0.1,
        poll_timeout=1.0,
    )

    mock_download.assert_called_with(export_return_value)

    mock_process.assert_has_calls(
        [
            mock.call(resource={"resourceType": "Patient", "id": "patient-id1"}),
            mock.call(resource={"resourceType": "Patient", "id": "patient-id2"}),
            mock.call(
                resource={"resourceType": "Observation", "id": "observation-id1"}
            ),
            mock.call(
                resource={"resourceType": "Observation", "id": "observation-id2"}
            ),
        ]
    )
