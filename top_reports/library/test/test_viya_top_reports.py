####################################################################
# ### test_viya_top_reports.py                                   ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import json
import os
import pytest

from typing import Dict, List, Text

from top_reports.library.viya_top_reports import ViyaTopReports

from viya_ark_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest


####################################################################
# Unit Test Fixtures                                             ###
####################################################################
@pytest.fixture(scope="module")
def report() -> ViyaTopReports:
    """
    This fixture method runs the report to populate data. With the "module" scope, this will only run once for this
    test file, which saves time because a generic report can be used by multiple tests.

    :return: The completed ViyaTopReports object.
    """
    report: ViyaTopReports = ViyaTopReports()
    report.gather_reports(kubectl=KubectlTest())
    return report


####################################################################
# Unit Tests                                                     ###
####################################################################
def test_gather_reports_basic_user_invalid_namespace_from_command_line() -> None:
    """
    In the event that a user without the ability to see non-namespaced resources passes an invalid namespace on the
    command line, kubectl won't be able to verify that value as valid or invalid and will pass it along to the report.
    If this occurs, the gather_reports() method should throw an error when listing pods is forbidden.
    """
    with pytest.raises(KubectlRequestForbiddenError) as exec_info:
        report: ViyaTopReports = ViyaTopReports()
        report.gather_reports(kubectl=KubectlTest(include_non_namespaced_resources=False,
                                                  namespace="Foo"))

    assert ("Listing pods is forbidden in namespace [Foo]. Make sure KUBECONFIG is correctly set and that the correct "
            "namespace is being targeted. A namespace can be given on the command line using the \"--namespace=\" "
            "option.") in str(exec_info.value)


def test_gather_reports_basic_user_valid_namespace_from_command_line() -> None:
    """
    In the event that a user without the ability to see non-namespaced resources passes a valid namespace on the
    command line, kubectl won't be able to verify that value as valid or invalid and will pass it along to the report.
    If this occurs, the gather_reports() method should not throw an error when listing pods as the request should be
    allowed with a valid namespace.
    """
    try:
        report: ViyaTopReports = ViyaTopReports()
        report.gather_reports(kubectl=KubectlTest(include_non_namespaced_resources=False,
                                                  namespace="test"))
    except KubectlRequestForbiddenError as e:
        pytest.fail(f"An unexpected error was raised: {e}")


def test_write_report(report: ViyaTopReports) -> None:
    """
    This test verifies that a completed reports are correctly written to disk as text files.

    :param report: The populated ViyaTopReports returned by the report() fixture.
    """
    # write the data files
    data_top_nodes_file, data_top_pods_file = report.write_report()

    # check for expected files
    assert os.path.exists(data_top_nodes_file)
    assert os.path.isfile(data_top_nodes_file)
    assert os.path.exists(data_top_pods_file)
    assert os.path.isfile(data_top_pods_file)

    # clean up files
    os.remove(data_top_nodes_file)
    os.remove(data_top_pods_file)


def test_write_report_unpopulated() -> None:
    """
    This test verifies that a None value is returned for each file when the report is unpopulated.
    """
    # create unpopulated report instance
    report = ViyaTopReports()

    # write the data files
    data_top_nodes_file, data_top_pods_file = report.write_report()

    # make sure None is returned
    assert data_top_nodes_file is None
    assert data_top_pods_file is None
