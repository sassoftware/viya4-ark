####################################################################
# ### test_metrics_utils.py                                      ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import copy
import pytest

from typing import Dict

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as ReportKeys
from deployment_report.model.utils import metrics_util

from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest


####################################################################
# Unit Tests                                                     ###
####################################################################
@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_get_pod_metrics(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that pod metrics are correctly defined per pod when metrics are available.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # get the list of all pods
    pods: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD]

    # add the metrics
    metrics_util.get_pod_metrics(kubectl=KubectlTest(), pods=pods)

    # verify that the metrics were added
    for pod in pods[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT in pod[ReportKeys.ResourceDetails.EXT_DICT]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_get_pod_metrics_unavailable(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that no errors are raised when pod metrics are not available.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # get the list of all pods
    pods: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD]

    # try to add the metrics
    metrics_util.get_pod_metrics(kubectl=KubectlTest(include_metrics=False), pods=pods)

    # make sure the metrics dictionary was not added
    for pod in pods[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT not in pod[ReportKeys.ResourceDetails.EXT_DICT]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_get_node_metrics(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that node metrics are correctly defined per node when metrics are available.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # get the list of all nodes
    nodes: Dict = gathered_resources_copy[KubernetesResource.Kinds.NODE]

    # add the metrics
    metrics_util.get_node_metrics(kubectl=KubectlTest(), nodes=nodes)

    # make sure the metrics were added
    for node in nodes[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT in node[ReportKeys.ResourceDetails.EXT_DICT]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_get_node_metrics_unavailable(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that no errors are raised when pod metrics are not available.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # get the list of all nodes
    nodes: Dict = gathered_resources_copy[KubernetesResource.Kinds.NODE]

    # try to add the metrics
    metrics_util.get_node_metrics(kubectl=KubectlTest(include_metrics=False), nodes=nodes)

    # make sure the metrics dictionary was not added
    for node in nodes[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT not in node[ReportKeys.ResourceDetails.EXT_DICT]
