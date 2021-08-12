####################################################################
# ### test_model.py                                              ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import filecmp
import os
import multiprocessing
import pytest
import shutil

from typing import Dict, Text

from download_pod_logs.model import PodLogDownloader, NoPodsError, NoMatchingPodsError, _ContainerStatus, \
    _LogDownloadProcess

from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface
from viya_ark_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest


####################################################################
# PodLogDownloader Tests                                         ###
# Notes:                                                         ###
#   No explicit tests for _write_log() because it is tested in   ###
#   the test_download_logs()                                     ###
####################################################################
def test_init_default() -> None:
    """
    This test verifies that the PodLogDownloader is constructed correctly with all default values.
    """
    # create test object
    expected_kubectl: KubectlInterface = KubectlTest()
    actual: PodLogDownloader = PodLogDownloader(kubectl=expected_kubectl)

    # check for expected default values
    assert actual._kubectl == expected_kubectl
    assert actual._output_dir == PodLogDownloader.DEFAULT_OUTPUT_DIR
    assert actual._processes == PodLogDownloader.DEFAULT_PROCESSES
    assert actual._wait == PodLogDownloader.DEFAULT_WAIT


def test_init_custom() -> None:
    """
    This test verifies that the PodLogDownloader is constructed correctly with all custom values.
    """
    # define expected values
    expected_output_dir: Text = "./custom"
    expected_processes: int = 7
    expected_wait: int = 45

    # create test object
    expected_kubectl: KubectlInterface = KubectlTest()
    actual: PodLogDownloader = PodLogDownloader(kubectl=expected_kubectl,
                                                output_dir=expected_output_dir,
                                                processes=expected_processes,
                                                wait=expected_wait)

    # check for expected custom values
    assert actual._kubectl == expected_kubectl
    assert actual._output_dir == expected_output_dir
    assert actual._processes == expected_processes
    assert actual._wait == expected_wait


def test_init_invalid_concurrent_processes() -> None:
    """
    This test verifies that an AttributeError is raised when an invalid concurrent_processes value is given.
    """
    with pytest.raises(AttributeError) as except_info:
        PodLogDownloader(kubectl=KubectlTest(),
                         processes=0)

    assert "The processes value must be greater than 0" in str(except_info.value)


def test_init_invalid_process_wait_time() -> None:
    """
    This test verifies that an AttributeError is raised when an invalid process_wait_time value is given.
    """
    with pytest.raises(AttributeError) as except_info:
        PodLogDownloader(kubectl=KubectlTest(),
                         wait=-5)

    assert "The wait value must be 0 or greater" in str(except_info.value)


def test_download_logs() -> None:
    """
    This test verifies that available pod log files are correctly downloaded and formatted.
    """
    # create the test object
    this: PodLogDownloader = PodLogDownloader(kubectl=KubectlTest(), output_dir="./test_download_logs")

    # run the method being tested
    logs_dir, timeout_pods, error_pods = this.download_logs()

    # verify the expected number of logs were written to disk
    assert len([name for name in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, name))]) == 6

    # define the expected and actual log files
    expected_log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "expected-sas-annotations.txt")
    actual_log_file = os.path.join(logs_dir, f"{KubectlTest.Values.COMPONENT_SAS_ANNOTATIONS_POD_NAME}.log")

    # verify that a downloaded log contains the expected content
    assert filecmp.cmp(expected_log_file, actual_log_file)

    # clean up logs created above
    shutil.rmtree(os.path.abspath(os.path.join(logs_dir, "..")))


def test_download_logs_with_valid_selected_component() -> None:
    """
    This test verifies that a log file is correctly downloaded and formatted when a matching component is selected.
    """
    # create the test object
    this: PodLogDownloader = PodLogDownloader(kubectl=KubectlTest(), output_dir="./test_download_logs_selected")

    # run the method being tested
    logs_dir, timeout_pods, error_pods = this.download_logs(selected_components=["sas-annotations"])

    # verify the expected number of logs were written to disk
    assert len([name for name in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, name))]) == 1

    # define the expected and actual log files
    expected_log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "expected-sas-annotations.txt")
    actual_log_file = os.path.join(logs_dir, f"{KubectlTest.Values.COMPONENT_SAS_ANNOTATIONS_POD_NAME}.log")

    # verify that a downloaded log contains the expected content
    assert filecmp.cmp(expected_log_file, actual_log_file)

    # clean up logs created above
    shutil.rmtree(os.path.abspath(os.path.join(logs_dir, "..")))


def test_download_logs_with_invalid_selected_component() -> None:
    """
    This test verifies that a NoMatchingPodsError is raised when the selected_components list doesn't contain an
    available pod.
    """
    # create the test object
    this: PodLogDownloader = PodLogDownloader(kubectl=KubectlTest())

    # cause the error
    with pytest.raises(NoMatchingPodsError) as except_info:
        this.download_logs(selected_components=["sas-foo"])

    # make sure the correct error was raised
    assert isinstance(except_info.value, NoMatchingPodsError)
    assert "No pods in namespace [test] matched the provided components filter: [sas-foo]" in str(except_info.value)


def test_download_logs_with_list_pods_forbidden() -> None:
    """
    This test verifies that a KubectlRequestForbiddenError is raised when pods cannot be listed.
    """
    # create the test object
    this: PodLogDownloader = PodLogDownloader(kubectl=KubectlTest(namespace="foo"))

    # cause the error
    with pytest.raises(KubectlRequestForbiddenError) as except_info:
        this.download_logs()

    # make sure the correct error was raised
    assert isinstance(except_info.value, KubectlRequestForbiddenError)
    assert ("Listing pods is forbidden in namespace [foo]. Make sure KUBECONFIG is correctly set and that the "
            "correct namespace is being targeted. A namespace can be given on the command line using the "
            "\"--namespace=\" option.") in str(except_info.value)


def test_download_logs_with_empty_deployment() -> None:
    """
    This test verifies that a NoPodsError is raised when no pods are available in the deployment.
    """
    # create the test object
    this: PodLogDownloader = PodLogDownloader(kubectl=KubectlTest(simulate_empty_deployment=True))

    # cause the error
    with pytest.raises(NoPodsError) as except_info:
        this.download_logs()

    # make sure the correct error was raised
    assert isinstance(except_info.value, NoPodsError)
    assert "No pods were found in namespace [test]." in str(except_info.value)


####################################################################
# NoMatchingPodsError Tests                                      ###
####################################################################
def test_no_matching_pods_error() -> None:
    """
    This test verifies that the message is correctly set in a NoMatchingPodsError.
    """
    # raise the NoMatchingPodsError and get the ExceptionInfo
    with pytest.raises(NoMatchingPodsError) as except_info:
        raise NoMatchingPodsError("test message")

    # verify that the raised error matches the expected error
    assert "test message" in str(except_info.value)
    assert isinstance(except_info.value, NoMatchingPodsError)
    assert isinstance(except_info.value, RuntimeError)


####################################################################
# NoPodsError Tests                                              ###
####################################################################
def test_no_pods_error() -> None:
    """
    This test verifies that the message is correctly set in a NoPodsError.
    """
    # raise the NoPodsError and get the ExceptionInfo
    with pytest.raises(NoPodsError) as except_info:
        raise NoPodsError("test message")

    # verify that the raised error matches the expected error
    assert "test message" in str(except_info.value)
    assert isinstance(except_info.value, NoPodsError)
    assert isinstance(except_info.value, RuntimeError)


####################################################################
# _ContainerStatus Tests                                         ###
####################################################################
# test dictionary representing a "running" container status
expected_running_dict = \
    {
        "containerID": "docker://59c6c4fc36529bf4ffd434eb30e0b8e726cd6bbec9fdb53262ba5b75f6d0235c",
        "image": "test.sas.com/test/sas-annotations:2.2.25-20200506.1588775452057",
        "imageID": "docker-pullable://test.sas.com/test/sas-annotations@sha256:755f7bb150854c5e4b490d732a1cfae73d7a",
        "lastState": {
            "terminated": {
                "containerID": "docker://481bb52d37dcf41b5259d825c90ad97088b2ecbdd052b873c0ba2ab70ea2971c",
                "exitCode": 1,
                "finishedAt": "2020-06-02T18:01:35Z",
                "reason": "Error",
                "startedAt": "2020-06-02T16:54:36Z"
            }
        },
        "name": "sas-annotations",
        "ready": False,
        "restartCount": 1,
        "started": True,
        "state": {
            "running": {
                "startedAt": "2020-06-02T18:01:39Z"
            }
        }
    }

# test dictionary representing a "terminated" container status
expected_terminated_dict = \
    {
        "containerID": "docker://59c6c4fc36529bf4ffd434eb30e0b8e726cd6bbec9fdb53262ba5b75f6d0235c",
        "image": "test.sas.com/test/sas-annotations:2.2.25-20200506.1588775452057",
        "imageID": "docker-pullable://test.sas.com/test/sas-annotations@sha256:755f7bb150854c5e4b490d732a1cfae73d7a",
        "lastState": {},
        "name": "sas-annotations",
        "ready": False,
        "restartCount": 0,
        "started": True,
        "state": {
            "terminated": {
                "containerID": "docker://481bb52d37dcf41b5259d825c90ad97088b2ecbdd052b873c0ba2ab70ea2971c",
                "exitCode": 1,
                "finishedAt": "2020-06-02T18:01:35Z",
                "reason": "Error",
                "startedAt": "2020-06-02T16:54:36Z"
            }
        }
    }

# test dictionary representing a "waiting" container status
expected_waiting_dict = \
    {
        "containerID": "docker://59c6c4fc36529bf4ffd434eb30e0b8e726cd6bbec9fdb53262ba5b75f6d0235c",
        "image": "test.sas.com/test/sas-annotations:2.2.25-20200506.1588775452057",
        "imageID": "docker-pullable://test.sas.com/test/sas-annotations@sha256:755f7bb150854c5e4b490d732a1cfae73d7a",
        "lastState": {},
        "name": "sas-annotations",
        "ready": False,
        "restartCount": 0,
        "started": True,
        "state": {
            "waiting": {
                "reason": "WaitingToStart"
            }
        }
    }


def test_get_image() -> None:
    """
    This test verifies that the image value is correctly returned for the given container status.
    """
    # create the test object
    this: _ContainerStatus = _ContainerStatus(expected_running_dict)

    # verify actual value matches the expected value
    assert this.get_image() == expected_running_dict["image"]


def test_get_image_missing() -> None:
    """
    This test verifies that an empty string is returned if the image value is not defined.
    """
    # create the test object
    this: _ContainerStatus = _ContainerStatus(dict())

    # verify actual value matches the expected value
    assert this.get_image() == ""


def test_get_name() -> None:
    """
    This test verifies that the name value is correctly returned for the given container status.
    """
    # create the test object
    this: _ContainerStatus = _ContainerStatus(expected_running_dict)

    # verify actual value matches the expected value
    assert this.get_name() == expected_running_dict["name"]


def test_get_name_missing() -> None:
    """
    This test verifies that an empty string is returned if the name value is not defined.
    """
    # create the test object
    this = _ContainerStatus(dict())

    # verify actual value matches the expected value
    assert this.get_name() == ""


def test_is_ready() -> None:
    """
    This test verifies that the ready value is correctly returned for the given container status.
    """
    # create the test object
    this: _ContainerStatus = _ContainerStatus(expected_running_dict)

    # verify actual value matches the expected value
    assert this.is_ready() == str(expected_running_dict["ready"])


def test_is_ready_missing() -> None:
    """
    This test verifies that an empty string is returned if the ready value is not defined.
    """
    # create the test object
    this = _ContainerStatus(dict())

    # verify actual value matches the expected value
    assert this.is_ready() == ""


def test_get_restart_count() -> None:
    """
    This test verifies that the restartCount value is correctly returned for the given container status.
    """
    # create the test object
    this: _ContainerStatus = _ContainerStatus(expected_running_dict)

    # verify actual value matches the expected value
    assert this.get_restart_count() == str(expected_running_dict["restartCount"])


def test_get_restart_count_missing() -> None:
    """
    This test verifies that an empty string is returned if the restartCount value is not defined.
    """
    # create the test object
    this: _ContainerStatus = _ContainerStatus(dict())

    # verify actual value matches the expected value
    assert this.get_restart_count() == ""


def test_is_started() -> None:
    """
    This test verifies that the started value is correctly returned for the given container status.
    """
    # create the test object
    this: _ContainerStatus = _ContainerStatus(expected_running_dict)

    # verify actual value matches the expected value
    assert this.is_started() == str(expected_running_dict["started"])


def test_is_started_missing() -> None:
    """
    This test verifies that an empty string is returned if the started value is not defined.
    """
    # create the test object
    this: _ContainerStatus = _ContainerStatus(dict())

    # verify actual value matches the expected value
    assert this.is_started() == ""


def test_get_state_dict_running() -> None:
    """
    This test verifies that the correct state dictionary is returned when the container is in the "running" state.
    """
    # create the test object and get the actual test values
    this: _ContainerStatus = _ContainerStatus(expected_running_dict)
    actual_state_dict: Dict[Text, Text] = this.get_state_dict()

    # verify actual values match the expected values
    assert isinstance(actual_state_dict, dict)
    assert len(actual_state_dict) == 2
    assert actual_state_dict["container-state"] == "running"
    assert actual_state_dict["container-started-at"] == expected_running_dict["state"]["running"]["startedAt"]


def test_get_state_dict_terminated() -> None:
    """
    This test verifies that the correct state dictionary is returned when the container is in the "terminated" state.
    """
    # create the test object and get the actual test values
    this: _ContainerStatus = _ContainerStatus(expected_terminated_dict)
    actual_state_dict: Dict[Text, Text] = this.get_state_dict()

    # verify actual values match the expected values
    assert isinstance(actual_state_dict, dict)
    assert len(actual_state_dict) == 4
    assert actual_state_dict["container-state"] == "terminated"
    assert actual_state_dict["container-state-reason"] == expected_terminated_dict["state"]["terminated"]["reason"]
    assert actual_state_dict["container-started-at"] == expected_terminated_dict["state"]["terminated"]["startedAt"]
    assert actual_state_dict["container-finished-at"] == expected_terminated_dict["state"]["terminated"]["finishedAt"]


def test_get_state_dict_waiting() -> None:
    """
    This test verifies that the correct state dictionary is returned when the container is in the "waiting" state.
    """
    # create the test object and get the actual test values
    this: _ContainerStatus = _ContainerStatus(expected_waiting_dict)
    actual_state_dict: Dict[Text, Text] = this.get_state_dict()

    # verify actual values match the expected values
    assert isinstance(actual_state_dict, dict)
    assert len(actual_state_dict) == 2
    assert actual_state_dict["container-state"] == "waiting"
    assert actual_state_dict["container-state-reason"] == expected_waiting_dict["state"]["waiting"]["reason"]


def test_get_state_dict_missing() -> None:
    """
    This test verifies that the correct state dictionary is returned when the container state is not defined.
    """
    # create the test object and get the actual test values
    this: _ContainerStatus = _ContainerStatus(dict())
    actual_state_dict: Dict[Text, Text] = this.get_state_dict()

    # verify actual values match the expected values
    assert actual_state_dict is not None
    assert isinstance(actual_state_dict, dict)
    assert len(actual_state_dict) == 0


def test_get_headers_dict() -> None:
    """
    This test verifies that the correct headers dictionary is returned for the given status.
    """
    # create the test object and get the actual test values
    this: _ContainerStatus = _ContainerStatus(expected_running_dict)
    actual_headers_dict: Dict[Text, Text] = this.get_headers_dict()

    # verify actual values match the expected values
    assert isinstance(actual_headers_dict, dict)
    assert len(actual_headers_dict) == 7
    assert actual_headers_dict["container-name"] == expected_running_dict["name"]
    assert actual_headers_dict["container-image"] == expected_running_dict["image"]
    assert actual_headers_dict["container-is-started"] == str(expected_running_dict["started"])
    assert actual_headers_dict["container-is-ready"] == str(expected_running_dict["ready"])
    assert actual_headers_dict["container-restarts"] == str(expected_running_dict["restartCount"])
    assert actual_headers_dict["container-state"] == "running"
    assert actual_headers_dict["container-started-at"] == expected_running_dict["state"]["running"]["startedAt"]


def test_get_headers_dict_missing() -> None:
    """
    This test verifies that the correct headers dictionary is returned when the status dictionary is undefined.
    """
    # create the test object and get the actual test values
    this: _ContainerStatus = _ContainerStatus(dict())
    actual_headers_dict: Dict[Text, Text] = this.get_headers_dict()

    # verify actual values match the expected values
    assert isinstance(actual_headers_dict, dict)
    assert len(actual_headers_dict) == 5
    assert actual_headers_dict["container-name"] == ""
    assert actual_headers_dict["container-image"] == ""
    assert actual_headers_dict["container-is-started"] == ""
    assert actual_headers_dict["container-is-ready"] == ""
    assert actual_headers_dict["container-restarts"] == ""


####################################################################
# _LogDownloadProcess Tests                                      ###
####################################################################
def test_log_download_process() -> None:
    """
    _LogDownloadProcess is a very simple object which just associates the pooled process and name of pod for which the
    process is being run. This is a simple test to make sure values stored in the object are correctly retrieved.
    """
    pool: multiprocessing.Pool = multiprocessing.Pool(processes=1)
    process: multiprocessing.pool.ApplyResult = pool.apply_async(_pool_test_dummy)
    this: _LogDownloadProcess = _LogDownloadProcess(pod_name="test", process=process)

    assert this.get_pod_name() == "test"
    assert this.get_process() == process


def _pool_test_dummy():
    pass
