import unittest

from unittest import mock
from IntakePipeline import fhir

import json
import os
<<<<<<< HEAD

=======
import shutil
from pathlib import Path
>>>>>>> a46258b (Upload to FHIR server)

class TestFhir(unittest.TestCase):
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

        assert "some-access-token" == fhir.get_access_token()

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

        fhir.process_fhir_resource(fhir_json_req)

        mock_put.assert_called_with(
            f"{url}/{fhir_json_req['resourceType']}/{fhir_json_req['id']}",
            headers={
                "Authorization": "Bearer some-access-token",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            },
            data=json.dumps(fhir_json_req),
        )

<<<<<<< HEAD
=======

>>>>>>> a46258b (Upload to FHIR server)
    @mock.patch("requests.post")
    @mock.patch.dict("os.environ", TEST_ENV)
    def test_fhir_bundle_put(self, mock_post):

        url = os.environ.get("FHIR_URL")

        token_resp = mock.Mock()
        token_resp.json.return_value = {"access_token": "some-access-token"}

<<<<<<< HEAD
        fhir_json_orig = {
=======
        fhir_json_orig = { 
>>>>>>> a46258b (Upload to FHIR server)
            "resourceType": "Bundle",
            "type": "transaction",
            "id": "bundle-id",
            "entry": [
<<<<<<< HEAD
                {"resource": {"resourceType": "Patient", "id": "test-id1"}},
                {"resource": {"resourceType": "Patient", "id": "test-id2"}},
            ],
        }

        fhir_json_req = {
=======
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
>>>>>>> a46258b (Upload to FHIR server)
            "resourceType": "Bundle",
            "type": "transaction",
            "id": "bundle-id",
            "entry": [
                {
<<<<<<< HEAD
                    "resource": {"resourceType": "Patient", "id": "test-id1"},
                    "request": {"method": "PUT", "url": "Patient/test-id1"},
                },
                {
                    "resource": {"resourceType": "Patient", "id": "test-id2"},
                    "request": {"method": "PUT", "url": "Patient/test-id2"},
                },
            ],
=======
                    "resource": {
                        "resourceType": "Patient", 
                        "id": "test-id1"
                    },
                    "request": {
                        "method": "PUT",
                        "url": f"Patient/test-id1"
                    }
                },
                {
                    "resource": {
                        "resourceType": "Patient", 
                        "id": "test-id2"
                    },
                    "request": {
                        "method": "PUT",
                        "url": f"Patient/test-id2"
                    }
                }
            ]
>>>>>>> a46258b (Upload to FHIR server)
        }

        fhir_resp = mock.Mock()
        fhir_resp.json.return_value = fhir_json_req
        mock_post.side_effect = [token_resp, fhir_resp]

        fhir.process_fhir_resource(fhir_json_orig)

        mock_post.assert_called_with(
            f"{url}",
            headers={
                "Authorization": "Bearer some-access-token",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json",
            },
            data=json.dumps(fhir_json_req),
        )
