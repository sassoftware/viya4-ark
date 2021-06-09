####################################################################
# ### structured_logging.parser.py                               ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import json

from typing import AnyStr, Dict, List, Optional, Text

from viya_ark_library.structured_logging.spec import SASStructuredLoggingSpec


class SASStructuredLoggingParser(object):
    """
    Class providing methods for parsing SAS structured logging.
    """

    @staticmethod
    def parse_log(log: List[AnyStr]) -> List[Text]:
        """
        Parses a log file (given as a list of entries) and returns a traditionally formatted list of log entries for
        better human-readability. Any entries in the provided log that cannot be decoded from a structured log format
        will be returned as-is.

        :param log: List of log entries to parse
        :return: List of traditionally formatted log entries
        """
        # create a list to hold the unstructured log entries
        unstructured_log: List[Text] = list()

        # iterate over each entry in the provided log
        for log_entry in log:
            # add the unstructured entry to the list
            unstructured_log.append(SASStructuredLoggingParser.parse_log_entry(log_entry))

        # return the unstructured log
        return unstructured_log

    @staticmethod
    def parse_log_entry(log_entry: AnyStr) -> Text:
        """
        Parses a single entry in a log and returns a traditionally formatted logging entry for better
        human-readability. If the entry cannot be decoded from a structured log format, it is returned as-is.

        :param log_entry: Logging entry to parse.
        :return: Traditionally formatted, human-readable logging entry, or the entry as-is if it cannot be decoded from
                 a structured logging format.
        """
        # try to decode the entry from JSON
        try:
            structured_log_entry: Optional[Dict] = json.loads(log_entry)
        except json.JSONDecodeError:
            # if the entry couldn't be decoded from JSON, return as-is
            # in the future, if more logging structures are added, this could be updated to check for more formats
            return log_entry

        # make sure the decoded entry is a dictionary
        if not isinstance(structured_log_entry, dict):
            # this is not a dictionary, as expected
            # return the entry as-is
            return log_entry

        # validate that the structured entry conforms to the spec
        for required_key in SASStructuredLoggingSpec.get_required_keys():
            if required_key not in structured_log_entry:
                # if a required key is missing, the entry can't be parsed as expected
                # return the entry as-is
                return log_entry

        # create an empty string to build the unstructured entry
        unstructured_entry_str: Text = ""

        # the timeStamp is required in the spec and was checked above, add it as the first column
        # this column width is variable and the content is left-justified
        time_stamp = structured_log_entry.get(SASStructuredLoggingSpec.TIME_STAMP)

        # determine the width of the column
        if len(time_stamp) < 25:
            col_width = 26
        else:
            col_width = 34

        # add the column with the determined width
        unstructured_entry_str += f"{time_stamp:<{col_width}}"

        # the level is required in the spec and was checked above, add it as the second column
        # this column is 6 chars wide and is left-justified
        unstructured_entry_str += f"{structured_log_entry.get(SASStructuredLoggingSpec.LEVEL).upper():<6}"

        # the source is required in the spec and was checked above, get the value
        source = structured_log_entry.get(SASStructuredLoggingSpec.SOURCE)

        # make sure the source isn't too long
        if len(source) > 20:
            source = f"...{source[-17:]}"

        # add source as the third column
        # this column is variable width with an effective max of 32 chars and is right-justified
        # a visual break is added after the source
        unstructured_entry_str += f"[{source:>20}] --- "

        # get any properties
        properties: Optional[Dict] = structured_log_entry.get(SASStructuredLoggingSpec.PROPERTIES)

        # check for some commonly used properties to display, if properties are defined
        if properties:
            # check for the origin of the process being logged
            # for Java apps, this will be the thread property; for Go apps, this will be the caller property
            # check if a thread is defined
            thread: Text = properties.get(SASStructuredLoggingSpec.PROPERTY_THREAD)

            # if a thread is defined, process it
            if thread:
                # make sure the thread name isn't too long
                if len(thread) > 15:
                    thread = f"...{thread[-12:]}"

                # add the thread with a column width of 15 chars and right-justification
                unstructured_entry_str += f"[{thread:>15}]"

                # check for a logger property
                logger: Text = properties.get(SASStructuredLoggingSpec.PROPERTY_LOGGER)

                # process the logger value if it exists and the provided line isn't from a Go app where logger
                # information isn't as useful as the caller value
                if logger:
                    # if a logger is defined, truncate the value if longer than 30 chars to keep columns aligned
                    if len(logger) > 30:
                        logger = f"...{logger[-27:]}"

                    # add the logger as the fourth or fifth column
                    # the column is 31 chars wide (including trailing whitespace) and is right-justified
                    unstructured_entry_str += f" {logger:>30}"
            else:
                # check for caller property for GO apps
                caller: Text = properties.get(SASStructuredLoggingSpec.PROPERTY_CALLER)

                # if a caller is defined, process it
                if caller:
                    # make sure the caller value isn't too long
                    if len(caller) > 30:
                        caller = f"...{caller[-27:]}"

                    # add the caller with a column width of 30 chars and right-justification
                    unstructured_entry_str += f"[{caller:>30}]"

        # the message is required in the spec and was checked above, add it as the final column
        # the column length is undefined and it is left-justified
        unstructured_entry_str += f" : {structured_log_entry.get(SASStructuredLoggingSpec.MESSAGE)}"

        # return the unstructured entry
        return unstructured_entry_str
