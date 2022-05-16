import io
import FhirServerExport

from unittest import mock

ENVIRONMENT = {
    "FHIR_URL": "https://some-fhir-url",
    "POLLING_INTERVAL": 0.1,
    "POLLING_TIMEOUT": 1,
}


@mock.patch("FhirServerExport.process_resource")
@mock.patch("FhirServerExport.fhir.download_from_export_response")
@mock.patch("FhirServerExport.fhir.export_from_fhir_server")
@mock.patch("FhirServerExport.fhir.AzureFhirserverCredentialManager")
@mock.patch.dict("os.environ", ENVIRONMENT)
def test_main(mock_cred_manager, mock_export, mock_download, mock_process):
    req = mock.Mock()
    req.params = {
        "export_scope": "",
        "since": "",
        "type": "",
    }

    mock_get_access_token = mock.Mock()
    mock_get_access_token.return_value = "some-token"

    mock_cred_manager.get_access_token = mock_get_access_token

    export_return_value = {
        "output": [
            {"type": "Patient", "url": "https://some-export-url/_Patient"},
            {"type": "Observation", "url": "https://some-export-url/_Observation"},
        ]
    }

    mock_export.return_value = export_return_value

    mock_download.return_value = iter(
        [
            (
                "Patient",
                io.TextIOWrapper(
                    io.BytesIO(
                        b"{'resourceType':'Patient','id':'patient-id1'}\n"
                        + b"{'resourceType':'Patient','id':'patient-id2'}"
                    ),
                    encoding="utf-8",
                    newline="\n",
                ),
            ),
            (
                "Observation",
                io.TextIOWrapper(
                    io.BytesIO(
                        b"{'resourceType':'Observation','id':'observation-id1'}\n"
                        + b"{'resourceType':'Observation','id':'observation-id2'}"
                    ),
                    encoding="utf-8",
                    newline="\n",
                ),
            ),
        ]
    )

    FhirServerExport.main(req)

    mock_export.assert_called_with(
        access_token="some-token",
        fhir_url="https://some-fhir-url",
        export_scope="",
        since="",
        resource_step="",
        poll_step=0.1,
        poll_timeout=1,
    )

    mock_download.assert_called_with(export_return_value)

    mock_process.assert_has_calls(
        [
            mock.call({"resourceType": "Patient", "id": "patient-id1"}),
            mock.call({"resourceType": "Patient", "id": "patient-id2"}),
            mock.call({"resourceType": "Observation", "id": "observation-id1"}),
            mock.call({"resourceType": "Observation", "id": "observation-id2"}),
        ]
    )
