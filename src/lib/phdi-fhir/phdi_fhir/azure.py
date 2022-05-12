from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken

from datetime import datetime, timezone


class AzureFhirserverCredentialManager:
    """Manager for handling Azure credentials for access to the FHIR server"""

    def __init__(self, fhir_url):
        """Credential manager constructor"""
        self.access_token = None
        self.fhir_url = fhir_url

    def get_fhir_url(self):
        """Get FHIR URL"""
        return self.fhir_url

    def get_access_token(self, token_reuse_tolerance: float = 10.0) -> AccessToken:
        """If the token is already set for this object and is not about to expire
        (within token_reuse_tolerance parameter), then return the existing token.
        Otherwise, request a new one.
        :param str token_reuse_tolerance: Number of seconds before expiration
        it is OK to reuse the currently assigned token"""
        if not self._need_new_token(token_reuse_tolerance):
            return self.access_token

        creds = self._get_azure_credentials()
        scope = f"{self.fhir_url}/.default"
        self.access_token = creds.get_token(scope)

        return self.access_token

    def _get_azure_credentials(self):
        """Get default Azure Credentials from login context and related
        Azure configuration."""
        return DefaultAzureCredential()

    def _need_new_token(self, token_reuse_tolerance: float = 10.0) -> bool:
        """Determine whether the token already stored for this object can be reused, or if it
        needs to be re-requested.
        :param str token_reuse_tolerance: Number of seconds before expiration
        it is OK to reuse the currently assigned token"""
        try:
            current_time_utc = datetime.now(timezone.utc).timestamp()
            return (
                self.access_token.expires_on - token_reuse_tolerance
            ) < current_time_utc
        except AttributeError:
            # access_token not set
            return True


def get_fhirserver_cred_manager(fhir_url: str):
    """Get an instance of the Azure FHIR Server credential manager."""
    return AzureFhirserverCredentialManager(fhir_url)
