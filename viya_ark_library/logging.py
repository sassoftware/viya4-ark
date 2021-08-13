####################################################################
# ### logging.py                                                 ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

from typing import Text
import logging
import datetime

_LOGGER_TIMESTAMP_TMPL_ = "%Y-%m-%dT%H_%M_%S"


class ViyaARKLogger(object):
    """
    The ViyaARKLogger class represents a custom Logger, which can be instantiated my multiple tools.

    Example Usage:
        sas_logger = ViyaARKLogger(report_log_path)
        my_logger  = sas_logger.get_logger()
        my_logger.info("This is an informational message")
    """

    def __init__(self, log_file: Text, logging_level: int = logging.INFO, logger_name: Text = "sas_logger"):
        """
        Constructor for the  SAS custom Logger class.

        :param logging_level: One of the predefined levels - DEBUG, INFO, WARN, ERROR, CRITICAL
        :param log_file: The log file name with full path. Path must be valid
        """
        # Create a custom logger with unique name.
        logger_timestamp = datetime.datetime.now().strftime(_LOGGER_TIMESTAMP_TMPL_)
        self.name = logger_name
        self.logger_name = str(self.name) + logger_timestamp
        self.logger = logging.getLogger(self.logger_name)
        self.log_file = log_file
        self.logging_level = logging_level
        self.logger.setLevel(self.logging_level)
        # Create Handlers
        self.f_handler = logging.FileHandler(self.log_file)
        self.f_handler.setLevel(self.logging_level)

        # Create formatters and add it to handlers
        self.f_format = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        self.f_handler.setFormatter(self.f_format)

        # Add handlers to the logger
        self.logger.addHandler(self.f_handler)

    def get_logger(self):
        """
        Return the custom Logger.
        """
        return self.logger

    def get_logger_name(self):
        """
        Return the custom logger name.
        """
        return self.logger_name

    def get_log_file(self):
        """
        Return the log file name.
        """
        return self.log_file

    def get_log_level(self):
        """
        Return the logging level.
        """
        return self.logging_level
