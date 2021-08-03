####################################################################
# ### sas_kubectl_test.py                                        ###
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

from enum import Enum
from subprocess import CalledProcessError
from typing import AnyStr, Dict, List, Text, Union, Optional

from viya_ark_library.k8s.sas_k8s_objects import KubernetesApiResources, KubernetesMetrics, KubernetesResource
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface

_API_RESOURCES_All_INGRESSES_DATA_ = "api_resources_ingress_all.json"
_API_RESOURCES_CONTOUR_ONLY_DATA_ = "api_resources_ingress_contour.json"
_API_RESOURCES_ISTIO_ONLY_DATA_ = "api_resources_ingress_istio.json"
_API_RESOURCES_NGINX_ONLY_DATA_ = "api_resources_ingress_nginx.json"
_API_RESOURCES_NO_INGRESS_DATA_ = "api_resources_ingress_none.json"
_API_RESOURCES_OPENSHIFT_ONLY_DATA_ = "api_resources_ingress_openshift.json"
_API_VERSIONS_DATA_ = "api_versions.json"
_CONFIG_VIEW_DATA_ = "config_view.json"
_TOP_NODES_DATA_ = "top_nodes.json"
_TOP_PODS_DATA_ = "top_pods.json"
_VERSIONS_DATA_ = "versions.json"


class KubectlTest(KubectlInterface):
    """
    Implementation of the KubectlInterface used for unit testing. This implementation does not communicate with a live
    Kubernetes cluster, but instead returns static data stored as JSON in the response_data/ directory parallel to this
    file. The class allows for some behavior to be modified to represent various deployment scenarios such as simulating
    different ingress control configurations by passing an IngressSimulator value to the constructor, and controlling
    whether metrics are included for resources with a boolean flag also passed to the constructor.
    """

    ################################################################
    # ### CLASS: KubectlTest.IngressSimulator
    ################################################################
    class IngressSimulator(Enum):
        """
        Enumerated class representing the various ingress controller simulations that can be specified for the
        KubectlTest implementation.
        """
        # No ingress kinds will be included in the resources returned by api_resources()
        NONE = 0

        # All resource kinds will be returned by api_resources() but only Contour HTTPProxy objects will be found
        ALL_CONTOUR_USED = 1

        # All resource kinds will be returned by api_resources() but only Istio VirtualService objects will be found
        ALL_ISTIO_USED = 2

        # All resource kinds will be returned by api_resources() but only Ingress objects will be found
        ALL_NGINX_USED = 3

        # All resource kinds will be returned by api_resources() but only OpenShift Route objects will be found
        ALL_OPENSHIFT_USED = 4

        # Only the Contour HTTPProxy kind will be included in the resources returned by api_resources()
        ONLY_CONTOUR = 5

        # Only the Istio VirtualService kind will be included in the resources returned by api_resources()
        ONLY_ISTIO = 6

        # Only the Ingress kind will be included in the resources returned by api_resources()
        ONLY_NGINX = 7

        # Only the OpenShift Route kind will be included in the resources returned by api_resources()
        ONLY_OPENSHIFT = 8

    ################################################################
    # ### CLASS: KubectlTest.Values
    ################################################################
    class Values(object):
        """
        Class providing static references to values returned by the KubectlTest implementation.
        """
        NAMESPACE: Text = "test"
        CADENCEINFO: Text = "Fast R/TR 2020 (20201214.1607958443388)"
        DBINFO: Text = "Internal"

        # Component: prometheus
        COMPONENT_PROMETHEUS_DEPLOYMENT_NAME: Text = "pushgateway-test-prometheus-pushgateway"
        COMPONENT_PROMETHEUS_POD_NAME: Text = "pushgateway-test-prometheus-pushgateway-df9d7c96c-4n66t"
        COMPONENT_PROMETHEUS_REPLICA_SET_NAME: Text = "pushgateway-test-prometheus-pushgateway-df9d7c96c"
        COMPONENT_PROMETHEUS_SERVICE_NAME: Text = "pushgateway-test-prometheus-pushgateway"

        COMPONENT_PROMETHEUS_NAME: Text = "pushgateway-test-prometheus-pushgateway"
        COMPONENT_PROMETHEUS_RESOURCES_DICT: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.DEPLOYMENT: [COMPONENT_PROMETHEUS_DEPLOYMENT_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_PROMETHEUS_POD_NAME],
            KubernetesResource.Kinds.REPLICA_SET: [COMPONENT_PROMETHEUS_REPLICA_SET_NAME],
            KubernetesResource.Kinds.SERVICE: [COMPONENT_PROMETHEUS_SERVICE_NAME]
        }
        COMPONENT_PROMETHEUS_RESOURCE_COUNT: int = len(COMPONENT_PROMETHEUS_RESOURCES_DICT)

        # Component: sas-annotations - all
        COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME: Text = "sas-annotations"
        COMPONENT_SAS_ANNOTATIONS_CONTOUR_HTTPPROXY_NAME: Text = "sas-annotations"
        COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME_DEPRECATED_DEFINITION: Text = "sas-annotations-deprecated-definition"
        COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME: Text = "sas-annotations"
        COMPONENT_SAS_ANNOTATIONS_OPENSHIFT_ROUTE_NAME: Text = "sas-annotations"
        COMPONENT_SAS_ANNOTATIONS_POD_NAME: Text = "sas-annotations-58db55fd65-l2jrw"
        COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME: Text = "sas-annotations-58db55fd65"
        COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME: Text = "sas-annotations"
        COMPONENT_SAS_ANNOTATIONS_VIRTUAL_SERVICE_NAME: Text = "sas-annotations"

        COMPONENT_SAS_ANNOTATIONS_NAME: Text = "sas-annotations"

        # Component: sas-annotations - No Ingress
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NO_INGRESS: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.DEPLOYMENT: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResource.Kinds.REPLICA_SET: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResource.Kinds.SERVICE: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NO_INGRESS: int = \
            len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NO_INGRESS)

        # Component: sas-annotations - Contour
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_CONTOUR: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.DEPLOYMENT: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResource.Kinds.REPLICA_SET: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResource.Kinds.SERVICE: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME],
            KubernetesResource.Kinds.CONTOUR_HTTPPROXY: [COMPONENT_SAS_ANNOTATIONS_CONTOUR_HTTPPROXY_NAME],
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_CONTOUR: int = len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_CONTOUR)

        # Component: sas-annotations - Istio
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_ISTIO: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.DEPLOYMENT: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResource.Kinds.REPLICA_SET: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResource.Kinds.SERVICE: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME],
            KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE: [COMPONENT_SAS_ANNOTATIONS_VIRTUAL_SERVICE_NAME],
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_ISTIO: int = len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_ISTIO)

        # Component: sas-annotations - NGINX
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NGINX: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.DEPLOYMENT: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResource.Kinds.REPLICA_SET: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResource.Kinds.SERVICE: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME],
            KubernetesResource.Kinds.INGRESS: [
                COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME,
                COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME_DEPRECATED_DEFINITION
            ],
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NGINX: int = len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NGINX)

        # Component: sas-annotations - OpenShift
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_OPENSHIFT: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.DEPLOYMENT: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResource.Kinds.REPLICA_SET: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResource.Kinds.SERVICE: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME],
            KubernetesResource.Kinds.OPENSHIFT_ROUTE: [COMPONENT_SAS_ANNOTATIONS_OPENSHIFT_ROUTE_NAME],
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_OPENSHIFT: int = len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_OPENSHIFT)

        # Component: sas-cacheserver
        COMPONENT_SAS_CACHE_SERVER_POD_NAME: Text = "sas-cacheserver-0"
        COMPONENT_SAS_CACHE_SERVER_SERVICE_NAME: Text = "sas-cacheserver"
        COMPONENT_SAS_CACHE_SERVER_STATEFUL_SET_NAME: Text = "sas-cacheserver"

        COMPONENT_SAS_CACHE_SERVER_NAME: Text = "sas-cacheserver"
        COMPONENT_SAS_CACHE_SERVER_RESOURCE_DICT: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_CACHE_SERVER_POD_NAME],
            KubernetesResource.Kinds.SERVICE: [COMPONENT_SAS_CACHE_SERVER_SERVICE_NAME],
            KubernetesResource.Kinds.STATEFUL_SET: [COMPONENT_SAS_CACHE_SERVER_STATEFUL_SET_NAME]
        }
        COMPONENT_SAS_CACHE_SERVER_RESOURCE_COUNT: int = len(COMPONENT_SAS_CACHE_SERVER_RESOURCE_DICT)

        # Component: sas-cas-operator
        COMPONENT_SAS_CAS_OPERATOR_DEPLOYMENT_NAME: Text = "sas-cas-operator"
        COMPONENT_SAS_CAS_OPERATOR_POD_NAME: Text = "sas-cas-operator-7f8b77dc78-bq7bg"
        COMPONENT_SAS_CAS_OPERATOR_REPLICA_SET_NAME: Text = "sas-cas-operator-7f8b77dc78"
        COMPONENT_SAS_CAS_OPERATOR_SERVICE_NAME: Text = "sas-cas-operator"

        COMPONENT_SAS_CAS_OPERATOR_NAME: Text = "sas-cas-operator"
        COMPONENT_SAS_CAS_OPERATOR_RESOURCE_DICT: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.DEPLOYMENT: [COMPONENT_SAS_CAS_OPERATOR_DEPLOYMENT_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_CAS_OPERATOR_POD_NAME],
            KubernetesResource.Kinds.REPLICA_SET: [COMPONENT_SAS_CAS_OPERATOR_REPLICA_SET_NAME],
            KubernetesResource.Kinds.SERVICE: [COMPONENT_SAS_CAS_OPERATOR_SERVICE_NAME]
        }
        COMPONENT_SAS_CAS_OPERATOR_RESOURCE_COUNT: int = len(COMPONENT_SAS_CAS_OPERATOR_RESOURCE_DICT)

        # Component: sas-cas-server
        COMPONENT_SAS_CAS_SERVER_CAS_DEPLOYMENT_NAME: Text = "default"
        COMPONENT_SAS_CAS_SERVER_POD_NAME: Text = "sas-cas-server-default-controller"
        COMPONENT_SAS_CAS_SERVER_SERVICE_NAME: Text = "sas-cas-server-default"
        COMPONENT_SAS_CAS_SERVER_EXTNP_SERVICE_NAME: Text = "sas-cas-server-default-extnp"

        COMPONENT_SAS_CAS_SERVER_NAME: Text = COMPONENT_SAS_CAS_OPERATOR_NAME
        COMPONENT_SAS_CAS_SERVER_RESOURCE_DICT: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.CAS_DEPLOYMENT: [COMPONENT_SAS_CAS_SERVER_CAS_DEPLOYMENT_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_CAS_SERVER_POD_NAME],
            KubernetesResource.Kinds.SERVICE: [
                COMPONENT_SAS_CAS_SERVER_SERVICE_NAME,
                COMPONENT_SAS_CAS_SERVER_EXTNP_SERVICE_NAME
            ]
        }
        COMPONENT_SAS_CAS_SERVER_RESOURCE_COUNT: int = len(COMPONENT_SAS_CAS_SERVER_RESOURCE_DICT)

        # Component: sas-scheduled-backup-job
        COMPONENT_SAS_SCHEDULED_BACKUP_JOB_CRON_JOB_NAME: Text = "sas-scheduled-backup-job"
        COMPONENT_SAS_SCHEDULED_BACKUP_JOB_JOB_NAME: Text = "sas-scheduled-backup-job-1589072400"
        COMPONENT_SAS_SCHEDULED_BACKUP_JOB_POD_NAME: Text = "sas-scheduled-backup-job-1589072400-5kfgj"

        COMPONENT_SAS_SCHEDULED_BACKUP_JOB_NAME: Text = "sas-backup-job"
        COMPONENT_SAS_SCHEDULED_BACKUP_JOB_RESOURCE_DICT: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.CRON_JOB: [COMPONENT_SAS_SCHEDULED_BACKUP_JOB_CRON_JOB_NAME],
            KubernetesResource.Kinds.JOB: [COMPONENT_SAS_SCHEDULED_BACKUP_JOB_JOB_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_SCHEDULED_BACKUP_JOB_POD_NAME]
        }
        COMPONENT_SAS_SCHEDULED_BACKUP_JOB_RESOURCE_COUNT: int = len(COMPONENT_SAS_SCHEDULED_BACKUP_JOB_RESOURCE_DICT)

        # Components
        COMPONENT_NAMES_LIST: List[Text] = [
            COMPONENT_PROMETHEUS_NAME,
            COMPONENT_SAS_ANNOTATIONS_NAME,
            COMPONENT_SAS_CACHE_SERVER_NAME,
            COMPONENT_SAS_CAS_OPERATOR_NAME,
            COMPONENT_SAS_SCHEDULED_BACKUP_JOB_NAME
        ]
        COMPONENT_COUNT: int = len(COMPONENT_NAMES_LIST)

        # Resource: All
        RESOURCE_LIST_ALL: List[Text] = [
            KubernetesResource.Kinds.CAS_DEPLOYMENT,
            KubernetesResource.Kinds.CONFIGMAP,
            KubernetesResource.Kinds.CONTOUR_HTTPPROXY,
            KubernetesResource.Kinds.CRON_JOB,
            KubernetesResource.Kinds.DEPLOYMENT,
            KubernetesResource.Kinds.INGRESS,
            KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE,
            KubernetesResource.Kinds.JOB,
            KubernetesResource.Kinds.NODE,
            KubernetesResource.Kinds.NODE_METRICS,
            KubernetesResource.Kinds.OPENSHIFT_ROUTE,
            KubernetesResource.Kinds.POD,
            KubernetesResource.Kinds.POD_METRICS,
            KubernetesResource.Kinds.REPLICA_SET,
            KubernetesResource.Kinds.SERVICE,
            KubernetesResource.Kinds.STATEFUL_SET
        ]
        RESOURCE_LIST_ALL_COUNT: int = len(RESOURCE_LIST_ALL)

        # Resource: Contour Ingress
        RESOURCE_LIST_CONTOUR: List[Text] = [
            KubernetesResource.Kinds.CAS_DEPLOYMENT,
            KubernetesResource.Kinds.CONFIGMAP,
            KubernetesResource.Kinds.CONTOUR_HTTPPROXY,
            KubernetesResource.Kinds.CRON_JOB,
            KubernetesResource.Kinds.DEPLOYMENT,
            KubernetesResource.Kinds.JOB,
            KubernetesResource.Kinds.NODE,
            KubernetesResource.Kinds.NODE_METRICS,
            KubernetesResource.Kinds.POD,
            KubernetesResource.Kinds.POD_METRICS,
            KubernetesResource.Kinds.REPLICA_SET,
            KubernetesResource.Kinds.SERVICE,
            KubernetesResource.Kinds.STATEFUL_SET
        ]
        RESOURCE_LIST_CONTOUR_COUNT: int = len(RESOURCE_LIST_CONTOUR)

        # Resource: Istio Ingress
        RESOURCE_LIST_ISTIO: List[Text] = [
            KubernetesResource.Kinds.CAS_DEPLOYMENT,
            KubernetesResource.Kinds.CONFIGMAP,
            KubernetesResource.Kinds.CRON_JOB,
            KubernetesResource.Kinds.DEPLOYMENT,
            KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE,
            KubernetesResource.Kinds.JOB,
            KubernetesResource.Kinds.NODE,
            KubernetesResource.Kinds.NODE_METRICS,
            KubernetesResource.Kinds.POD,
            KubernetesResource.Kinds.POD_METRICS,
            KubernetesResource.Kinds.REPLICA_SET,
            KubernetesResource.Kinds.SERVICE,
            KubernetesResource.Kinds.STATEFUL_SET
        ]
        RESOURCE_LIST_ISTIO_COUNT: int = len(RESOURCE_LIST_ISTIO)

        # Resource: NGINX Ingress
        RESOURCE_LIST_NGINX: List[Text] = [
            KubernetesResource.Kinds.CAS_DEPLOYMENT,
            KubernetesResource.Kinds.CONFIGMAP,
            KubernetesResource.Kinds.CRON_JOB,
            KubernetesResource.Kinds.DEPLOYMENT,
            KubernetesResource.Kinds.INGRESS,
            KubernetesResource.Kinds.JOB,
            KubernetesResource.Kinds.NODE,
            KubernetesResource.Kinds.NODE_METRICS,
            KubernetesResource.Kinds.POD,
            KubernetesResource.Kinds.POD_METRICS,
            KubernetesResource.Kinds.REPLICA_SET,
            KubernetesResource.Kinds.SERVICE,
            KubernetesResource.Kinds.STATEFUL_SET
        ]
        RESOURCE_LIST_NGINX_COUNT: int = len(RESOURCE_LIST_NGINX)

        # Resource: OpenShift Ingress
        RESOURCE_LIST_OPENSHIFT: List[Text] = [
            KubernetesResource.Kinds.CAS_DEPLOYMENT,
            KubernetesResource.Kinds.CONFIGMAP,
            KubernetesResource.Kinds.CRON_JOB,
            KubernetesResource.Kinds.DEPLOYMENT,
            KubernetesResource.Kinds.JOB,
            KubernetesResource.Kinds.NODE,
            KubernetesResource.Kinds.NODE_METRICS,
            KubernetesResource.Kinds.OPENSHIFT_ROUTE,
            KubernetesResource.Kinds.POD,
            KubernetesResource.Kinds.POD_METRICS,
            KubernetesResource.Kinds.REPLICA_SET,
            KubernetesResource.Kinds.SERVICE,
            KubernetesResource.Kinds.STATEFUL_SET
        ]
        RESOURCE_LIST_OPENSHIFT_COUNT: int = len(RESOURCE_LIST_OPENSHIFT)

        # Resource: CASDeployment
        RESOURCE_CAS_DEPLOYMENT_LIST: List[Text] = [
            COMPONENT_SAS_CAS_SERVER_CAS_DEPLOYMENT_NAME
        ]
        RESOURCE_CAS_DEPLOYMENT_COUNT: int = len(RESOURCE_CAS_DEPLOYMENT_LIST)

        # Resource: Contour HTTPProxy
        RESOURCE_HTTPPROXY_LIST: List[Text] = [
            COMPONENT_SAS_ANNOTATIONS_CONTOUR_HTTPPROXY_NAME
        ]
        RESOURCE_HTTPPROXY_COUNT: int = len(RESOURCE_HTTPPROXY_LIST)

        # Resource: CronJob
        RESOURCE_CRON_JOB_LIST: List[Text] = [
            COMPONENT_SAS_SCHEDULED_BACKUP_JOB_CRON_JOB_NAME
        ]
        RESOURCE_CRON_JOB_COUNT: int = len(RESOURCE_CRON_JOB_LIST)

        # Resource: Deployment
        RESOURCE_DEPLOYMENT_LIST: List[Text] = [
            COMPONENT_PROMETHEUS_DEPLOYMENT_NAME,
            COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME,
            COMPONENT_SAS_CAS_OPERATOR_DEPLOYMENT_NAME]
        RESOURCE_DEPLOYMENT_COUNT: int = len(RESOURCE_DEPLOYMENT_LIST)

        # Resource: Ingress
        RESOURCE_INGRESS_LIST: List[Text] = [
            COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME,
            COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME_DEPRECATED_DEFINITION
        ]
        RESOURCE_INGRESS_COUNT: int = len(RESOURCE_INGRESS_LIST)

        # Resource: Istio VirtualService
        RESOURCE_VIRTUAL_SERVICE_LIST: List[Text] = [
            COMPONENT_SAS_ANNOTATIONS_VIRTUAL_SERVICE_NAME
        ]
        RESOURCE_VIRTUAL_SERVICE_COUNT: int = len(RESOURCE_VIRTUAL_SERVICE_LIST)

        # Resource: Job
        RESOURCE_JOB_LIST: List[Text] = [
            COMPONENT_SAS_SCHEDULED_BACKUP_JOB_JOB_NAME
        ]
        RESOURCE_JOB_COUNT: int = len(RESOURCE_JOB_LIST)

        # Resource: Node
        RESOURCE_NODE_1_NAME: Text = "k8s-master-node.test.sas.com"
        RESOURCE_NODE_LIST: List[Text] = [
            RESOURCE_NODE_1_NAME
        ]
        RESOURCE_NODE_COUNT: int = len(RESOURCE_NODE_LIST)

        # Resource: OpenShift Route
        RESOURCE_ROUTE_LIST: List[Text] = [
            COMPONENT_SAS_ANNOTATIONS_OPENSHIFT_ROUTE_NAME
        ]
        RESOURCE_ROUTE_COUNT: int = len(RESOURCE_ROUTE_LIST)

        # Resource: Pod
        RESOURCE_POD_LIST: List[Text] = [
            COMPONENT_PROMETHEUS_POD_NAME,
            COMPONENT_SAS_ANNOTATIONS_POD_NAME,
            COMPONENT_SAS_SCHEDULED_BACKUP_JOB_POD_NAME,
            COMPONENT_SAS_CACHE_SERVER_POD_NAME,
            COMPONENT_SAS_CAS_OPERATOR_POD_NAME,
            COMPONENT_SAS_CAS_SERVER_POD_NAME
        ]
        RESOURCE_POD_COUNT: int = len(RESOURCE_POD_LIST)

        # Resource: ReplicaSet
        RESOURCE_REPLICA_SET_LIST: List[Text] = [
            COMPONENT_PROMETHEUS_REPLICA_SET_NAME,
            COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME,
            COMPONENT_SAS_CAS_OPERATOR_REPLICA_SET_NAME
        ]
        RESOURCE_REPLICA_SET_COUNT: int = len(RESOURCE_REPLICA_SET_LIST)

        # Resource: Service
        RESOURCE_SERVICE_LIST: List[Text] = [
            COMPONENT_PROMETHEUS_SERVICE_NAME,
            COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME,
            COMPONENT_SAS_CACHE_SERVER_SERVICE_NAME,
            COMPONENT_SAS_CAS_OPERATOR_SERVICE_NAME,
            COMPONENT_SAS_CAS_SERVER_SERVICE_NAME,
            COMPONENT_SAS_CAS_SERVER_EXTNP_SERVICE_NAME
        ]
        RESOURCE_SERVICE_COUNT: int = len(RESOURCE_SERVICE_LIST)

        # Resource: StatefulSet
        RESOURCE_STATEFUL_SET_LIST: List[Text] = [
            COMPONENT_SAS_CACHE_SERVER_STATEFUL_SET_NAME
        ]
        RESOURCE_STATEFUL_SET_COUNT: int = len(RESOURCE_STATEFUL_SET_LIST)

    ################################################################
    # ### KubectlTest functions
    ################################################################

    def __init__(self,
                 ingress_simulator: IngressSimulator = IngressSimulator.ONLY_NGINX,
                 include_metrics: bool = True,
                 include_non_namespaced_resources: bool = True,
                 namespace: Text = Values.NAMESPACE,
                 simulate_empty_deployment: bool = False) -> None:
        """
        Constructor for the KubectlTest implementation.

        :param ingress_simulator: The enumerated IngressSimulator value to use when returning data.
        :param include_metrics: True if resource metrics should be returned, otherwise False.
        :param include_non_namespaced_resources: True if non-namespaced resources should be returned, otherwise False.
        :param namespace: The namespace to target. For testing, if the namespace doesn't equal it's default value, a
                          CalledProcessError will be raised.
        :param simulate_empty_deployment: Simulates an empty deployment by not returning any resources (as if none have
                                          been created).
        """
        self.ingress_simulator = ingress_simulator
        self.include_metrics = include_metrics
        self.include_non_namespaced_resources = include_non_namespaced_resources
        self.namespace = namespace
        self.simulate_empty_deployment = simulate_empty_deployment

    def get_namespace(self) -> Text:
        return self.namespace

    def do(self, command: Text, ignore_errors: bool = False, success_rcs: Optional[List[int]] = None) -> AnyStr:
        return "Not functional in testing implementation"

    def api_resources(self, ignore_errors: bool = False) -> KubernetesApiResources:
        api_resources_data: Dict = dict()

        # check for ingress simulation to determine which API resources should be returned
        # None
        if self.ingress_simulator == self.IngressSimulator.NONE:
            api_resources_data = KubectlTest._load_response_data(_API_RESOURCES_NO_INGRESS_DATA_)

        # All included
        elif 0 < self.ingress_simulator.value <= 4:
            api_resources_data = KubectlTest._load_response_data(_API_RESOURCES_All_INGRESSES_DATA_)

        # Contour
        elif self.ingress_simulator == self.IngressSimulator.ONLY_CONTOUR:
            api_resources_data = KubectlTest._load_response_data(_API_RESOURCES_CONTOUR_ONLY_DATA_)

        # Istio
        elif self.ingress_simulator == self.IngressSimulator.ONLY_ISTIO:
            api_resources_data = KubectlTest._load_response_data(_API_RESOURCES_ISTIO_ONLY_DATA_)

        # NGINX
        elif self.ingress_simulator == self.IngressSimulator.ONLY_NGINX:
            api_resources_data = KubectlTest._load_response_data(_API_RESOURCES_NGINX_ONLY_DATA_)

        # OpenShift
        elif self.ingress_simulator == self.IngressSimulator.ONLY_OPENSHIFT:
            api_resources_data = KubectlTest._load_response_data(_API_RESOURCES_OPENSHIFT_ONLY_DATA_)

        return KubernetesApiResources(api_resources_data)

    def api_versions(self, ignore_errors: bool = False) -> List:
        return KubectlTest._load_response_data(_API_VERSIONS_DATA_)

    def can_i(self, action: Text, all_namespaces: bool = False, ignore_errors: bool = False) -> bool:
        # this method is not functional in the testing implementation
        return False

    def cluster_info(self) -> Optional[AnyStr]:
        pass

    def manage_resource(self, action: Text, file: Text, ignore_errors: bool = False, ) -> AnyStr:
        pass

    def config_view(self, raw: bool = False, ignore_errors: bool = False) -> Dict:
        return KubectlTest._load_response_data(_CONFIG_VIEW_DATA_)

    def get_resources(self, k8s_api_resource: Text, raw: bool = False) -> Union[Dict, List[KubernetesResource]]:
        # if the resource name is None, raise a CalledProcessError
        if k8s_api_resource is None:
            raise CalledProcessError(1, f"kubectl get {k8s_api_resource} -o json")

        # if the expected namespace isn't set, raise a CalledProcessError
        if self.namespace != self.Values.NAMESPACE:
            raise CalledProcessError(1, f"kubectl -n {self.namespace} get {k8s_api_resource.lower()} -o json")

        # return an empty list if simulating an empty deployment
        if self.simulate_empty_deployment:
            return list()

        # handle any ingress simulation - this logic covers scenarios where no resources would be returned
        # Contour
        if k8s_api_resource.lower() == "httpproxy" and \
                self.ingress_simulator != self.IngressSimulator.ALL_CONTOUR_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_CONTOUR:
            return list()

        # Istio
        elif k8s_api_resource.lower() == "virtualservices" and \
                self.ingress_simulator != self.IngressSimulator.ALL_ISTIO_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_ISTIO:
            return list()

        # NGINX
        elif k8s_api_resource.lower() == "ingresses" and \
                self.ingress_simulator != self.IngressSimulator.ALL_NGINX_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_NGINX:
            return list()

        # OpenShift
        elif k8s_api_resource.lower() == "routes" and \
                self.ingress_simulator != self.IngressSimulator.ALL_OPENSHIFT_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_OPENSHIFT:
            return list()

        # handle non-namespaced resources
        if not self.include_non_namespaced_resources and (k8s_api_resource.lower() == "nodes" or
                                                          k8s_api_resource.lower() == "namespaces"):
            raise CalledProcessError(1, f"kubectl get {k8s_api_resource.lower()} -o json")

        # if the resource should not be represented as unavailable, load the response from the file
        resources_dict: Dict = KubectlTest._load_response_data(f"resources_{k8s_api_resource.lower()}.json")

        # convert the raw JSON to KubernetesResource objects
        resources: List[KubernetesResource] = list()
        for resource in resources_dict:
            resources.append(KubernetesResource(resource))

        return resources

    def get_resource(self, k8s_api_resource: Text, resource_name: Text, raw: bool = False, ignore_errors: bool = False)\
            -> Union[AnyStr, KubernetesResource]:
        # if the resource name is None, raise a CalledProcessError
        if k8s_api_resource is None:
            raise CalledProcessError(1, f"kubectl get {k8s_api_resource} {resource_name} -o json")

        # raise a CalledProcessError if an unexpected namespace is given
        if self.namespace != self.Values.NAMESPACE:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {k8s_api_resource.lower()} {resource_name} "
                                     "-o json")

        # throw an error if simulating an empty deployment
        if self.simulate_empty_deployment:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {k8s_api_resource.lower()} {resource_name} "
                                     "-o json")

        # handle any ingress simulation - this logic covers scenarios where no resources would be returned
        # Contour
        if k8s_api_resource.lower() == "httpproxy" and \
                self.ingress_simulator != self.IngressSimulator.ALL_CONTOUR_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_CONTOUR:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {k8s_api_resource.lower()} {resource_name} "
                                        "-o json")

        # Istio
        elif k8s_api_resource.lower() == "virtualservices" and \
                self.ingress_simulator != self.IngressSimulator.ALL_ISTIO_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_ISTIO:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {k8s_api_resource.lower()} {resource_name} "
                                        "-o json")

        # NGINX
        elif k8s_api_resource.lower() == "ingresses" and \
                self.ingress_simulator != self.IngressSimulator.ALL_NGINX_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_NGINX:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {k8s_api_resource.lower()} {resource_name} "
                                        "-o json")

        # OpenShift
        elif k8s_api_resource.lower() == "routes" and \
                self.ingress_simulator != self.IngressSimulator.ALL_OPENSHIFT_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_OPENSHIFT:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {k8s_api_resource.lower()} {resource_name} "
                                        "-o json")

        # handle non-namespaced resources
        if not self.include_non_namespaced_resources and (k8s_api_resource.lower() == "nodes" or
                                                          k8s_api_resource.lower() == "namespaces"):
            raise CalledProcessError(1, f"kubectl get {k8s_api_resource.lower()} {resource_name} -o json")

        # if the resource should not be represented as unavailable, load it from the file
        raw_resources_dict: Dict = KubectlTest._load_response_data(f"resources_{k8s_api_resource.lower()}.json")

        # iterate to find the requested resource
        for raw_resource in raw_resources_dict:
            resource: KubernetesResource = KubernetesResource(raw_resource)

            if resource.get_name() == resource_name:
                return resource

        # if the resource isn't found by name, raise a CalledProcessError
        raise CalledProcessError(1, f"kubectl get {k8s_api_resource.lower()} {resource_name} -o json")

    def logs(self, pod_name: Text, container_name: Optional[Text] = None, prefix: bool = True, tail: int = 10,
             ignore_errors: bool = False) -> List:
        # raise a CalledProcessError if an unexpected namespace is given
        if self.namespace != self.Values.NAMESPACE:
            raise CalledProcessError(1, f"kubectl -n {self.namespace} logs {pod_name}")

        # raise an error if simulating an empty deployment
        if self.simulate_empty_deployment:
            raise CalledProcessError(1, f"kubectl -n {self.namespace} logs {pod_name}")

        return [
            "test log line 1",
            "test log line 2",
            "test log line 3",
            "test log line 4",
            "test log line 5",
            "test log line 6",
            "test log line 7",
            "test log line 8",
            "test log line 9",
            "test log line 10"
        ]

    def top_nodes(self, ignore_errors: bool = False) -> KubernetesMetrics:
        # raise a CalledProcessError if an unexpected namespace is given
        if self.namespace != self.Values.NAMESPACE:
            raise CalledProcessError(1, f"kubectl -n {self.namespace} top nodes")

        # if metrics should not be included, raise an error like the live Kubectl method would
        if not self.include_metrics or not self.include_non_namespaced_resources or self.simulate_empty_deployment:
            raise CalledProcessError(1, "kubectl top nodes")

        # otherwise load the data from file and return as a KubernetesMetrics object
        raw_metrics: Dict = KubectlTest._load_response_data(_TOP_NODES_DATA_)
        return KubernetesMetrics(raw_metrics)

    def top_pods(self, ignore_errors: bool = False) -> KubernetesMetrics:
        # raise a CalledProcessError if an unexpected namespace is given
        if self.namespace != self.Values.NAMESPACE:
            raise CalledProcessError(1, f"kubectl -n {self.namespace} top pods")

        # if metrics should not be included, raise an error like the live Kubectl method would
        if not self.include_metrics or self.simulate_empty_deployment:
            raise CalledProcessError(1, "kubectl top pods")

        # otherwise load the data from file and return as a KubernetesMetrics object
        raw_metrics: Dict = KubectlTest._load_response_data(_TOP_PODS_DATA_)
        return KubernetesMetrics(raw_metrics)

    def version(self, ignore_errors: bool = False) -> Dict:
        return KubectlTest._load_response_data(_VERSIONS_DATA_)

    @staticmethod
    def _load_response_data(filename: Text) -> Union[Dict, List]:
        """
        Internal method used for loading the response data stored in JSON files.

        :param filename: The name of the response_data file to load.
        :return: The JSON data from the requested file converted to a Python-native list or dict.
        """
        # get the current directory of this script to create absolute path
        current_dir: Text = os.path.dirname(os.path.abspath(__file__))
        # join the path to this file with the remaining path to the requested test data
        test_data_file: Text = os.path.join(current_dir, f"response_data{os.sep}{filename}")
        # open the test file and return the contents as a Python-native dictionary
        with open(test_data_file, "r") as test_data_file_pointer:
            return json.load(test_data_file_pointer)
