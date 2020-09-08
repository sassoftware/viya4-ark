####################################################################
# ### structured_logging.test_spec.py                            ###
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

from viya_ark_library.structured_logging.spec import SASStructuredLoggingSpec


def test_static_var_attributes() -> None:
    """
    Tests the value of the static attributes variable.
    """
    assert SASStructuredLoggingSpec.ATTRIBUTES == "attributes"


def test_static_var_level() -> None:
    """
    Tests the value of the static level variable.
    """
    assert SASStructuredLoggingSpec.LEVEL == "level"


def test_static_var_message() -> None:
    """
    Tests the value of the static message variable.
    """
    assert SASStructuredLoggingSpec.MESSAGE == "message"


def test_static_var_message_key() -> None:
    """
    Tests the value of the static message key variable.
    """
    assert SASStructuredLoggingSpec.MESSAGE_KEY == "messageKey"


def test_static_var_message_parameters() -> None:
    """
    Tests the value of the static message parameters variable.
    """
    assert SASStructuredLoggingSpec.MESSAGE_PARAMETERS == "messageParameters"


def test_static_var_properties() -> None:
    """
    Tests the value of the static properties variable.
    """
    assert SASStructuredLoggingSpec.PROPERTIES == "properties"


def test_static_var_property_caller() -> None:
    """
    Tests the value of the static caller property key variable.
    """
    assert SASStructuredLoggingSpec.PROPERTY_CALLER == "caller"


def test_static_var_property_logger() -> None:
    """
    Tests the value of the static logger property variable.
    """
    assert SASStructuredLoggingSpec.PROPERTY_LOGGER == "logger"


def test_static_var_property_thread() -> None:
    """
    Tests the value of the static thread property variable.
    """
    assert SASStructuredLoggingSpec.PROPERTY_THREAD == "thread"


def test_static_var_source() -> None:
    """
    Tests the value of the static source variable.
    """
    assert SASStructuredLoggingSpec.SOURCE == "source"


def test_static_var_time_stamp() -> None:
    """
    Tests the value of the static timestamp variable.
    """
    assert SASStructuredLoggingSpec.TIME_STAMP == "timeStamp"


def test_static_var_version() -> None:
    """
    Tests the value of the static version variable.
    """
    assert SASStructuredLoggingSpec.VERSION == "version"


def test_get_required_keys() -> None:
    """
    Tests that all required keys are represented in the returned list.
    """
    required_keys: List[Text] = SASStructuredLoggingSpec.get_required_keys()

    assert isinstance(required_keys, list)
    assert len(required_keys) == 5
    assert SASStructuredLoggingSpec.LEVEL in required_keys
    assert SASStructuredLoggingSpec.MESSAGE in required_keys
    assert SASStructuredLoggingSpec.SOURCE in required_keys
    assert SASStructuredLoggingSpec.TIME_STAMP in required_keys
    assert SASStructuredLoggingSpec.VERSION in required_keys
