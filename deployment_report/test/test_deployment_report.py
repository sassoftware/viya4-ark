####################################################################
# ### test_deployment_report.py                                  ###
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
import pytest

from deployment_report.deployment_report import ViyaDeploymentReportCommand, usage

####################################################################
# There is not unit test defined for:
#    ViyaDeploymentReportCommand.run()
# This method requires a Kubernetes environment for full
# functionality.
####################################################################


def test_viya_deployment_report_command_command_name():
    # create command instance
    cmd = ViyaDeploymentReportCommand()

    # check for expected output
    assert cmd.command_name() == "deployment-report"


def test_viya_deployment_report_command_command_desc():
    # create command instance
    cmd = ViyaDeploymentReportCommand()

    # check for expected output
    assert cmd.command_desc() == "Generate a deployment report of SAS components for a target Kubernetes environment."


####################################################################
# There is not unit test defined for:
#    main()
# This method requires a Kubernetes environment for full
# functionality.
####################################################################


def test_usage(capfd):
    # test that a SystemExit is raised
    with pytest.raises(SystemExit) as sys_exit:
        usage(0)

    # make sure the exit value is correct
    assert sys_exit.value.code == 0

    # define expected output
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_data_file = os.path.join(current_dir, f"data{os.sep}expected_command_output.txt")

    with open(test_data_file) as f:
        expected = f.read()

    # get the captured output
    out, err = capfd.readouterr()

    # assert that the captured output matches the expected
    assert out == expected

    # make sure that a non-zero exit code is correct
    with pytest.raises(SystemExit) as sys_exit:
        usage(5)
    assert sys_exit.value.code == 5
