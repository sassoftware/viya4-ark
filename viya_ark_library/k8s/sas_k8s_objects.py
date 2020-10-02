####################################################################
# ### sas_k8s_objects.py                                         ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from collections.abc import MutableMapping
import json
from typing import Any, AnyStr, Dict, Iterator, List, Optional, Text, Union

# name prefix for Resources deployed by SAS #
_SAS_RESOURCE_KEY_CONTAINS_ = "sas.com"
_SAS_RESOURCE_NAME_PREFIX_ = "sas-"
_SAS_RESOURCE_NAME_CONTAINS_ = "-sas-"


###################################################################################
#                                                                                 #
# Class: KubernetesApiResources                                                   #
#                                                                                 #
###################################################################################
class KubernetesApiResources(object):
    """
    Class representing the response returned from the `kubectl api-resources` command.
    """

    class Keys(object):
        """
        Class defining static references to key value used in the KubernetesApiResources dictionary representation.
        """
        API_GROUP = "apiGroup"
        NAME = "name"
        NAMESPACED = "namespaced"
        SHORT_NAME = "shortname"
        VERBS = "verbs"

    def __init__(self, api_resources_dict: Dict) -> None:
        """
        Constructor for KubernetesApiResources objects.

        :param api_resources_dict: The dictionary representing all API resources.
        """
        self._api_resources = api_resources_dict

    def is_available(self, kind: Text) -> bool:
        """
        Is the given kind available in the environment?

        :param kind: The kind whose availability should be checked.
        :return: True if the kind is available, otherwise False.
        """
        return kind in self._api_resources

    def get_api_group(self, kind: Text) -> Optional[AnyStr]:
        """
        Returns the API group for the given kind.

        :param kind: The kind whose API group value will be retrieved.
        :return: The API group of the given kind, or None if the given kind does not exist.
        """
        try:
            return self._api_resources[kind][self.Keys.API_GROUP]
        except KeyError:
            return None

    def get_name(self, kind: Text) -> Optional[AnyStr]:
        """
        Returns the API name for the given kind. This value can be used in "get" requests via Kubectl.

        Example::

            kubectl = Kubectl()
            api_resources = kubectl.get_api_resources()
            deployments = kubectl.get_resources(api_resources.get_name(<kind>))

        :param kind: The kind whose name value will be retrieved.
        :return: The API name of the given kind, or None if the given kind does not exist.
        """
        try:
            return self._api_resources[kind][self.Keys.NAME]
        except KeyError:
            return None

    def is_namespaced(self, kind: Text) -> Optional[bool]:
        """
        Is the given kind namespaced?

        :param kind: The kind whose namspaced designation will be returned.
        :return: True if the kind is namespaced, otherwise False or None if the kind does not exist.
        """
        try:
            return self._api_resources[kind][self.Keys.NAMESPACED]
        except KeyError:
            return None

    def get_short_name(self, kind: Text) -> Optional[AnyStr]:
        """
        Returns the short API name for the given kind.

        :param kind: The kind whose short name value will be retrieved.
        :return: The API short name of the given kind, or None if the kind does not exist.
        """
        try:
            return self._api_resources[kind][self.Keys.SHORT_NAME]
        except KeyError:
            return None

    def get_verbs(self, kind: Text) -> Optional[List]:
        """
        Returns the list of verbs defined for the given kind.

        :param kind: The kind whose verbs list will be returned.
        :return: The list of verbs defined for the given kind, or None if the kind does not exist.
        """
        try:
            return self._api_resources[kind][self.Keys.VERBS]
        except KeyError:
            return None

    def kind_as_dict(self, kind: Text) -> Optional[Dict]:
        """
        Returns the given kind in a Python-native dictionary representation.

        The returned dictionary is structured like so::

            {
                "name": "",
                "shortname": "",
                "apiGroup": "",
                "namespaced": bool,
                "verbs": []
            }

        :param kind: The kind to return in a Python-native dictionary representation.
        :return: A dictionary representation of the requested kind, or None if the kind does not exist
        """
        return self._api_resources.get(kind)

    def as_dict(self) -> Dict:
        """
        Returns a dictionary representation of the API resources.

        The returned dictionary is structured like so::

            {
                "<resource_kind>": {
                    "name": "",
                    "shortname": "",
                    "apiGroup": "",
                    "namespaced": bool,
                    "verbs": []
                },
                ...
            }

        :return: A dictionary representation of this object.
        """
        return self._api_resources


###################################################################################
#                                                                                 #
# Class: KubernetesObjectJSONEncoder                                              #
#                                                                                 #
###################################################################################
class KubernetesObjectJSONEncoder(json.JSONEncoder):
    """
    Custom JSONEncoder implementation used to handle the JSON serialization of SAS Kubernetes objects.
    """

    def default(self, o: object) -> Dict:
        """
        Handles converting Kubectl response objects to their correct Python-native dictionary representation.

        :param o: The object to to JSON encode.
        :return: The dictionary representation of Kubectl response objects, or the same dict, if the object is
                 already a Python-native dictionary.
        """
        if isinstance(o, KubernetesResource):
            return o.as_dict()
        if isinstance(o, KubernetesApiResources):
            return o.as_dict()
        if isinstance(o, KubernetesMetrics):
            return o.as_dict()
        else:
            return o.__dict__


###################################################################################
#                                                                                 #
# Class: KubernetesMetrics                                                        #
#                                                                                 #
###################################################################################
class KubernetesMetrics(object):
    """
    Class representing the response from `kubectl top <nodes/pods>` commands.
    """

    class Keys(object):
        """
        Class defining static references used in the dictionary representation of this object.
        """
        CPU_CORES = "cpuCores"
        CPU_USED = "cpuUsed"
        MEMORY_BYTES = "memoryBytes"
        MEMORY_USED = "memoryUsed"

    def __init__(self, metrics_dict: Dict) -> None:
        """
        Constructor for Metrics objects.

        :param metrics_dict: Dictionary defining the metrics for the requested resource.
        """
        self._metrics = metrics_dict

    def get_cpu_cores(self, name: Text) -> Optional[AnyStr]:
        """
        Returns the CPU used in cores for the given resource.

        :param name: The name of the pod/node.
        :return: CPU used in cores for the given pod/node, or None if the given node/pod isn't defined.
        """
        try:
            return self._metrics[name][self.Keys.CPU_CORES]
        except KeyError:
            return None

    def get_cpu_used(self, name: Text) -> Optional[AnyStr]:
        """
        Returns the CPU percentage used for the given node.

        **NOTE**: Will always return None for pods.

        :param name: The name of the resource.
        :return: The CPU percentage used for nodes, None for pods or if given Node isn't defined.
        """
        try:
            return self._metrics[name][self.Keys.CPU_USED]
        except KeyError:
            return None

    def get_memory_bytes(self, name: Text) -> Optional[AnyStr]:
        """
        Returns the memory used in bytes for the given pod/node.

        :param name: The name of the pod/node.
        :return: The memory used in bytes for the given pod/node, or None if the given node/pod isn't defined.
        """
        try:
            return self._metrics[name][self.Keys.MEMORY_BYTES]
        except KeyError:
            return None

    def get_memory_used(self, name: Text) -> Optional[AnyStr]:
        """
        Returns the memory percentage used for the given node.

        **NOTE**: Will always return None for pods.

        :param name: The name of the resource.
        :return: The memory percentage used for nodes, None for pods or if the given Node isn't defined.
        """
        try:
            return self._metrics[name][self.Keys.MEMORY_USED]
        except KeyError:
            return None

    def resource_metrics_as_dict(self, name: Text) -> Optional[Dict]:
        """
        Returns a dictionary representation of the metrics defined for the given resource.

        The returned dictionary is structured like so::

            {
                "cpuCores": "",
                "cpuUsed": "",
                "memoryBytes": "",
                "memoryUsed": ""
            }

        :param name: The name of the resource whose metrics will be retrieved.
        :return: A dictionary of the metrics for the given resource, or None if the given resource isn't defined.
        """
        try:
            return self._metrics[name]
        except KeyError:
            return None

    def as_dict(self) -> Dict:
        """
        Returns a dictionary representation of this object.

        The returned dictionary is structured like so::

            {
                "<node_name">: {
                    "cpuCores": "",
                    "cpuUsed": "",
                    "memoryBytes": "",
                    "memoryUsed": ""
                },
                ...
            }

        :return: A dictionary representation of this object.
        """
        return self._metrics


###################################################################################
#                                                                                 #
# Class: KubernetesResource                                                       #
#                                                                                 #
###################################################################################
class KubernetesResource(MutableMapping):
    """
    A MutableMapping implementation that holds the data defining a Kubernetes resource and provides
    methods for retrieving values.
    """

    class Keys(object):
        """
        Class providing static access to commonly used key names in Resource objects (list is not all-inclusive).
        """
        ADDRESSES = "addresses"
        ANNOTATIONS = "annotations"
        ANNOTATION_PROXY_BODY_SIZE = "nginx.ingress.kubernetes.io/proxy-body-size"
        ANNOTATION_COMPONENT_NAME = "sas.com/component-name"
        ANNOTATION_COMPONENT_VERSION = "sas.com/component-version"
        ANNOTATION_VERSION = "sas.com/version"
        API_VERSION = "apiVersion"
        ARCHITECTURE = "architecture"
        AVAILABLE_REPLICAS = "availableReplicas"
        BACKEND = "backend"
        CAPACITY = "capacity"
        CLUSTER_IP = "clusterIP"
        COLLISION_COUNT = "collisionCount"
        COMPLETION_TIME = "completionTime"
        CONTAINER_RUNTIME_VERSION = "containerRuntimeVersion"
        CONTAINER_STATUSES = "containerStatuses"
        CONTAINERS = "containers"
        CONTROLLER_TEMPLATE = "controllerTemplate"
        CREATION_TIMESTAMP = "creationTimestamp"
        CURRENT_REPLICAS = "currentReplicas"
        DESTINATION = "destination"
        ENV = "env"
        EXACT = "exact"
        FULLY_LABELED_REPLICAS = "fullyLabeledReplicas"
        GATEWAYS = "gateways"
        GENERATION = "generation"
        HTTP = "http"
        HOST = "host"
        HOSTS = "hosts"
        HOST_IP = "hostIP"
        IMAGE = "image"
        IMAGES = "images"
        INIT_CONTAINERS = "initContainers"
        ITEMS = "items"
        KERNEL_VERSION = "kernelVersion"
        KIND = "kind"
        KUBE_PROXY_VERSION = "kubeProxyVersion"
        KUBELET_VERSION = "kubeletVersion"
        LABEL_CAS_NODE_TYPE = "cas-node-type"
        LABEL_CAS_SERVER = "cas-server"
        LABEL_MANAGED_BY = "app.kubernetes.io/managed-by"
        LABEL_PG_CLUSTER = "pg-cluster"
        LABEL_PG_DEPLOYMENT_NAME = "deployment-name"
        LABEL_PG_SERVICE_NAME = "service-name"
        LABEL_SAS_DEPLOYMENT = "sas.com/deployment"
        LABELS = "labels"
        MATCH = "match"
        MATCH_LABELS = "matchLabels"
        METADATA = "metadata"
        NAME = "name"
        NAMESPACE = "namespace"
        NODE_INFO = "nodeInfo"
        NODE_NAME = "nodeName"
        OBSERVED_GENERATION = "observedGeneration"
        OPERATING_SYSTEM = "operatingSystem"
        OS_IMAGE = "osImage"
        OWNER_REFERENCES = "ownerReferences"
        PARAMETERS = "parameters"
        PATH = "path"
        PATHS = "paths"
        PHASE = "phase"
        POD_CIDR = "podCIDR"
        POD_CIDRS = "podCIDRs"
        POD_IP = "podIP"
        POD_IPS = "podIPs"
        PORT = "port"
        PORTS = "ports"
        PROTOCOL = "protocol"
        PROVISIONER = "provisioner"
        PUBLISH_NODE_PORT_SERVICE = "publishNodePortService"
        READY = "ready"
        READY_REPLICAS = "readyReplicas"
        REPLICAS = "replicas"
        RESOURCES = "resources"
        RESOURCE_VERSION = "resourceVersion"
        RESTART_COUNT = "restartCount"
        ROUTE = "route"
        RULES = "rules"
        SELECTOR = "selector"
        SELF_LINK = "selfLink"
        SERVICE_PORT = "servicePort"
        SERVICE_NAME = "serviceName"
        SPEC = "spec"
        START_TIME = "startTime"
        STARTED = "started"
        STATE = "state"
        STATUS = "status"
        SUCCEEDED = "succeeded"
        TARGET_PORT = "targetPort"
        TCP = "tcp"
        TEMPLATE = "template"
        UID = "uid"
        URI = "uri"
        UPDATED_REPLICAS = "updatedReplicas"
        UNAVAILABLE_REPLICAS = "unavailableReplicas"
        WORKER_TEMPLATE = "workerTemplate"
        WORKERS = "workers"

    class Kinds(object):
        """
        Class defining commonly used Kubernetes kind names for SAS deployments (list is not all-inclusive).

        All available kinds can be discovered by calling the Kubectl.get_api_resources() method.
        """
        CAS_DEPLOYMENT = "CASDeployment"
        CRON_JOB = "CronJob"
        CRUNCHY_PG_BACKUP = "Pgbackup"
        CRUNCHY_PG_CLUSTER = "Pgcluster"
        CRUNCHY_PG_POLICY = "Pgpolicy"
        CRUNCHY_PG_REPLICA = "Pgreplica"
        CRUNCHY_PG_TASK = "Pgtask"
        DEPLOYMENT = "Deployment"
        ENDPOINT = "Endpoint"
        INGRESS = "Ingress"
        ISTIO_VIRTUAL_SERVICE = "VirtualService"
        JOB = "Job"
        NODE = "Node"
        NODE_METRICS = "NodeMetrics"
        POD = "Pod"
        POD_METRICS = "PodMetrics"
        REPLICA_SET = "ReplicaSet"
        SERVICE = "Service"
        STATEFUL_SET = "StatefulSet"
        STORAGECLASS = "sc"

    def __init__(self, resource: Union[Dict, AnyStr]) -> None:
        """
        Constructor for Resource class.

        :param resource: A dict, bytes, or str object representing the Kubernetes resource. An AttributeError
                         is raised if the provided resource is not an instance of dict, bytes, or str.
        """
        self._resource: Dict = dict()
        if isinstance(resource, dict):
            self._resource = resource
        elif isinstance(resource, bytes):
            self._resource = json.loads(resource.decode())
        elif isinstance(resource, str):
            self._resource = json.loads(resource)
        else:
            raise AttributeError(f"{self.__class__.__name__}.'resource' must by of type [dict, bytes, str].")

    def __getitem__(self, key) -> Any:
        """
        Implemented method for retrieving an item from the Resource data structure.

        :param key: The key of the item to retrieve.
        :return: The value mapped to the provided key.
        """
        return self._resource[key]

    def __setitem__(self, key, value: Any) -> None:
        """
        Implemented method for setting a new key/value pair in the Resource data structure.

        :param key: The new key to add to the data structure.
        :param value: The value mapped to the given key.
        """
        self._resource[key] = value

    def __delitem__(self, key) -> None:
        """
        Implemented method for removing a key and value from the Resource data structure.

        :param key: The key to remove from the data structure.
        """
        del self._resource[key]

    def __iter__(self) -> Iterator[Dict]:
        """
        Implemented method for returning an iterator for the Resource data structure.

        :return: The iterator for this data structure.
        """
        return iter(self._resource)

    def __len__(self) -> int:
        """
        Implemented method for returning the length of the Resource data structure.

        :return: The length of the data structure.
        """
        return len(self._resource)

    def is_sas_resource(self) -> bool:
        """
        Does this Resource belong to a SAS component?

        :return: True if the Resource is determined to belong to SAS, otherwise False.
        """
        # if the name is not defined, return False
        if self.get_name() is None:
            return False

        # if this resource has any annotation with a key that contains "sas.com", treat it as a SAS resource
        if self.get_annotations() is not None:
            for annotation_key in self.get_annotations().keys():
                if _SAS_RESOURCE_KEY_CONTAINS_ in annotation_key:
                    return True

        # if this resource has any label with a key that contains "sas.com", treat it as a SAS resource
        if self.get_labels() is not None:
            for label_key in self.get_labels().keys():
                if _SAS_RESOURCE_KEY_CONTAINS_ in label_key:
                    return True

        # if the resource name starts with 'sas-' or contains '-sas-', treat it as a SAS resource
        if self.get_name().startswith(_SAS_RESOURCE_NAME_PREFIX_) or _SAS_RESOURCE_NAME_CONTAINS_ in self.get_name():
            return True

        # if nothing returned True above, treat this as a non-SAS resource
        return False

    def get_api_version(self) -> AnyStr:
        """
        Returns the 'apiVersion' value of this Resource.

        :return: This Resource's 'apiVersion' value.
        """
        return self._resource.get(self.Keys.API_VERSION)

    def get_kind(self) -> AnyStr:
        """
        Returns the 'kind' value of this Resource.

        :return: This Resource's 'kind' value.
        """
        return self._resource.get(self.Keys.KIND)

    def get_metadata(self) -> Optional[Dict]:
        """
        Returns the 'metadata' dictionary for this Resource.

        :return: This Resource's 'metadata' dictionary.
        """
        return self._resource.get(self.Keys.METADATA)

    def get_metadata_value(self, key: Text) -> Optional[Any]:
        """
        Returns the given key's value from the 'metadata' dictionary.

        :param key: The key of the value to return.
        :return: The value mapped to the given key, or None if the given key doesn't exist.
        """
        try:
            return self._resource[self.Keys.METADATA][key]
        except KeyError:
            return None

    def get_annotations(self) -> Optional[Dict]:
        """
        Returns the dictionary of all annotations defined for this Resource.

        :return: A dictionary of all annotations defined for this Resource.
        """
        return self.get_metadata_value(self.Keys.ANNOTATIONS)

    def get_annotation(self, annotation: Text) -> Optional[Any]:
        """
        Returns the value of the given annotation.

        :param annotation: The key of the annotation to retrieve.
        :return: The value mapped to the given annotation, or None if the given annotation doesn't exist.
        """
        annotations: Dict = self.get_annotations()
        if annotations is None:
            return None
        return annotations.get(annotation)

    def get_sas_component_name(self) -> Optional[AnyStr]:
        """
        Returns the component name of the KubernetesResource.

        :return: This resource's component name, or None if the 'sas.com/component-name' annotation doesn't exist.
        """
        return self.get_annotation(self.Keys.ANNOTATION_COMPONENT_NAME)

    def get_sas_component_version(self) -> Optional[AnyStr]:
        """
        Returns the component version of the KubernetesResource.

        :return: This resource's component version, or None if the 'sas.com/component-version' annotation doesn't
                 exist.
        """
        return self.get_annotation(self.Keys.ANNOTATION_COMPONENT_VERSION)

    def get_sas_version(self) -> Optional[AnyStr]:
        """
        returns the version of the KubernetesResource.

        :return: This resource's version, or None if the 'sas.com/version' annotation doesn't exist.
        """
        return self.get_annotation(self.Keys.ANNOTATION_VERSION)

    def get_creation_timestamp(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.creationTimestamp' value for this Resource.

        :return: This Resource's 'metadata.creationTimestamp' value.
        """
        return self.get_metadata_value(self.Keys.CREATION_TIMESTAMP)

    def get_generation(self) -> Optional[int]:
        """
        Returns the 'metadata.generation" value for this Resource.

        :return: This Resource's 'metadata.generation' value.
        """
        return self.get_metadata_value(self.Keys.GENERATION)

    def get_labels(self) -> Optional[Dict]:
        """
        Returns the metadata labels for this Resource.

        :return: This resource's metadata labels.
        """
        return self.get_metadata_value(self.Keys.LABELS)

    def get_label(self, label_key: Text) -> Optional[Any]:
        """
        Returns the value of the given metadata label key.

        :param label_key: The key of the metadata label to retrieve.
        :return: The value of the the given key, or None if the given key does not exist.
        """
        try:
            if self.get_labels() is None:
                return None
            return self.get_labels()[label_key]
        except KeyError:
            return None

    def get_name(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.name" value for this Resource.

        :return: This Resource's 'metadata.name' value.
        """
        return self.get_metadata_value(self.Keys.NAME)

    def get_namespace(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.namespace" value for this Resource.

        :return: This Resource's 'metadata.namespace' value.
        """
        return self.get_metadata_value(self.Keys.NAMESPACE)

    def get_resource_version(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.resourceVersion" value for this Resource.

        :return: This Resource's 'metadata.resourceVersion' value.
        """
        return self.get_metadata_value(self.Keys.RESOURCE_VERSION)

    def get_self_link(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.selfLink" value for this Resource.

        :return: This Resource's 'metadata.selfLink' value.
        """
        return self.get_metadata_value(self.Keys.SELF_LINK)

    def get_uid(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.uid" value for this Resource.

        :return: This Resource's 'metadata.uid' value.
        """
        return self.get_metadata_value(self.Keys.UID)

    def get_spec(self) -> Optional[Dict]:
        """
        Returns the 'spec' dictionary for this Resource.

        :return: This Resource's 'spec' dictionary.
        """
        return self._resource.get(self.Keys.SPEC)

    def get_spec_value(self, key: Text) -> Optional[Any]:
        """
        Returns the given key's value from the 'spec' dictionary.

        :param key: The key of the value to return.
        :return: The value mapped to the given key, or None if the given key doesn't exist.
        """
        try:
            return self._resource[self.Keys.SPEC][key]
        except KeyError:
            return None

    def get_status(self) -> Optional[Dict]:
        """
        Returns the 'status' dictionary for this Resource.

        :return: This Resource's 'status' dictionary.
        """
        return self._resource.get(self.Keys.STATUS)

    def get_status_value(self, key: Text) -> Optional[Any]:
        """
        Returns the given key's value from the 'status' dictionary.

        :param key: The key of the value to return.
        :return: The value mapped to the given key, or None if the given key doesn't exist.
        """
        try:
            return self._resource[self.Keys.STATUS][key]
        except KeyError:
            return None

    def as_dict(self) -> Dict:
        """
        Returns this KubernetesResource as a native 'dict' object.

        :return: A native 'dict' version of this Kubernetes resource.
        """
        return self._resource

    def get_parameter_value(self, key: Text) -> Optional[Any]:
        """
        Returns the given key's value from the 'parameters' dictionary.

        :param key: The key of the value to return.
        :return: The value mapped to the given key, or None if the given key doesn't exist.
        """
        try:
            return self._resource[self.Keys.PARAMETERS][key]
        except KeyError:
            return None

    def get_provisioner(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.creationTimestamp' value for this Resource.

        :return: This Resource's 'metadata.creationTimestamp' value.
        """
        return self._resource.get(self.Keys.PROVISIONER)