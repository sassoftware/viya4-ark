####################################################################
# ### test_top_reports.py                                        ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

import os
import pytest

from top_reports.top_reports import ViyaTopReportsCommand, main

####################################################################
# There is no unit test defined for:                             ###
#    ViyaTopReportsCommand.run()                                 ###
# This method requires a Kubernetes environment for full         ###
# functionality.                                                 ###
####################################################################


def test_viya_top_reports_command_command_name():
    # create command instance
    cmd = ViyaTopReportsCommand()

    # check for expected output
    assert cmd.command_name() == "top-reports"


def test_viya_top_reports_command_command_desc():
    # create command instance
    cmd = ViyaTopReportsCommand()

    # check for expected output
    assert cmd.command_desc() == "Generate top reports for a target Kubernetes environment."


####################################################################
# There are no complete units test defined for:                  ###
#    main()                                                      ###
# This method requires a Kubernetes environment for full         ###
# functionality.                                                 ###
####################################################################


def test_usage(capfd) -> None:
    """
    Tests that the usage message is printed as expected.
    :param capfd: pytest fixture for file descriptor pointing to captured stdout and stderr.
    """
    _argv: list = ["-h"]

    # run main
    with pytest.raises(SystemExit):
        main(_argv)

    # define expected output
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_data_file = os.path.join(current_dir, f"data{os.sep}expected_usage_output.txt")

    with open(test_data_file) as f:
        expected = f.read()

    # get output
    out, err = capfd.readouterr()

    assert out == expected
