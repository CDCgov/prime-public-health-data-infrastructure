import unittest

from unittest import mock
from Import import main

import json
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

    @mock.patch("requests.put")
    @mock.patch("requests.post")
    @mock.patch.dict("os.environ", TEST_ENV)
    def test_fhir_resource_put(self, mock_post, mock_put):
        token_resp = mock.Mock()
        token_resp.json.return_value = {"access_token": "some-access-token"}
        mock_post.return_value = token_resp

        fhir_json_req = {"resourceType": "Patient", "id": "test-id"}

        fhir_resp = mock.Mock()
        fhir_resp.json.return_value = fhir_json_req
        mock_put.return_value = fhir_resp

        url = os.environ.get("FHIR_URL")

        main.process_fhir_resource(fhir_json_req)

        mock_put.assert_called_with(
            f"{url}/{fhir_json_req['resourceType']}/{fhir_json_req['id']}",
            headers={
                "Authorization": "Bearer some-access-token",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            },
            data=json.dumps(fhir_json_req),
        )


    @mock.patch("requests.post")
    @mock.patch.dict("os.environ", TEST_ENV)
    def test_fhir_bundle_put(self, mock_post):

        url = os.environ.get("FHIR_URL")

        token_resp = mock.Mock()
        token_resp.json.return_value = {"access_token": "some-access-token"}

        fhir_json_orig = { 
            "resourceType": "Bundle",
            "type": "transaction",
            "id": "bundle-id",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient", 
                        "id": "test-id1"
                    }
                },
                {
                    "resource": {
                        "resourceType": "Patient", 
                        "id": "test-id2"
                    }
                }
            ]
        }

        fhir_json_req = { 
            "resourceType": "Bundle",
            "type": "transaction",
            "id": "bundle-id",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient", 
                        "id": "test-id1"
                    },
                    "request": {
                        "method": "PUT",
                        "url": f"{url}/Patient/test-id1"
                    }
                },
                {
                    "resource": {
                        "resourceType": "Patient", 
                        "id": "test-id2"
                    },
                    "request": {
                        "method": "PUT",
                        "url": f"{url}/Patient/test-id2"
                    }
                }
            ]
        }

        fhir_resp = mock.Mock()
        fhir_resp.json.return_value = fhir_json_req
        mock_post.side_effect = [token_resp, fhir_resp]

        main.process_fhir_resource(fhir_json_orig)

        mock_post.assert_called_with(
            f"{url}",
            headers={
                "Authorization": "Bearer some-access-token",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            },
            data=json.dumps(fhir_json_req),
        )


    def test_file_unzip(self):
        test_file_path = Path("BulkImport").parent / "tests" / "assets" / "test_files.zip"
        main._unzip_input_file(test_file_path)
        assert os.path.isfile("./FhirResources/test_files/Claim-1.ndjson")
        assert os.path.isfile("./FhirResources/test_files/Organization-1.ndjson")
        shutil.rmtree("./FhirResources")

if __name__ == '__main__':
    unittest.main()
