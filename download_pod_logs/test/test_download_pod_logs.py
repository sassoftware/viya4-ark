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
from download_pod_logs.model import PodLogDownloader
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest

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


def test_write_log_container_status_none() -> None:
    """
    This test verifies that an error is not raised when the _write_log() method is passed a pod with no
    container_status dictionary.
    """
    pod_definition = """
    {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "annotations": {
                "sas.com/component-name": "sas-annotations",
                "sas.com/component-version": "2.2.25-20200506.1588775452057",
                "sas.com/version": "2.2.25"
            },
            "creationTimestamp": "2020-05-09T00:16:45Z",
            "generateName": "sas-annotations-58db55fd65-",
            "labels": {
                "app": "sas-annotations",
                "app.kubernetes.io/name": "sas-annotations",
                "pod-template-hash": "58db55fd65",
                "sas.com/deployment": "sas-viya"
            },
            "name": "sas-annotations-58db55fd65-l2jrw",
            "namespace": "test",
            "resourceVersion": "11419232",
            "selfLink": "/api/v1/namespaces/test/pods/sas-annotations-58db55fd65-l2jrw",
            "uid": "b0e2b9c6-58f9-4c81-94b9-8ea2be06a7c1"
        },
        "spec": {
            "containers": [],
            "dnsPolicy": "ClusterFirst",
            "enableServiceLinks": true,
            "imagePullSecrets": [],
            "nodeName": "k8s-master-node.test.sas.com",
            "priority": 0,
            "restartPolicy": "Always",
            "schedulerName": "default-scheduler",
            "securityContext": {},
            "serviceAccount": "default",
            "serviceAccountName": "default",
            "terminationGracePeriodSeconds": 30,
            "tolerations": [],
            "volumes": []
        },
        "status": {
            "conditions": [],
            "hostIP": "10.104.215.7",
            "phase": "Running",
            "podIP": "0.0.0.0",
            "podIPs": [
                {
                    "ip": "0.0.0.0"
                }
            ],
            "qosClass": "Burstable",
            "startTime": "2020-05-09T00:16:45Z"
        }
    }
    """

    # create the Kubernetes resource object
    pod: KubernetesResource = KubernetesResource(pod_definition)

    err_info = PodLogDownloader._write_log(kubectl=KubectlTest(), pod=pod, tail=1,
                                           output_dir="./no_container_status_test")
    assert err_info is None


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
