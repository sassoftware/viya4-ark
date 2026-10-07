####################################################################
# ### test_deployment_report.py                                  ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020-2026, SAS Institute Inc., Cary, NC, USA.    ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

from deployment_report.deployment_report import ViyaDeploymentReportCommand

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
