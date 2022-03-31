#!/usr/bin/env python3 

from bdb import Breakpoint
import hl7
import hl7apy
from hl7apy import parser
from hl7apy.core import Message
from hl7apy.core import Segment
import yaml
import random
import copy
import sys


class Anonymizer:

    config_filename: str = "anonymize.config.yml"

    config: object

    anon_cache: dict = {}

    def __init__(self, config_filename : str = None):
        if config_filename is None:
            config_filename = self.config_filename
        else:
            self.config_filename = config_filename

        
        config_file = open(config_filename, 'r')
        self.config = yaml.load(config_file,yaml.FullLoader)
        
    def anonymize_hl7_file(self, hl7_input_file: str, hl7_output_file: str) -> None:
        
        outfile = open(hl7_output_file, 'w')

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
                        outfile.write(self.anonymize_hl7_message(messagestr))
                        messagestr = ""
                        
                    # Start a new message
                    messagestr = line
                    continue
                        
                # Continue building message
                else:
                    # Basic validation - must at least be long enough for a segment identifier
                    messagestr += line

            # After reading all input, process final message
            if messagestr != "":
                outfile.write(self.anonymize_hl7_message(messagestr))

    def anonymize_hl7_message_temp(self, messagestr: str) -> str:
        breakpoint()
        hl7_message = hl7.parse(messagestr)
        cache_key = hl7_message.segment('PID')[3]
        if cache_key == "":
            cache_key = hl7_message.pid.pid_2.value
        if cache_key == "":
            cache_key = hl7_message.pid.pid_4.value
        if cache_key == "":
            raise RuntimeError("Patient ID not found.")


        segment = None  # type: Segment
        anon_cache_entry = self._get_anon_cache_entry(cache_key)

        anon_hl7_message = hl7_message
        for segment in anon_hl7_message.children:
            if segment.name == 'PID':
                anon_name_family = self._get_anon_cache_entry_value(cache_key, "pid.pid_5.pid_5_1")
                if anon_name_family == "":
                    anon_name_family = random.choice(self.config['names']['family'])
                    self._set_anon_cache_entry_value(cache_key,"pid.pid_5.pid_5_1",anon_name_family)
                hl7_message.pid.pid_5.pid_5_1 = anon_name_family
                print("Random family name: " + anon_name_family)

                anon_name_given = self._get_anon_cache_entry_value(cache_key, "pid.pid_5.pid_5_2")
                if anon_name_given == "":
                    gender = segment.pid_8
                    if gender not in ['M', 'F']:
                        gender = random.choice(['M', 'F'])
                    
                    if gender == 'M':
                        anon_name_given = random.choice(self.config['names']['male'])
                    else:
                        anon_name_given = random.choice(self.config['names']['female'])
                    self._set_anon_cache_entry_value(cache_key,"pid.pid_5.pid_5_2",anon_name_given)
                hl7_message.pid.pid_5.pid_5_2 = anon_name_given
                print("Random given name: " + anon_name_given)
        
        return anon_hl7_message.to_er7()


    def anonymize_hl7_message(self, messagestr: str) -> str:
        hl7_message = hl7.parse(messagestr) # type: hl7.Message
        cache_key = str(hl7_message.segment('PID')[3][0])
        if cache_key == "":
            cache_key = str(hl7_message.segment('PID')[3][0])
        if cache_key == "":
            cache_key = str(hl7_message.segment('PID')[3][0])
        if cache_key == "":
            raise RuntimeError("Patient ID not found.")


        segment = None  # type: Segment
        anon_cache_entry = self._get_anon_cache_entry(cache_key)

        for segment in hl7_message.segments('PID'):
            anon_name_family = self._get_anon_cache_entry_value(cache_key, "pid.pid_5.pid_5_1")
            if anon_name_family == "":
                anon_name_family = random.choice(self.config['names']['family'])
                self._set_anon_cache_entry_value(cache_key,"pid.pid_5.pid_5_1",anon_name_family)
            hl7_message.assign_field(anon_name_family, 'PID',1,5,1,1)
            print("Random family name: " + anon_name_family)

            anon_name_given = self._get_anon_cache_entry_value(cache_key, "pid.pid_5.pid_5_2")
            if anon_name_given == "":
                gender = hl7_message.extract_field('PID',1,8,1)
                if gender not in ['M', 'F']:
                    gender = random.choice(['M', 'F'])
                
                if gender == 'M':
                    anon_name_given = random.choice(self.config['names']['male'])
                else:
                    anon_name_given = random.choice(self.config['names']['female'])
                self._set_anon_cache_entry_value(cache_key,"pid.pid_5.pid_5_2",anon_name_given)
            hl7_message.assign_field(anon_name_given, 'PID',1,5,1,2)
            print("Random given name: " + anon_name_given)
        
        return str(hl7_message)


    @classmethod
    def _get_anon_cache_entry(cls, cache_key: str) -> dict:
        if cache_key not in cls.anon_cache:
            cls.anon_cache[cache_key] = {}
        return cls.anon_cache[cache_key]

    @classmethod
    def _get_anon_cache_entry_value(cls, cache_key: str, property_path: str) -> str:
        anon_cache_entry = cls._get_anon_cache_entry(cache_key)
        if property_path not in anon_cache_entry:
            anon_cache_entry[property_path] = ""
        return anon_cache_entry[property_path]

    @classmethod
    def _set_anon_cache_entry_value(cls, cache_key: str, property_path: str, value: str) -> None:
        anon_cache_entry = cls._get_anon_cache_entry(cache_key)
        anon_cache_entry[property_path] = value

if __name__ == "__main__":
    anonymizer = Anonymizer()
    anonymizer.anonymize_hl7_file(sys.argv[1], sys.argv[1] + ".anon")
    