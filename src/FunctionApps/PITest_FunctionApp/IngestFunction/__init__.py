import logging
import pysftp
import sys
import azure.functions as func
from .settings import settings


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    logging.info(f"Settings: {settings}")

    try:
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None   
        sftp = pysftp.Connection(
            settings["hostname"],
            username=settings["username"],
            password=settings["password"],
            cnopts=cnopts
        )
        for filename in sftp.listdir("/"):
            logging.info(f"filename: {filename}")

        return func.HttpResponse(f"This HTTP triggered function executed successfully.")
    except:
        e = sys.exc_info()
        logging.error(f"Exception: {e}, Traceback: {e[2]}")
        return func.HttpResponse(f"Error in response: {e}", status_code=500)
