import re
import json
import requests
from typing import List
from config import get_required_config


def clean_message(message: str, delimiter: str = "\n") -> str:
    cleaned_message = re.sub("[\r\n]+", delimiter, message)

    # These are unicode for vertical tab and file separator, respectively
    # \u000b appears before every MSH segment, and \u001c appears at the
    # end of the message in some of the data we've been receiving, so
    # we're explicitly removing them here.
    cleaned_message = re.sub("[\u000b\u001c]", "", cleaned_message).strip()
    return cleaned_message


# This method was adopted from PRIME ReportStream, which can be found here:
# https://github.com/CDCgov/prime-reportstream/blob/194396582be02fcc51295089f20b0c2b90e7c830/prime-router/src/main/kotlin/serializers/Hl7Serializer.kt#L121
def convert_batch_messages_to_list(
    content: str,
    delimiter: str = "\n"
) -> List[str]:
    """
    FHS is a "File Header Segment", which is used to head a file (group of batches)
    FTS is a "File Trailer Segment", which defines the end of a file
    BHS is "Batch Header Segment", which defines the start of a batch
    BTS is "Batch Trailer Segment", which defines the end of a batch

    The structure of an HL7 Batch looks like this:
    [FHS] (file header segment) { [BHS] (batch header segment)
    { [MSH (zero or more HL7 messages)
    ....
    ....
    ....
    ] }
    [BTS] (batch trailer segment)
    }
    [FTS] (file trailer segment)

    We ignore lines that start with these since we don't want to include
    them in a message
    """

    cleaned_message = clean_message(content)
    message_lines = cleaned_message.split(delimiter)
    next_message = ""
    output = []

    for line in message_lines:
        if line.startswith("FHS"):
            continue
        if line.startswith("BHS"):
            continue
        if line.startswith("BTS"):
            continue
        if line.startswith("FTS"):
            continue

        # If we reach a line that starts with MSH and we have
        # content in nextMessage, then by definition we have
        # a full message in next_message and need to append it
        # to output. This will not trigger the first time we
        # see a line with MSH since next_message will be empty
        # at that time.
        if next_message != "" and line.startswith("MSH"):
            output.append(next_message)
            next_message = ""

        # Otherwise, continue to add the line of text to next_message
        if line != "":
            next_message += f"{line}\r"

    # Since our loop only adds messages to output when it finds
    # a line that starts with MSH, the last message would never
    # be added. So we explicitly add it here.
    if next_message != "":
        output.append(next_message)

    return output


def convert_message_to_fhir(
    message: str,
    message_format: str,
    message_type: str,
    access_token: str
) -> str:
    message_format_map = {
        "hl7v2": "Hl7v2",
        "ccda": "Ccda",
        "json": "Json"
    }

    message_type_map = {
        "adt_a01": "ADT_A01",
        "oml_o21": "OML_O21",
        "oru_r01": "ORU_R01",
        "vxu_v04": "VXU_V04",
        "ccd": "CCD",
        "ccda": "CCD",
        "consultationnote": "ConsultationNote",
        "dischargesummary": "DischargeSummary",
        "historyandphysical": "HistoryandPhysical",
        "operativenote": "OperativeNote",
        "procedurenote": "ProcedureNote",
        "progressnote": "ProgressNote",
        "referralnote": "ReferralNote",
        "transfersummary": "TransferSummary",
        "examplepatient": "ExamplePatient",
        "stu3chargeitem": "Stu3ChargeItem"
    }

    template_map = {
        "Hl7v2": "microsofthealth/fhirconverter:default",
        "Ccda": "microsofthealth/ccdatemplates:default",
        "Json": "microsofthealth/jsontemplates:default",
    }

    input_data_type = message_format_map.get(message_format.lower())
    root_template = message_type_map.get(message_type.lower())
    template_collection = template_map.get(
        input_data_type,
        "microsofthealth/hl7v2templates:default"
    )

    if input_data_type is None or root_template is None:
        raise Exception("Unknown file format or message type")

    url = f"{get_required_config('FHIR_URL')}/$convert-data"
    data = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "inputData", "valueString": message},
            {"name": "inputDataType", "valueString": input_data_type},
            {"name": "templateCollectionReference", "valueString": template_collection},
            {"name": "rootTemplate", "valueString": root_template}
        ]
    }
    
    data = json.dumps(data)

    response = requests.post(
        url=url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )

    return response
