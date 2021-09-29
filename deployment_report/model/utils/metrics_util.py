####################################################################
# ### metrics_util.py                                            ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from subprocess import CalledProcessError
from typing import Dict

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as ReportKeys

from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface


def get_pod_metrics(kubectl: KubectlInterface, pods: Dict) -> None:
    """
    Retrieves Pod metrics from the Kubernetes API and defines the ext.metrics dictionary for all gathered Pods.

    :param kubectl: The KubectlInterface object for issuing requests to the Kubernetes cluster for Pod metrics.
    :param pods: The Pod resources gathered in the Kubernetes cluster.
    """
    # get Pod metrics if Pods are defined
    if pods[ReportKeys.ResourceTypeDetails.COUNT] > 0:
        try:
            # get Pod metrics
            pod_metrics: Dict = kubectl.top_pods().as_dict()

            # iterate over the returned metrics and add them to the Pod extensions
            for pod_name, metrics in pod_metrics.items():
                try:
                    pod_ext: Dict = pods[ITEMS_KEY][pod_name][ReportKeys.ResourceDetails.EXT_DICT]
                    pod_ext[ReportKeys.ResourceDetails.Ext.METRICS_DICT]: Dict = metrics
                except KeyError:
                    # if the Pod isn't defined, move on without error
                    pass

        except CalledProcessError:
            # if Pod metrics aren't available, move on without error
            pass


def get_node_metrics(kubectl: KubectlInterface, nodes: Dict) -> None:
    """
    Retrieves Node metrics from the Kubernetes API and defines the metrics extension for all gathered Nodes.

    :param kubectl: The KubectlInterface object for issuing requests to the Kubernetes cluster for Node metrics.
    :param nodes: The Node resources gathered in the Kubernetes cluster.
    """
    # get Node metrics if Nodes are defined
    if nodes[ReportKeys.ResourceTypeDetails.COUNT] > 0:
        try:
            # get Node metrics
            node_metrics: Dict = kubectl.top_nodes().as_dict()

            # iterate over the returned metrics and add them to the Node extensions
            for node_name, metrics in node_metrics.items():
                try:
                    node_ext: Dict = nodes[ITEMS_KEY][node_name][ReportKeys.ResourceDetails.EXT_DICT]
                    node_ext[ReportKeys.ResourceDetails.Ext.METRICS_DICT]: Dict = metrics
                except KeyError:
                    # if the Node isn't defined, move on without error
                    pass

        except CalledProcessError:
            # if Node metrics aren't available, move on without error
            pass
