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
import pytest

from typing import Dict

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as ReportKeys
from deployment_report.model.utils import metrics_util
from deployment_report.model.utils.test import conftest
from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues

from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest


####################################################################
# Unit Tests                                                     ###
####################################################################
# run the unavailable tests first, the dictionary will be added to the fixture by the "available' tests
@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_get_pod_metrics_unavailable(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that no errors are raised when pod metrics are not available.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # get the list of all pods
    pods: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS]

    # try to add the metrics
    metrics_util.get_pod_metrics(kubectl=KubectlTest(include_metrics=False), pods=pods)

    # make sure the metrics dictionary was not added
    for pod in pods[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT not in pod[ReportKeys.ResourceDetails.EXT_DICT]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_get_node_metrics_unavailable(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that no errors are raised when pod metrics are not available.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # get the list of all nodes
    nodes: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_NODES]

    # try to add the metrics
    metrics_util.get_node_metrics(kubectl=KubectlTest(include_metrics=False), nodes=nodes)

    # make sure the metrics dictionary was not added
    for node in nodes[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT not in node[ReportKeys.ResourceDetails.EXT_DICT]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_get_pod_metrics(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that pod metrics are correctly defined per pod when metrics are available.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # get the list of all pods
    pods: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS]

    # add the metrics
    metrics_util.get_pod_metrics(kubectl=KubectlTest(), pods=pods)

    # verify that the metrics were added
    for pod in pods[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT in pod[ReportKeys.ResourceDetails.EXT_DICT]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_get_node_metrics(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that node metrics are correctly defined per node when metrics are available.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # get the list of all nodes
    nodes: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_NODES]

    # add the metrics
    metrics_util.get_node_metrics(kubectl=KubectlTest(), nodes=nodes)

    # make sure the metrics were added
    for node in nodes[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT in node[ReportKeys.ResourceDetails.EXT_DICT]
