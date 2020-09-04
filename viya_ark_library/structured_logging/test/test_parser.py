####################################################################
# ### structured_logging.test_parser.py                          ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import os

from typing import AnyStr, List, Text

from viya_ark_library.structured_logging.parser import SASStructuredLoggingParser


def test_parse_log() -> None:
    """
    Tests that a log containing structured entries is correctly parsed. The test log contains entries to fully test the
    various code paths through SASStructuredLoggingParser.parse_log_entry().
    """
    # get the current directory of this script to create absolute path
    current_dir: Text = os.path.dirname(os.path.abspath(__file__))
    # join the path to this file with the remaining path to the requested test data
    test_data_file: Text = os.path.join(current_dir, "data", "test_log.txt")
    # open the test file and return the contents as a Python-native dictionary
    with open(test_data_file, "r") as test_data_file_pointer:
        test_log: List[AnyStr] = test_data_file_pointer.read().splitlines()

    actual_log: List[Text] = SASStructuredLoggingParser.parse_log(test_log)

    # get expected log
    test_data_file = os.path.join(current_dir, "data", "expected_log.txt")
    with open(test_data_file, "r") as test_data_file_pointer:
        expected_log: List[AnyStr] = test_data_file_pointer.read().splitlines()

    assert actual_log == expected_log
