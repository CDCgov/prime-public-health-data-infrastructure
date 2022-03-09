from dataclasses import dataclass
import os


@dataclass
class DecryptSettings:
    """Settings necessary for decrypting a given message.
    When run remotely, settings are passed by environment variables in the function app,
    which in turn reference KeyVault variables as mentioned here:
    https://docs.microsoft.com/en-us/azure/app-service/app-service-key-vault-references

    When tests are run, these settings are read from the local file `test.settings.json`
    which contains a different pgp key that is only used for tests and is not stored in
    the KeyVault.
    """

    private_key_password = os.getenv("PRIVATE_KEY_PASSWORD")
    private_key = os.getenv("PRIVATE_KEY")
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
