from unittest import mock

from IntakePipeline import run_pipeline


TEST_ENV = {
    "INTAKE_CONTAINER_URL": "some-url",
    "INTAKE_CONTAINER_PREFIX": "some-prefix",
    "VALID_OUTPUT_CONTAINER_PATH": "output/path",
    "HASH_SALT": "super-secret-definitely-legit-passphrase",
    "SMARTYSTREETS_AUTH_ID": "smarty-auth-id",
    "SMARTYSTREETS_AUTH_TOKEN": "smarty-auth-token",
    "FHIR_URL": "fhir-url",
}


@mock.patch("IntakePipeline.transform_bundle")
@mock.patch("IntakePipeline.add_patient_identifier")
@mock.patch("IntakePipeline.upload_bundle_to_fhir_server")
@mock.patch("IntakePipeline.store_bundle")
@mock.patch("IntakePipeline.get_smartystreets_client")
@mock.patch.dict("os.environ", TEST_ENV)
def test_basic_pipeline(
    patched_get_geocoder,
    patched_store,
    patched_upload,
    patched_patient_id,
    patched_transform,
):

    patched_geocoder = mock.Mock()
    patched_get_geocoder.return_value = patched_geocoder

    cred_manager = mock.Mock()
    run_pipeline({"hello": "world"}, "VXU", cred_manager)

    patched_get_geocoder.assert_called_with("smarty-auth-id", "smarty-auth-token")
    patched_transform.assert_called_with(patched_geocoder, {"hello": "world"})
    patched_patient_id.assert_called_with(TEST_ENV["HASH_SALT"], {"hello": "world"})
    patched_upload.assert_called_with(cred_manager, {"hello": "world"})
    patched_store.assert_called_with(
        "some-url", "output/path", {"hello": "world"}, "VXU"
    )
