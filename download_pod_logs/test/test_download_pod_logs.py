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

from download_pod_logs.download_pod_logs import DownloadPodLogsCommand, main


####################################################################
# There is no unit test defined for:                             ###
#    DownloadPodLogsCommand.run()                                ###
# This method requires a Kubernetes environment for full         ###
# functionality.                                                 ###
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
