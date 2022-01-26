import os


class Settings:
    hostname = os.environ.get("VDHSFTPHostname")
    username = os.environ.get("VDHSFTPUsername")
    password = os.environ.get("VDHSFTPPassword")
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")


settings = Settings()
