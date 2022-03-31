#!/usr/bin/env python3 

from cgi import test
import fileinput
import hl7apy
from hl7apy.core import Message
import typing

config_file: str = ".anonymize.config.json"

def anonymize_hl7_file(hl7_input_file: str, hl7_output_file: str):
    outfile = open(hl7_output_file, 'w')

    # Read character by character because
    #  a) segments are often delimited by \r, which python doesn't recognize as a new line
    #  b) other mechanisms to split up messages (e.g. split(), hl7.parse_batch(), etc.) 
    #     parse the whole file at once and may cause memory issues for large files.

    
    startofline = True
    thislinestr = ""
    messagestr = ""
    message = None
    with open(hl7_input_file, mode = 'r', newline='') as infile:

        # Loop over input file line by line
        for line in infile:

            # Detect we need to start a new message
            if line[:3] == "MSH":

                # Anonymize previously read message and write to output file
                if messagestr != "":
                    message = hl7apy.parser.parse_message(messagestr)
                    anon_message = anonymize_hl7_message(message)
                    outfile.write(anon_message.to_er7())
                    
                # Start a new message
                messagestr = ""
                if len(line) >= 3:
                    messagestr = line
                continue
                    
            # Continue building message
            else:
                # Basic validation - must at least be long enough for a segment identifier
                    messagestr += line

        # After reading all input, write to file
        if messagestr != "":
            message = hl7apy.parser.parse_message(messagestr)
            anon_message = anonymize_hl7_message(message)
            outfile.write(anon_message.to_er7())


def anonymize_hl7_message(hl7_message: hl7apy.core.Message) -> hl7apy.core.Message:
    # test
    hl7_message.





