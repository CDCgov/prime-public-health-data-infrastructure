import unittest

from unittest import mock
from Import import main
import requests

import os
import shutil
from pathlib import Path

class TestImport(unittest.TestCase):
    TEST_ENV = {
        "TENANT_ID": "a-tenant-id",
        "CLIENT_ID": "a-client-id",
        "CLIENT_SECRET": "a-client-secret",
        "FHIR_URL": "https://some-fhir-server",
    }

    @mock.patch("requests.post")
    @mock.patch.dict("os.environ", TEST_ENV)
    def test_get_access_token(self, mock_post):
        resp = mock.Mock()
        resp.json.return_value = {"access_token": "some-access-token"}
        mock_post.return_value = resp

        assert "some-access-token" == main.get_access_token()

        mock_post.assert_called_with(
            "https://login.microsoftonline.com/a-tenant-id/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "a-client-id",
                "client_secret": "a-client-secret",
                "resource": "https://some-fhir-server",
            },
        )

    @mock.patch("requests.post")
    @mock.patch.dict("os.environ", TEST_ENV)
    def test_fhir_post(self, mock_post):
        token_resp = mock.Mock()
        token_resp.json.return_value = {"access_token": "some-access-token"}

        fhir_resp = mock.Mock()
        fhir_resp.json.return_value = {"resourceType": "Patient", "id": "test-id"}
        
        mock_post.side_effect = [token_resp, fhir_resp]

        url = os.environ.get("FHIR_URL")
        calls = [mock.call(
            "https://login.microsoftonline.com/a-tenant-id/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "a-client-id",
                "client_secret": "a-client-secret",
                "resource": "https://some-fhir-server",
            }),
            mock.call(
                f"{url}/Patient",
                headers={
                    "Authorization": mock.ANY,
                    "Accept": "application/fhir+json",
                    "Content-Type": "application/fhir+json",
                },
                data={"resourceType": "Patient", 
                "id": "test-id"},                
            )]

        main.process_fhir_resource(fhir_string = "{\"resourceType\": \"Patient\", \"id\": \"test-id\"}")

        mock_post.assert_called_with(
            f"{url}/Patient",
            headers={
                "Authorization": mock.ANY,
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            },
            data={"resourceType": "Patient", "id": "test-id"},
        )


    def test_file_unzip(self):
        test_file_path = Path("BulkImport").parent / "tests" / "assets" / "test_files.zip"
        main._unzip_input_file(test_file_path)
        assert os.path.isfile("./FhirResources/test_files/Claim-1.ndjson")
        assert os.path.isfile("./FhirResources/test_files/Organization-1.ndjson")
        shutil.rmtree("./FhirResources")

if __name__ == '__main__':
    unittest.main()
