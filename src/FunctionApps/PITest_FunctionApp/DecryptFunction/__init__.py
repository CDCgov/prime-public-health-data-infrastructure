import azure.functions as func

from DecryptFunction import decrypt


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Get the message from the request and decrypt it.

    Args:
        req (func.HttpRequest): the request object.
        Pass the encrypted text in the body of the request.

    Returns:
        func.HttpResponse: the decrypted message
    """
    return decrypt.main_with_overload(req, None)
