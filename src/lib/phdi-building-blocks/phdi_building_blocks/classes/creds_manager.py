from datetime import datetime, timezone

from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential


class AzureFhirserverCredentialManager:
    """
    A class that manages handling Azure credentials for access to the FHIR server.
    """

    def __init__(self, fhir_url: str):
        """
        Constructor to create a credential manager.
        :param str fhir_url: The url of the FHIR server to-access
        """
        self.access_token = None
        self.fhir_url = fhir_url

    def get_fhir_url(self) -> str:
        """
        Getter to retrieve the FHIR URL.
        :return: The FHIR url
        :rtype: str
        """
        return self.fhir_url

    def get_access_token(self, token_reuse_tolerance: float = 10.0) -> AccessToken:
        """
        Obtain an access token for the FHIR server the manager is pointed at.
        If the token is already set for this object and is not about to expire
        (within token_reuse_tolerance parameter), then return the existing token.
        Otherwise, request a new one.
        :param float token_reuse_tolerance: Number of seconds before expiration; it
        is okay to reuse the currently assigned token
        :return: The AccessToken the manager is currently using
        :rtype: AccessToken
        """
        if not self._need_new_token(token_reuse_tolerance):
            return self.access_token

        # Obtain a new token if ours is going to expire soon
        creds = self._get_azure_credentials()
        scope = f"{self.fhir_url}/.default"
        self.access_token = creds.get_token(scope)
        return self.access_token

    def _get_azure_credentials(self):
        """
        Get default Azure Credentials from login context and related
        Azure configuration.
        :return: A set of default Azure credentials
        """
        return DefaultAzureCredential()

    def _need_new_token(self, token_reuse_tolerance: float = 10.0) -> bool:
        """
        Determine whether the token already stored for this object can be reused,
        or if it needs to be re-requested.
        :param float token_reuse_tolerance: Number of seconds before expiration
        :return: Whether we need a new token (True means we do)
        :rtype: bool
        """
        try:
            current_time_utc = datetime.now(timezone.utc).timestamp()
            return (
                self.access_token.expires_on - token_reuse_tolerance
            ) < current_time_utc
        except AttributeError:
            # access_token not set
            return True
