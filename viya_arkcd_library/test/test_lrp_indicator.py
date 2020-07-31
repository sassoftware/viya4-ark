####################################################################
# ### test_lrp_indicator.py                                     ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import time

from viya_arkcd_library.lrp_indicator import LRPIndicator


def test_init_default() -> None:
    """
    Tests that a new instance is created with the correct default values.
    """
    this: LRPIndicator = LRPIndicator("Test")

    assert this._indicator_char == "."
    assert this._indicator_delay == 0.9
    assert this._indicator_count == 0
    assert this._indicator_total == 46
    assert this._line_length == 50
    assert this._process_running is False
    assert this._screen_lock is None
    assert this._thread is None
    assert this._enter_message == "Test"
    assert this.exit_message == "DONE"


def test_init_custom() -> None:
    """
    Tests that a new instance is created with the correct custom values.
    """
    this: LRPIndicator = LRPIndicator(enter_message="Test",
                                      character="*",
                                      delay=0.5,
                                      line_length=80)

    assert this._indicator_char == "*"
    assert this._indicator_delay == 0.5
    assert this._indicator_count == 0
    assert this._indicator_total == 76
    assert this._line_length == 80
    assert this._process_running is False
    assert this._screen_lock is None
    assert this._thread is None
    assert this._enter_message == "Test"
    assert this.exit_message == "DONE"


def test_default(capfd) -> None:
    """
    Test the default execution of the LRPIndicator.

    :param capfd: pytest fixture with file descriptor for captured stdout, stderr.
    """
    with LRPIndicator("Test"):
        time.sleep(1)

    stdout, stderr = capfd.readouterr()

    assert "Test..............................................DONE" in stdout


def test_custom(capfd) -> None:
    """
    Test the execution of the LRPIndicator with a custom indicator character, line_length, and exit_message. The delay
    cannot easily be tested because it would require dynamically reading stdout. The delay should be tested by
    integration testing.

    :param capfd: pytest fixture with file descriptor for captured stdout, stderr.
    """
    with LRPIndicator("Test", character="*", line_length=10) as indicator:
        time.sleep(1)
        indicator.exit_message = "FINISHED"

    stdout, stderr = capfd.readouterr()

    assert "Test******FINISHED" in stdout
