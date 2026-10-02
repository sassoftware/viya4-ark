####################################################################
# ### sas_kubectl_test.py                                        ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021-2026, SAS Institute Inc., Cary, NC, USA.    ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import json
import os

from enum import Enum
from subprocess import CalledProcessError
from typing import AnyStr, Dict, List, Text, Union, Optional

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues
from viya_ark_library.k8s.sas_k8s_objects import KubernetesAvailableResourceTypes, KubernetesMetrics, KubernetesResource
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
        # No ingress resource types will be included in the resources returned by api_resources()
        NONE = 0

        # All resource types will be returned by api_resources() but only Contour HTTPProxy objects will be found
        ALL_CONTOUR_USED = 1

        # All resource types will be returned by api_resources() but only Istio VirtualService objects will be found
        ALL_ISTIO_USED = 2

        # All resource types will be returned by api_resources() but only Ingress objects will be found
        ALL_NGINX_USED = 3

        # All resource types will be returned by api_resources() but only OpenShift Route objects will be found
        ALL_OPENSHIFT_USED = 4

        # Only the Contour HTTPProxy type will be included in the resources returned by api_resources()
        ONLY_CONTOUR = 5

        # Only the Istio VirtualService type will be included in the resources returned by api_resources()
        ONLY_ISTIO = 6

        # Only the Ingress type will be included in the resources returned by api_resources()
        ONLY_NGINX = 7

        # Only the OpenShift Route type will be included in the resources returned by api_resources()
        ONLY_OPENSHIFT = 8

        GATEWAY_API_ENVOY = 9
        GATEWAY_API_UNKNOWN = 10
        GATEWAY_API_VERSION_UNAVAILABLE = 11
        GATEWAY_API_ACCESS_DENIED = 12
        GATEWAY_API_DIGEST_ONLY = 13
        GATEWAY_API_GATEWAY_ACCESS_DENIED = 14
        GATEWAY_API_CROSS_NAMESPACE_ROUTE = 15
        GATEWAY_API_DISTRACTOR_ROUTE = 16
        GATEWAY_API_AMBIGUOUS_GATEWAYS = 17
        GATEWAY_API_STALE_PARENT = 18
        GATEWAY_API_AMBIGUOUS_VERSION = 19
        GATEWAY_API_LISTENER_SET = 20
        GATEWAY_API_LISTENER_SET_DEFAULT_NAMESPACE = 21
        GATEWAY_API_LISTENER_SET_HOST_MISMATCH = 22
        GATEWAY_API_LISTENER_SET_WILDCARD_HOST = 23
        GATEWAY_API_LISTENER_SET_ACCESS_DENIED = 24
        GATEWAY_API_LISTENER_SET_MISSING = 25

    ################################################################
    # ### CLASS: KubectlTest.Values
    ################################################################
    class Values(object):
        """
        Class providing static references to values returned by the KubectlTest implementation.
        """
        NAMESPACE: Text = "test"
        CADENCEINFO: Text = "Fast R/TR 2020 (20201214.1607958443388)"
        DB_External: Text = "External"
        DB_Internal: Text = "Internal"
        DB_DATASERVER_PORT = 5432
        INGRESS_NAMESPACE: Text = ""

        # Component: prometheus
        COMPONENT_PROMETHEUS_DEPLOYMENT_NAME: Text = "pushgateway-test-prometheus-pushgateway"
        COMPONENT_PROMETHEUS_POD_NAME: Text = "pushgateway-test-prometheus-pushgateway-df9d7c96c-4n66t"
        COMPONENT_PROMETHEUS_REPLICA_SET_NAME: Text = "pushgateway-test-prometheus-pushgateway-df9d7c96c"
        COMPONENT_PROMETHEUS_SERVICE_NAME: Text = "pushgateway-test-prometheus-pushgateway"

        COMPONENT_PROMETHEUS_NAME: Text = "pushgateway-test-prometheus-pushgateway"
        COMPONENT_PROMETHEUS_RESOURCES_DICT: Dict[Text, List[Text]] = {
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS: [COMPONENT_PROMETHEUS_DEPLOYMENT_NAME],
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_PROMETHEUS_POD_NAME],
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS: [COMPONENT_PROMETHEUS_REPLICA_SET_NAME],
            KubernetesResourceTypeValues.K8S_CORE_SERVICES: [COMPONENT_PROMETHEUS_SERVICE_NAME]
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
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResourceTypeValues.K8S_CORE_SERVICES: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NO_INGRESS: int = \
            len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NO_INGRESS)

        # Component: sas-annotations - Contour
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_CONTOUR: Dict[Text, List[Text]] = {
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResourceTypeValues.K8S_CORE_SERVICES: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME],
            KubernetesResourceTypeValues.CONTOUR_HTTP_PROXIES: [COMPONENT_SAS_ANNOTATIONS_CONTOUR_HTTPPROXY_NAME],
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_CONTOUR: int = len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_CONTOUR)

        # Component: sas-annotations - Istio
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_ISTIO: Dict[Text, List[Text]] = {
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResourceTypeValues.K8S_CORE_SERVICES: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME],
            KubernetesResourceTypeValues.ISTIO_VIRTUAL_SERVICES: [COMPONENT_SAS_ANNOTATIONS_VIRTUAL_SERVICE_NAME],
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_ISTIO: int = len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_ISTIO)

        # Component: sas-annotations - NGINX
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NGINX: Dict[Text, List[Text]] = {
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResourceTypeValues.K8S_CORE_SERVICES: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME],
            KubernetesResourceTypeValues.K8S_EXTENSIONS_INGRESSES: [
                COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME_DEPRECATED_DEFINITION
            ],
            KubernetesResourceTypeValues.K8S_NETWORKING_INGRESSES: [COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME]
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NGINX: int = len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NGINX)

        # Component: sas-annotations - OpenShift
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_OPENSHIFT: Dict[Text, List[Text]] = {
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResourceTypeValues.K8S_CORE_SERVICES: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME],
            KubernetesResourceTypeValues.OPENSHIFT_ROUTES: [COMPONENT_SAS_ANNOTATIONS_OPENSHIFT_ROUTE_NAME],
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_OPENSHIFT: int = len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_OPENSHIFT)

        # Component: sas-cacheserver
        COMPONENT_SAS_CACHE_SERVER_POD_NAME: Text = "sas-cacheserver-0"
        COMPONENT_SAS_CACHE_SERVER_SERVICE_NAME: Text = "sas-cacheserver"
        COMPONENT_SAS_CACHE_SERVER_STATEFUL_SET_NAME: Text = "sas-cacheserver"

        COMPONENT_SAS_CACHE_SERVER_NAME: Text = "sas-cacheserver"
        COMPONENT_SAS_CACHE_SERVER_RESOURCE_DICT: Dict[Text, List[Text]] = {
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_SAS_CACHE_SERVER_POD_NAME],
            KubernetesResourceTypeValues.K8S_CORE_SERVICES: [COMPONENT_SAS_CACHE_SERVER_SERVICE_NAME],
            KubernetesResourceTypeValues.K8S_APPS_STATEFUL_SETS: [COMPONENT_SAS_CACHE_SERVER_STATEFUL_SET_NAME]
        }
        COMPONENT_SAS_CACHE_SERVER_RESOURCE_COUNT: int = len(COMPONENT_SAS_CACHE_SERVER_RESOURCE_DICT)

        # Component: sas-cas-operator
        COMPONENT_SAS_CAS_OPERATOR_DEPLOYMENT_NAME: Text = "sas-cas-operator"
        COMPONENT_SAS_CAS_OPERATOR_POD_NAME: Text = "sas-cas-operator-7f8b77dc78-bq7bg"
        COMPONENT_SAS_CAS_OPERATOR_REPLICA_SET_NAME: Text = "sas-cas-operator-7f8b77dc78"
        COMPONENT_SAS_CAS_OPERATOR_SERVICE_NAME: Text = "sas-cas-operator"

        COMPONENT_SAS_CAS_OPERATOR_NAME: Text = "sas-cas-operator"
        COMPONENT_SAS_CAS_OPERATOR_RESOURCE_DICT: Dict[Text, List[Text]] = {
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS: [COMPONENT_SAS_CAS_OPERATOR_DEPLOYMENT_NAME],
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_SAS_CAS_OPERATOR_POD_NAME],
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS: [COMPONENT_SAS_CAS_OPERATOR_REPLICA_SET_NAME],
            KubernetesResourceTypeValues.K8S_CORE_SERVICES: [COMPONENT_SAS_CAS_OPERATOR_SERVICE_NAME]
        }
        COMPONENT_SAS_CAS_OPERATOR_RESOURCE_COUNT: int = len(COMPONENT_SAS_CAS_OPERATOR_RESOURCE_DICT)

        # Component: sas-cas-server
        COMPONENT_SAS_CAS_SERVER_CAS_DEPLOYMENT_NAME: Text = "default"
        COMPONENT_SAS_CAS_SERVER_POD_NAME: Text = "sas-cas-server-default-controller"
        COMPONENT_SAS_CAS_SERVER_SERVICE_NAME: Text = "sas-cas-server-default"
        COMPONENT_SAS_CAS_SERVER_EXTNP_SERVICE_NAME: Text = "sas-cas-server-default-extnp"

        COMPONENT_SAS_CAS_SERVER_NAME: Text = COMPONENT_SAS_CAS_OPERATOR_NAME
        COMPONENT_SAS_CAS_SERVER_RESOURCE_DICT: Dict[Text, List[Text]] = {
            KubernetesResourceTypeValues.SAS_CAS_DEPLOYMENTS: [COMPONENT_SAS_CAS_SERVER_CAS_DEPLOYMENT_NAME],
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_SAS_CAS_SERVER_POD_NAME],
            KubernetesResourceTypeValues.K8S_CORE_SERVICES: [
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
            KubernetesResourceTypeValues.K8S_BATCH_CRON_JOBS: [COMPONENT_SAS_SCHEDULED_BACKUP_JOB_CRON_JOB_NAME],
            KubernetesResourceTypeValues.K8S_BATCH_JOBS: [COMPONENT_SAS_SCHEDULED_BACKUP_JOB_JOB_NAME],
            KubernetesResourceTypeValues.K8S_CORE_PODS: [COMPONENT_SAS_SCHEDULED_BACKUP_JOB_POD_NAME]
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
            KubernetesResourceTypeValues.SAS_CAS_DEPLOYMENTS,
            KubernetesResourceTypeValues.K8S_CORE_CONFIG_MAPS,
            KubernetesResourceTypeValues.K8S_BATCH_CRON_JOBS,
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS,
            KubernetesResourceTypeValues.K8S_BATCH_JOBS,
            KubernetesResourceTypeValues.K8S_CORE_NODES,
            KubernetesResourceTypeValues.CONTOUR_HTTP_PROXIES,
            KubernetesResourceTypeValues.K8S_EXTENSIONS_INGRESSES,
            KubernetesResourceTypeValues.K8S_NETWORKING_INGRESSES,
            KubernetesResourceTypeValues.ISTIO_VIRTUAL_SERVICES,
            KubernetesResourceTypeValues.OPENSHIFT_ROUTES,
            KubernetesResourceTypeValues.K8S_CORE_PODS,
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS,
            KubernetesResourceTypeValues.K8S_CORE_SECRETS,
            KubernetesResourceTypeValues.K8S_CORE_SERVICES,
            KubernetesResourceTypeValues.K8S_APPS_STATEFUL_SETS
        ]
        RESOURCE_LIST_ALL_COUNT: int = len(RESOURCE_LIST_ALL)

        # Resource: Contour Ingress
        RESOURCE_LIST_CONTOUR: List[Text] = [
            KubernetesResourceTypeValues.SAS_CAS_DEPLOYMENTS,
            KubernetesResourceTypeValues.K8S_CORE_CONFIG_MAPS,
            KubernetesResourceTypeValues.CONTOUR_HTTP_PROXIES,
            KubernetesResourceTypeValues.K8S_BATCH_CRON_JOBS,
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS,
            KubernetesResourceTypeValues.K8S_BATCH_JOBS,
            KubernetesResourceTypeValues.K8S_CORE_NODES,
            KubernetesResourceTypeValues.K8S_CORE_PODS,
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS,
            KubernetesResourceTypeValues.K8S_CORE_SECRETS,
            KubernetesResourceTypeValues.K8S_CORE_SERVICES,
            KubernetesResourceTypeValues.K8S_APPS_STATEFUL_SETS
        ]
        RESOURCE_LIST_CONTOUR_COUNT: int = len(RESOURCE_LIST_CONTOUR)

        # Resource: Istio Ingress
        RESOURCE_LIST_ISTIO: List[Text] = [
            KubernetesResourceTypeValues.SAS_CAS_DEPLOYMENTS,
            KubernetesResourceTypeValues.K8S_CORE_CONFIG_MAPS,
            KubernetesResourceTypeValues.K8S_BATCH_CRON_JOBS,
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS,
            KubernetesResourceTypeValues.ISTIO_VIRTUAL_SERVICES,
            KubernetesResourceTypeValues.K8S_BATCH_JOBS,
            KubernetesResourceTypeValues.K8S_CORE_NODES,
            KubernetesResourceTypeValues.K8S_CORE_PODS,
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS,
            KubernetesResourceTypeValues.K8S_CORE_SECRETS,
            KubernetesResourceTypeValues.K8S_CORE_SERVICES,
            KubernetesResourceTypeValues.K8S_APPS_STATEFUL_SETS
        ]
        RESOURCE_LIST_ISTIO_COUNT: int = len(RESOURCE_LIST_ISTIO)

        # Resource: NGINX Ingress
        RESOURCE_LIST_NGINX: List[Text] = [
            KubernetesResourceTypeValues.SAS_CAS_DEPLOYMENTS,
            KubernetesResourceTypeValues.K8S_CORE_CONFIG_MAPS,
            KubernetesResourceTypeValues.K8S_BATCH_CRON_JOBS,
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS,
            KubernetesResourceTypeValues.K8S_EXTENSIONS_INGRESSES,
            KubernetesResourceTypeValues.K8S_NETWORKING_INGRESSES,
            KubernetesResourceTypeValues.K8S_BATCH_JOBS,
            KubernetesResourceTypeValues.K8S_CORE_NODES,
            KubernetesResourceTypeValues.K8S_CORE_PODS,
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS,
            KubernetesResourceTypeValues.K8S_CORE_SECRETS,
            KubernetesResourceTypeValues.K8S_CORE_SERVICES,
            KubernetesResourceTypeValues.K8S_APPS_STATEFUL_SETS
        ]
        RESOURCE_LIST_NGINX_COUNT: int = len(RESOURCE_LIST_NGINX)

        # Resource: OpenShift Ingress
        RESOURCE_LIST_OPENSHIFT: List[Text] = [
            KubernetesResourceTypeValues.SAS_CAS_DEPLOYMENTS,
            KubernetesResourceTypeValues.K8S_CORE_CONFIG_MAPS,
            KubernetesResourceTypeValues.K8S_BATCH_CRON_JOBS,
            KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS,
            KubernetesResourceTypeValues.K8S_BATCH_JOBS,
            KubernetesResourceTypeValues.K8S_CORE_NODES,
            KubernetesResourceTypeValues.OPENSHIFT_ROUTES,
            KubernetesResourceTypeValues.K8S_CORE_PODS,
            KubernetesResourceTypeValues.K8S_APPS_REPLICA_SETS,
            KubernetesResourceTypeValues.K8S_CORE_SECRETS,
            KubernetesResourceTypeValues.K8S_CORE_SERVICES,
            KubernetesResourceTypeValues.K8S_APPS_STATEFUL_SETS
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

        # Resource: Ingress (extensions)
        RESOURCE_EXTENSIONS_INGRESS_LIST: List[Text] = [
            COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME_DEPRECATED_DEFINITION
        ]
        RESOURCE_EXTENSIONS_INGRESS_COUNT: int = len(RESOURCE_EXTENSIONS_INGRESS_LIST)

        # Resource: Ingress (networking.k8s.io)
        RESOURCE_NETWORKING_INGRESS_LIST: List[Text] = [
            COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME
        ]
        RESOURCE_NETWORKING_INGRESS_COUNT: int = len(RESOURCE_NETWORKING_INGRESS_LIST)

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
                 simulate_empty_deployment: bool = False,
                 ingress_ns: Text = Values.INGRESS_NAMESPACE) -> None:
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
        self.ingress_ns = ingress_ns

    def get_namespace(self) -> Text:
        return self.namespace

    def do(self, command: Text, ignore_errors: bool = False, success_rcs: Optional[List[int]] = None) -> AnyStr:
        return b"Not functional in testing implementation"

    def api_resources(self, ignore_errors: bool = False) -> KubernetesAvailableResourceTypes:
        api_resources_data: Dict = dict()

        # check for ingress simulation to determine which API resources should be returned
        # None
        if self.ingress_simulator == self.IngressSimulator.NONE:
            api_resources_data = KubectlTest._load_response_data(_API_RESOURCES_NO_INGRESS_DATA_)

        # All included
        elif 0 < self.ingress_simulator.value <= 4:
            api_resources_data = KubectlTest._load_response_data(_API_RESOURCES_All_INGRESSES_DATA_)

        elif self.ingress_simulator.value >= self.IngressSimulator.GATEWAY_API_ENVOY.value:
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

        if self.ingress_simulator.value >= self.IngressSimulator.GATEWAY_API_ENVOY.value:
            api_resources_data.update({
                KubernetesResourceTypeValues.GATEWAY_API_GATEWAY_CLASSES: {
                    "group": KubernetesResourceTypeValues.GATEWAY_API_GROUP,
                    "kind": "GatewayClass", "name": "gatewayclasses", "namespaced": False,
                    "shortname": "", "verbs": ["get", "list"], "version": "v1"
                },
                KubernetesResourceTypeValues.GATEWAY_API_GATEWAYS: {
                    "group": KubernetesResourceTypeValues.GATEWAY_API_GROUP,
                    "kind": "Gateway", "name": "gateways", "namespaced": True,
                    "shortname": "", "verbs": ["get", "list"], "version": "v1"
                },
                KubernetesResourceTypeValues.GATEWAY_API_HTTP_ROUTES: {
                    "group": KubernetesResourceTypeValues.GATEWAY_API_GROUP,
                    "kind": "HTTPRoute", "name": "httproutes", "namespaced": True,
                    "shortname": "", "verbs": ["get", "list"], "version": "v1"
                },
                KubernetesResourceTypeValues.GATEWAY_API_LISTENER_SETS: {
                    "group": KubernetesResourceTypeValues.GATEWAY_API_GROUP,
                    "kind": "ListenerSet", "name": "listenersets", "namespaced": True,
                    "shortname": "", "verbs": ["get", "list"], "version": "v1"
                }
            })
        return KubernetesAvailableResourceTypes(api_resources_data)

    def api_versions(self, ignore_errors: bool = False) -> List:
        return KubectlTest._load_response_data(_API_VERSIONS_DATA_)

    def ingress_version(self) -> Optional[AnyStr]:
        pass

    def can_i(self, action: Text, all_namespaces: bool = False, ignore_errors: bool = False) -> bool:
        # this method is not functional in the testing implementation
        return False

    def cluster_info(self) -> Optional[AnyStr]:
        # this method is not functional in the testing implementation
        pass

    def config_view(self, raw: bool = False, ignore_errors: bool = False) -> Dict:
        return KubectlTest._load_response_data(_CONFIG_VIEW_DATA_)

    def get_resources(self, type_version_group: Text, raw: bool = False) -> Union[Dict, List[KubernetesResource]]:
        # if the resource name is None, raise a CalledProcessError
        if type_version_group is None:
            raise CalledProcessError(1, f"kubectl get {type_version_group} -o json")

        # if the expected namespace isn't set, raise a CalledProcessError
        if self.namespace != self.Values.NAMESPACE:
            raise CalledProcessError(1, f"kubectl -n {self.namespace} get {type_version_group} -o json")

        # return an empty list if simulating an empty deployment
        if self.simulate_empty_deployment:
            return list()

        gateway_types = (
            KubernetesResourceTypeValues.GATEWAY_API_GATEWAY_CLASSES,
            KubernetesResourceTypeValues.GATEWAY_API_GATEWAYS,
            KubernetesResourceTypeValues.GATEWAY_API_HTTP_ROUTES,
            KubernetesResourceTypeValues.GATEWAY_API_LISTENER_SETS)
        if type_version_group.lower() in gateway_types:
            if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_ACCESS_DENIED and \
                    type_version_group.lower() == KubernetesResourceTypeValues.GATEWAY_API_GATEWAY_CLASSES:
                raise CalledProcessError(1, f"kubectl get {type_version_group} -o json")
            if type_version_group.lower() == KubernetesResourceTypeValues.GATEWAY_API_HTTP_ROUTES:
                routes = [self._gateway_api_route()]
                if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_DISTRACTOR_ROUTE:
                    routes.append(KubernetesResource({
                        "apiVersion": "gateway.networking.k8s.io/v1",
                        "kind": "HTTPRoute",
                        "metadata": {"name": "sas-route-other", "namespace": "other-system"},
                        "spec": {
                            "hostnames": ["unrelated.example.com"],
                            "parentRefs": [{
                                "group": "gateway.networking.k8s.io",
                                "kind": "Gateway",
                                "name": "sas-gateway",
                                "namespace": "other-gateway-system"
                            }],
                            "rules": [{"backendRefs": [{"kind": "Service", "name": "sas-annotations",
                                                        "namespace": self.namespace, "port": 80}]}]
                        }
                    }))
                elif self.ingress_simulator in (
                        self.IngressSimulator.GATEWAY_API_AMBIGUOUS_GATEWAYS,
                        self.IngressSimulator.GATEWAY_API_STALE_PARENT):
                    routes.append(KubernetesResource({
                        "apiVersion": "gateway.networking.k8s.io/v1",
                        "kind": "HTTPRoute",
                        "metadata": {"name": "sas-route-other", "namespace": "other-system"},
                        "spec": {
                            "hostnames": ["k8s-master-node.test.sas.com"],
                            "parentRefs": [{
                                "group": "gateway.networking.k8s.io",
                                "kind": "Gateway",
                                "name": "sas-gateway",
                                "namespace": "other-gateway-system"
                            }],
                            "rules": [{"backendRefs": [{"kind": "Service", "name": "sas-annotations",
                                                        "namespace": self.namespace, "port": 80}]}]
                        }
                    }))
                return routes
            if type_version_group.lower() == KubernetesResourceTypeValues.GATEWAY_API_LISTENER_SETS:
                return []
            if type_version_group.lower() == KubernetesResourceTypeValues.GATEWAY_API_GATEWAY_CLASSES:
                return [self._gateway_api_class()]
            return list()

        if self.ingress_simulator.value >= self.IngressSimulator.GATEWAY_API_ENVOY.value and \
                type_version_group.lower() in (
                    KubernetesResourceTypeValues.CONTOUR_HTTP_PROXIES,
                    KubernetesResourceTypeValues.K8S_EXTENSIONS_INGRESSES,
                    KubernetesResourceTypeValues.K8S_NETWORKING_INGRESSES,
                    KubernetesResourceTypeValues.OPENSHIFT_ROUTES,
                    KubernetesResourceTypeValues.ISTIO_VIRTUAL_SERVICES):
            raise CalledProcessError(1, f"kubectl get {type_version_group} -o json")

        # handle any ingress simulation - this logic covers scenarios where no resources would be returned
        # Contour
        if type_version_group.lower() == KubernetesResourceTypeValues.CONTOUR_HTTP_PROXIES and \
                self.ingress_simulator != self.IngressSimulator.ALL_CONTOUR_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_CONTOUR:
            return list()

        # Istio
        elif type_version_group.lower() == KubernetesResourceTypeValues.ISTIO_VIRTUAL_SERVICES and \
                self.ingress_simulator != self.IngressSimulator.ALL_ISTIO_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_ISTIO:
            return list()

        # NGINX

        elif (type_version_group.lower() == KubernetesResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
              type_version_group.lower() == KubernetesResourceTypeValues.K8S_NETWORKING_INGRESSES) and \
                self.ingress_simulator != self.IngressSimulator.ALL_NGINX_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_NGINX:
            return list()

        # OpenShift
        elif type_version_group.lower() == KubernetesResourceTypeValues.OPENSHIFT_ROUTES and \
                self.ingress_simulator != self.IngressSimulator.ALL_OPENSHIFT_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_OPENSHIFT:
            return list()

        # handle non-namespaced resources
        if not self.include_non_namespaced_resources and (type_version_group.lower() == "nodes" or
                                                          type_version_group.lower() == "namespaces"):
            raise CalledProcessError(1, f"kubectl get {type_version_group} -o json")

        # if the resource should not be represented as unavailable, load the response from the file
        resources_data: List = KubectlTest._load_response_data(f"resources_{type_version_group.lower()}.json")

        # load input ConfigMap resources for the ingress type
        if type_version_group.lower() == "configmaps":
            # Contour
            if self.ingress_simulator in (self.IngressSimulator.ALL_CONTOUR_USED, self.IngressSimulator.ONLY_CONTOUR):
                resources_data.extend(
                    KubectlTest._load_response_data(f"resources_{type_version_group.lower()}_ingress_contour.json")
                )
            # Istio
            elif self.ingress_simulator in (self.IngressSimulator.ALL_ISTIO_USED, self.IngressSimulator.ONLY_ISTIO):
                resources_data.extend(
                    KubectlTest._load_response_data(f"resources_{type_version_group.lower()}_ingress_istio.json")
                )
            # NGINX
            elif self.ingress_simulator in (self.IngressSimulator.ALL_NGINX_USED, self.IngressSimulator.ONLY_NGINX):
                resources_data.extend(
                    KubectlTest._load_response_data(f"resources_{type_version_group.lower()}_ingress_nginx.json")
                )
            # OpenShift
            elif self.ingress_simulator \
                    in (self.IngressSimulator.ALL_OPENSHIFT_USED, self.IngressSimulator.ONLY_OPENSHIFT):
                resources_data.extend(
                    KubectlTest._load_response_data(f"resources_{type_version_group.lower()}_ingress_openshift.json")
                )
            elif self.ingress_simulator.value >= self.IngressSimulator.GATEWAY_API_ENVOY.value:
                resources_data.append({
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {
                        "name": "ingress-input-gateway",
                        "namespace": self.namespace,
                        "labels": {"sas.com/deployment": "test"}
                    },
                    "data": {
                        "INGRESS_APIVERSION": "gateway.networking.k8s.io/v1",
                        "INGRESS_IMPLEMENTATION": "gateway.networking.k8s.io",
                        "INGRESS_KIND": "HTTPRoute",
                        "INGRESS_HOST": "k8s-master-node.test.sas.com",
                        "GATEWAY_NAME": "sas-gateway"
                    }
                })

        # convert the raw JSON to KubernetesResource objects
        resources: List[KubernetesResource] = list()
        for resource in resources_data:
            resources.append(KubernetesResource(resource))

        return resources

    def get_resources_all_namespaces(self, type_version_group: Text,
                                     raw: bool = False) -> Union[Dict, List[KubernetesResource]]:
        listener_set_scenarios = (
            self.IngressSimulator.GATEWAY_API_LISTENER_SET,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_DEFAULT_NAMESPACE,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_HOST_MISMATCH,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_WILDCARD_HOST,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_ACCESS_DENIED,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_MISSING,
        )
        if type_version_group.lower() == KubernetesResourceTypeValues.GATEWAY_API_LISTENER_SETS:
            if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_LISTENER_SET_ACCESS_DENIED:
                raise CalledProcessError(1, f"kubectl get {type_version_group} --all-namespaces -o json")
            if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_LISTENER_SET_MISSING:
                return []
            if self.ingress_simulator not in listener_set_scenarios:
                return []
            if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_LISTENER_SET_DEFAULT_NAMESPACE:
                return [self._gateway_api_listener_set("test", gateway_namespace=None)]
            listener_set = self._gateway_api_listener_set("listener-system")
            if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_LISTENER_SET:
                return [listener_set, self._gateway_api_listener_set(
                    "other-listener-system", hostname="other.example.com")]
            return [listener_set]
        if type_version_group.lower() == KubernetesResourceTypeValues.GATEWAY_API_GATEWAYS:
            if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_GATEWAY_ACCESS_DENIED:
                raise CalledProcessError(1, f"kubectl get {type_version_group} --all-namespaces -o json")
            if self.ingress_simulator in listener_set_scenarios:
                gateway_namespace = "test" if \
                    self.ingress_simulator == self.IngressSimulator.GATEWAY_API_LISTENER_SET_DEFAULT_NAMESPACE \
                    else "gw-system"
                return [self._gateway_api_gateway(gateway_namespace, "k8s-gw")]
            gateways = [self._gateway_api_gateway("gateway-system")]
            if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_AMBIGUOUS_GATEWAYS:
                gateways.append(self._gateway_api_gateway("other-gateway-system"))
            return gateways
        if type_version_group.lower() != KubernetesResourceTypeValues.K8S_APPS_DEPLOYMENTS:
            return self.get_resources(type_version_group, raw)
        if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_VERSION_UNAVAILABLE:
            raise CalledProcessError(1, f"kubectl get {type_version_group} --all-namespaces -o json")
        if self.ingress_simulator.value >= self.IngressSimulator.GATEWAY_API_ENVOY.value:
            image = "docker.io/envoyproxy/gateway:v1.8.2"
            if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_DIGEST_ONLY:
                image = "docker.io/envoyproxy/gateway@sha256:0123456789abcdef"
            deployments = [KubernetesResource({
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": "envoy-gateway", "namespace": "gateway-system"},
                "spec": {"template": {"spec": {"containers": [
                    {"name": "envoy-gateway", "image": image}
                ]}}}
            })]
            if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_AMBIGUOUS_VERSION:
                deployments.append(KubernetesResource({
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {"name": "envoy-gateway-old", "namespace": "old-gateway-system"},
                    "spec": {"template": {"spec": {"containers": [
                        {"name": "envoy-gateway", "image": "docker.io/envoyproxy/gateway:v1.1.0"}
                    ]}}}
                }))
            if self.ingress_simulator in listener_set_scenarios:
                deployments.append(KubernetesResource({
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {"name": "envoy-gateway-secondary", "namespace": "envoy-gateway-system"},
                    "spec": {"template": {"spec": {"containers": [
                        {"name": "envoy-gateway", "image": "docker.io/envoyproxy/gateway:v1.8.2"}
                    ]}}}
                }))
            return deployments
        return []

    def get_resources_cluster_scoped(self, type_version_group: Text,
                                     raw: bool = False) -> Union[Dict, List[KubernetesResource]]:
        return self.get_resources(type_version_group, raw)

    def get_resource_in_namespace(self, type_version_group: Text, resource_name: Text,
                                  namespace: Text) -> KubernetesResource:
        if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_GATEWAY_ACCESS_DENIED:
            raise CalledProcessError(1, f"kubectl get {type_version_group} {resource_name} -n {namespace} -o json")
        if type_version_group.lower() == KubernetesResourceTypeValues.GATEWAY_API_GATEWAYS and \
                resource_name == "sas-gateway" and namespace == "gateway-system":
            return self._gateway_api_gateway(namespace)
        if type_version_group.lower() == KubernetesResourceTypeValues.GATEWAY_API_GATEWAYS and \
                resource_name == "k8s-gw" and namespace in ("gw-system", "test"):
            return self._gateway_api_gateway(namespace, resource_name)
        raise CalledProcessError(1, f"kubectl get {type_version_group} {resource_name} -n {namespace} -o json")

    @staticmethod
    def _gateway_api_gateway(namespace: Text, name: Text = "sas-gateway") -> KubernetesResource:
        return KubernetesResource({
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "Gateway",
            "metadata": {"name": name, "namespace": namespace},
            "spec": {"gatewayClassName": "envoy-gateway-class"}
        })

    def _gateway_api_class(self) -> KubernetesResource:
        controller = "gateway.envoyproxy.io/gatewayclass-controller"
        if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_UNKNOWN:
            controller = "example.invalid/controller"
        return KubernetesResource({
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "GatewayClass",
            "metadata": {"name": "envoy-gateway-class"},
            "spec": {"controllerName": controller}
        })

    def _gateway_api_route(self) -> KubernetesResource:
        route_namespace = self.namespace
        backend_namespace = None
        if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_CROSS_NAMESPACE_ROUTE:
            route_namespace = "route-system"
            backend_namespace = self.namespace
        listener_set_scenarios = (
            self.IngressSimulator.GATEWAY_API_LISTENER_SET,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_DEFAULT_NAMESPACE,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_HOST_MISMATCH,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_WILDCARD_HOST,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_ACCESS_DENIED,
            self.IngressSimulator.GATEWAY_API_LISTENER_SET_MISSING,
        )
        if self.ingress_simulator in listener_set_scenarios:
            default_namespace_case = self.ingress_simulator == \
                self.IngressSimulator.GATEWAY_API_LISTENER_SET_DEFAULT_NAMESPACE
            parent_ref = {"kind": "ListenerSet", "name": "sas-listenerset"}
            if not default_namespace_case:
                parent_ref["namespace"] = "listener-system"
                route_namespace = "route-system"
            else:
                route_namespace = "test"
            return KubernetesResource({
                "apiVersion": "gateway.networking.k8s.io/v1",
                "kind": "HTTPRoute",
                "metadata": {"name": "sas-route", "namespace": route_namespace},
                "spec": {
                    "parentRefs": [parent_ref],
                    "hostnames": [],
                    "rules": [{"backendRefs": [{"kind": "Service", "name": "sas-annotations",
                                                "namespace": self.namespace, "port": 80}]}]
                }
            })
        backend_ref = {"kind": "Service", "name": "sas-annotations", "port": 80}
        if backend_namespace:
            backend_ref["namespace"] = backend_namespace
        return KubernetesResource({
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "HTTPRoute",
            "metadata": {"name": "sas-route", "namespace": route_namespace},
            "spec": {
                "parentRefs": [{
                    "group": "gateway.networking.k8s.io",
                    "kind": "Gateway",
                    "name": "sas-gateway",
                    "namespace": "gateway-system"
                }],
                "hostnames": ["k8s-master-node.test.sas.com"],
                "rules": [{"backendRefs": [backend_ref]}]
            }
        })

    def _gateway_api_listener_set(self, namespace: Text, gateway_namespace: Optional[Text] = "gw-system",
                                  hostname: Optional[Text] = None) -> KubernetesResource:
        if self.ingress_simulator == self.IngressSimulator.GATEWAY_API_LISTENER_SET_HOST_MISMATCH:
            hostname = "unrelated.example.com"
        elif self.ingress_simulator == self.IngressSimulator.GATEWAY_API_LISTENER_SET_WILDCARD_HOST:
            hostname = "*.test.sas.com"
        else:
            hostname = hostname or "k8s-master-node.test.sas.com"
        parent_ref = {"group": "gateway.networking.k8s.io", "kind": "Gateway", "name": "k8s-gw"}
        if gateway_namespace:
            parent_ref["namespace"] = gateway_namespace
        return KubernetesResource({
            "apiVersion": "gateway.networking.k8s.io/v1",
            "kind": "ListenerSet",
            "metadata": {"name": "sas-listenerset", "namespace": namespace},
            "spec": {
                "parentRef": parent_ref,
                "listeners": [{"name": "https", "hostname": hostname,
                               "port": 443, "protocol": "HTTPS"}]
            }
        })

    def get_resource(self, type_version_group: Text, resource_name: Text, raw: bool = False,
                     ignore_errors: bool = False) -> Union[AnyStr, KubernetesResource]:
        # if the resource name is None, raise a CalledProcessError
        if type_version_group is None:
            raise CalledProcessError(1, f"kubectl get {type_version_group} {resource_name} -o json")

        # raise a CalledProcessError if an unexpected namespace is given
        if self.namespace != self.Values.NAMESPACE:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {type_version_group} {resource_name} "
                                     "-o json")

        # throw an error if simulating an empty deployment
        if self.simulate_empty_deployment:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {type_version_group} {resource_name} "
                                     "-o json")

        # handle any ingress simulation - this logic covers scenarios where no resources would be returned
        # Contour
        if type_version_group.lower() == KubernetesResourceTypeValues.CONTOUR_HTTP_PROXIES and \
                self.ingress_simulator != self.IngressSimulator.ALL_CONTOUR_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_CONTOUR:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {type_version_group} {resource_name} "
                                        "-o json")

        # Istio
        elif type_version_group.lower() == KubernetesResourceTypeValues.ISTIO_VIRTUAL_SERVICES and \
                self.ingress_simulator != self.IngressSimulator.ALL_ISTIO_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_ISTIO:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {type_version_group} {resource_name} "
                                        "-o json")

        # NGINX
        elif (type_version_group.lower() == KubernetesResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
              type_version_group.lower() == KubernetesResourceTypeValues.K8S_NETWORKING_INGRESSES) and \
                self.ingress_simulator != self.IngressSimulator.ALL_NGINX_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_NGINX:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {type_version_group} {resource_name} "
                                        "-o json")

        # OpenShift
        elif type_version_group.lower() == KubernetesResourceTypeValues.OPENSHIFT_ROUTES and \
                self.ingress_simulator != self.IngressSimulator.ALL_OPENSHIFT_USED and \
                self.ingress_simulator != self.IngressSimulator.ONLY_OPENSHIFT:
            raise CalledProcessError(1, f"kubectl get -n {self.namespace} {type_version_group} {resource_name} "
                                        "-o json")

        # handle non-namespaced resources
        if not self.include_non_namespaced_resources and (type_version_group.lower() == "nodes" or
                                                          type_version_group.lower() == "namespaces"):
            raise CalledProcessError(1, f"kubectl get {type_version_group} {resource_name} -o json")

        # if the resource should not be represented as unavailable, load it from the file
        raw_resources_dict: Dict = KubectlTest._load_response_data(f"resources_{type_version_group.lower()}.json")

        # iterate to find the requested resource
        for raw_resource in raw_resources_dict:
            resource: KubernetesResource = KubernetesResource(raw_resource)

            if resource.get_name() == resource_name:
                return resource

        # if the resource isn't found by name, raise a CalledProcessError
        raise CalledProcessError(1, f"kubectl get {type_version_group} {resource_name} -o json")

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

    def manage_resource(self, action: Text, file: Text, ignore_errors: bool = False) -> AnyStr:
        # this method is not functional in the testing implementation
        pass

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
