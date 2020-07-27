####################################################################
# ### test_download_pod_logs.py                                  ###
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

from download_pod_logs.download_pod_logs import DownloadPodLogsCommand, usage

####################################################################
# There is no unit test defined for:
#    DownloadPodLogsCommand.run()
# This method requires a Kubernetes environment for full
# functionality.
####################################################################


def test_download_pod_logs_command_command_name():
    # create command instance
    cmd = DownloadPodLogsCommand()

    # check for expected output
    assert cmd.command_name() == "download-pod-logs"


def test_download_pod_logs_command_command_desc():
    # create command instance
    cmd = DownloadPodLogsCommand()

    # check for expected output
    assert cmd.command_desc() == "Download log files for all or a select list of pods."


####################################################################
# There is no unit test defined for:
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
    test_data_file = os.path.join(current_dir, "data", "expected_usage_output.txt")

    with open(test_data_file) as f:
        expected = f.read()

    # get the captured output
    stdout, stderr = capfd.readouterr()

    # assert that the captured output matches the expected
    assert stdout == expected

    # make sure that a non-zero exit code is correct
    with pytest.raises(SystemExit) as sys_exit:
        usage(5)

    # make sure the exit value is correct
    assert sys_exit.value.code == 5
