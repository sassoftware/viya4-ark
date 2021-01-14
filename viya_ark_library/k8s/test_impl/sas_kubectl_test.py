####################################################################
# ### sas_kubectl_test.py                                        ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
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

_API_RESOURCES_BOTH_INGRESS_DATA_ = "api_resources_both_ingress.json"
_API_RESOURCES_ISTIO_ONLY_DATA_ = "api_resources_istio_only.json"
_API_RESOURCES_NGINX_ONLY_DATA_ = "api_resources_nginx_only.json"
_API_RESOURCES_NO_INGRESS_DATA_ = "api_resources_no_ingress.json"
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
        # Neither VirtualService nor Ingress will be included in the resources returned by api_resources() #
        NONE = 1

        # VirtualService will be omitted from the resources returned by api_resources() #
        NGINX_ONLY = 2

        # Ingress will be omitted from the resources returned by api_resources() #
        ISTIO_ONLY = 3

        # Both VirtualService and Ingress will be included in the resources returned by api_resources() but only #
        # Ingress objects will be defined #
        BOTH_RESOURCES_NGINX_USED = 4

        # Both VirtualService and Ingress will be included in the resources returned by api_resources() but only #
        # VirtualService objects will be defined #
        BOTH_RESOURCES_ISTIO_USED = 5

        # Both VirtualService and Ingress will be included in the resources returned by api_resources() and both #
        # will be defined and available #
        BOTH = 6

    ################################################################
    # ### CLASS: KubectlTest.Values
    ################################################################
    class Values(object):
        """
        Class providing static references to values returned by the KubectlTest implementation.
        """
        NAMESPACE: Text = "test"

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

        # Component: sas-annotations
        COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME: Text = "sas-annotations"
        COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME: Text = "sas-annotations"
        COMPONENT_SAS_ANNOTATIONS_POD_NAME: Text = "sas-annotations-58db55fd65-l2jrw"
        COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME: Text = "sas-annotations-58db55fd65"
        COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME: Text = "sas-annotations"
        COMPONENT_SAS_ANNOTATIONS_VIRTUAL_SERVICE_NAME: Text = "sas-annotations"

        COMPONENT_SAS_ANNOTATIONS_NAME: Text = "sas-annotations"
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT: Dict[Text, List[Text]] = {
            KubernetesResource.Kinds.DEPLOYMENT: [COMPONENT_SAS_ANNOTATIONS_DEPLOYMENT_NAME],
            KubernetesResource.Kinds.INGRESS: [COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME],
            KubernetesResource.Kinds.POD: [COMPONENT_SAS_ANNOTATIONS_POD_NAME],
            KubernetesResource.Kinds.REPLICA_SET: [COMPONENT_SAS_ANNOTATIONS_REPLICA_SET_NAME],
            KubernetesResource.Kinds.SERVICE: [COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME],
            KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE: [COMPONENT_SAS_ANNOTATIONS_VIRTUAL_SERVICE_NAME]
        }
        COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT: int = len(COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT)

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

        # Resource: all kinds
        RESOURCE_KINDS_LIST: List[Text] = [
            KubernetesResource.Kinds.CAS_DEPLOYMENT,
            KubernetesResource.Kinds.CONFIGMAP,
            KubernetesResource.Kinds.CRON_JOB,
            KubernetesResource.Kinds.DEPLOYMENT,
            KubernetesResource.Kinds.INGRESS,
            KubernetesResource.Kinds.JOB,
            KubernetesResource.Kinds.NODE,
            KubernetesResource.Kinds.POD,
            KubernetesResource.Kinds.REPLICA_SET,
            KubernetesResource.Kinds.SERVICE,
            KubernetesResource.Kinds.STATEFUL_SET,
            KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE
        ]
        RESOURCE_KINDS_COUNT: int = len(RESOURCE_KINDS_LIST)

        # Resource: CASDeployment
        RESOURCE_CAS_DEPLOYMENT_LIST: List[Text] = [
            COMPONENT_SAS_CAS_SERVER_CAS_DEPLOYMENT_NAME
        ]
        RESOURCE_CAS_DEPLOYMENT_COUNT: int = len(RESOURCE_CAS_DEPLOYMENT_LIST)

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
            COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME
        ]
        RESOURCE_INGRESS_COUNT: int = len(RESOURCE_INGRESS_LIST)

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

        # Resource: VirtualService
        RESOURCE_VIRTUAL_SERVICE_LIST: List[Text] = [
            COMPONENT_SAS_ANNOTATIONS_VIRTUAL_SERVICE_NAME
        ]
        RESOURCE_VIRTUAL_SERVICE_COUNT: int = len(RESOURCE_VIRTUAL_SERVICE_LIST)

    ################################################################
    # ### KubectlTest functions
    ################################################################

    def __init__(self,
                 ingress_simulator: IngressSimulator = IngressSimulator.NGINX_ONLY,
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

    def do(self, command: Text, ignore_errors: bool = False) -> AnyStr:
        return "Not functional in testing implementation"

    def api_resources(self, ignore_errors: bool = False) -> KubernetesApiResources:
        # check for ingress simulation to determine which API resources should be returned
        if self.ingress_simulator == self.IngressSimulator.NONE:
            api_resources_data: Dict = KubectlTest._load_response_data(_API_RESOURCES_NO_INGRESS_DATA_)
        elif self.ingress_simulator == self.IngressSimulator.NGINX_ONLY:
            api_resources_data: Dict = KubectlTest._load_response_data(_API_RESOURCES_NGINX_ONLY_DATA_)
        elif self.ingress_simulator == self.IngressSimulator.ISTIO_ONLY:
            api_resources_data: Dict = KubectlTest._load_response_data(_API_RESOURCES_ISTIO_ONLY_DATA_)
        else:
            api_resources_data: Dict = KubectlTest._load_response_data(_API_RESOURCES_BOTH_INGRESS_DATA_)

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

        # handle any ingress simulation
        # in the scenarios below, the resources would be defined but there wouldn't be any existing objects
        # so empty lists would be returned
        if (self.ingress_simulator == self.IngressSimulator.BOTH_RESOURCES_NGINX_USED and k8s_api_resource.lower() ==
            "virtualservices") or \
            (self.ingress_simulator == self.IngressSimulator.BOTH_RESOURCES_ISTIO_USED and k8s_api_resource.lower() ==
             "ingresses"):
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

        # handle any ingress simulation
        # in the scenarios below, the kinds would be defined but no objects of that kind would be created, so trying
        # to get one by name would raise a CalledProcessError
        if (self.ingress_simulator == self.IngressSimulator.BOTH_RESOURCES_NGINX_USED and k8s_api_resource.lower() ==
            "virtualservices") or \
            (self.ingress_simulator == self.IngressSimulator.BOTH_RESOURCES_ISTIO_USED and k8s_api_resource.lower() ==
             "ingresses"):
            raise CalledProcessError(1, f"kubectl get {k8s_api_resource.lower()} {resource_name} -o json")

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

    def logs(self, pod_name: Text, all_containers: bool = True, prefix: bool = True, tail: int = 10,
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
