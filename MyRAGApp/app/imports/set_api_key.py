import keyring
from imports.config import SERVICE_NAME, USERNAME

def set_api_key(api_key):
    """Save the API key to Windows Credential Manager."""
    keyring.set_password(
        SERVICE_NAME,
        USERNAME,
        api_key
    )

    return "Success", ""