####################################################################
# ### structured_logging.spec.py                                 ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from typing import List, Text


class SASStructuredLoggingSpec(object):
    """
    Class providing static references to key values defined by the SAS spec for structured logging.
    """
    ATTRIBUTES: Text = "attributes"  # optional
    LEVEL: Text = "level"  # required
    MESSAGE: Text = "message"  # required
    MESSAGE_KEY: Text = "messageKey"  # optional
    MESSAGE_PARAMETERS: Text = "messageParameters"  # optional
    PROPERTIES: Text = "properties"  # optional
    PROPERTY_CALLER: Text = "caller"  # optional
    PROPERTY_LOGGER: Text = "logger"  # optional
    PROPERTY_THREAD: Text = "thread"  # optional
    SOURCE: Text = "source"  # required
    TIME_STAMP: Text = "timeStamp"  # required
    VERSION: Text = "version"  # required

    @staticmethod
    def get_required_keys() -> List[Text]:
        """
        Returns a list of all required keys in the SAS structured logging spec.

        :return: The list of all required keys in the SAS structured logging spec.
        """
        return [
            SASStructuredLoggingSpec.LEVEL,
            SASStructuredLoggingSpec.MESSAGE,
            SASStructuredLoggingSpec.SOURCE,
            SASStructuredLoggingSpec.TIME_STAMP,
            SASStructuredLoggingSpec.VERSION
        ]
