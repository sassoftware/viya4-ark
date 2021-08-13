####################################################################
# ### sas_k8s_objects.py                                         ###
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

from collections.abc import MutableMapping
from typing import Any, AnyStr, Dict, Iterator, List, Optional, Text, Tuple, Union

from viya_ark_library.k8s.k8s_resource_keys import KubernetesResourceKeys

# values used to determine if a resource is a SAS custom resource
_SAS_RESOURCE_KEY_CONTAINS_ = "sas.com"
_SAS_RESOURCE_NAME_PREFIX_ = "sas-"
_SAS_RESOURCE_NAME_CONTAINS_ = "-sas-"


###################################################################################
#                                                                                 #
# Class: KubernetesAvailableResourceTypes                                         #
#                                                                                 #
###################################################################################
class KubernetesAvailableResourceTypes(object):
    """
    Class providing access to values returned from the `kubectl api-resources` command about resource types available
    in the targeted cluster.
    """

    class Keys(object):
        """
        Class defining static references to keys used in the KubernetesAvailableResourceTypes dictionary
        representation.
        """
        GROUP = "group"
        KIND = "kind"
        NAME = "name"
        NAMESPACED = "namespaced"
        SHORT_NAME = "shortname"
        VERBS = "verbs"
        VERSION = "version"

    def __init__(self, api_resources_response_dict: Dict) -> None:
        """
        Constructor for KubernetesAvailableResourceTypes objects.

        :param api_resources_response_dict: The dictionary representing all API resource types.
        """
        self._api_resource_types = api_resources_response_dict

    def _find_resource_type(self, kind: Text, api_version: Optional[Text] = None) \
            -> Tuple[Optional[Text], Optional[Dict], bool]:
        """
        Finds the requested resource type by comparing (case-insensitive) the "kind" value of available resource types
        returned by Kubernetes for the targeted namespace against the value provided via the "kind" parameter. If a
        value is provided via the "api_version" parameter, it is used to avoid ambiguity (i.e., to distinguish between
        resource types with the same "kind" value). If not provided, the first resource type with a matching "kind" is
        returned.

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: A tuple containing [0] - the qualified type value of the available resource type
                 (i.e., <name>.<group>), [1] - a dictionary defining the details of the available resource type, and
                 [2] a bool representing whether a matching resource type was found. If the resource type could not be
                 found, the first two values in the tuple will be None.
        """
        # if the api resources dictionary isn't populated, return values
        # indicating that the resource type couldn't be found
        if not self._api_resource_types:
            return None, None, False

        # default requested group and version values
        requested_group: Optional[Text] = None
        requested_version: Optional[Text] = None

        # only process the apiVersion if the optional parameter was provided
        if api_version:
            if "/" in api_version:
                # if the value contains a "/" then group and version information is provided, separate them
                group_and_version: List[Text] = api_version.rsplit("/", 1)
                requested_group = group_and_version[0]  # group will be the first value in list
                requested_version = group_and_version[1]  # version will be the second value in the list
            else:
                # if the value doesn't contain a "/" then the resource type should be treated as a member of the k8s
                # core api whose group value is omitted, the value represents only version information
                requested_version = api_version

        # iterate over available resources
        for qualified_type, details in self._api_resource_types.items():
            # get the kind value for this resource type
            available_kind: Text = details[self.Keys.KIND]

            # check for matching kind values (case-insensitive)
            if available_kind.lower() != kind.lower():
                # no match, move to the next resource type
                continue

            # compare group values if a group was provided
            if requested_group:
                # get the group value for this resource
                available_group: Text = details[self.Keys.GROUP]

                # check for matching group values (case-insensitive)
                if available_group.lower() != requested_group.lower():
                    # no match, move to the next resource type
                    continue

            # compare version values if a version was provided
            if requested_version:
                # get the version value for this resource
                available_version: Text = details[self.Keys.VERSION]

                # some versions of kubectl don't return the resource type version when requesting api-resources
                # if a version is not defined for this resource type, a version comparison will not be valid
                # if a version is defined for this resource type , check for matching version values (case-insensitive)
                if available_version != "" and available_version.lower() != requested_version.lower():
                    # no match, move to next resource type
                    continue

            # based on the provided values, a matching resource type was found
            return qualified_type, details, True

        # the resource type wasn't found
        return None, None, False

    def is_available(self, kind: Text, api_version: Optional[Text] = None) -> bool:
        """
        Is the requested resource type available in the environment?

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: True if the resource type is available, otherwise False.
        """
        _, _, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        return type_found

    def get_api_group(self, kind: Text, api_version: Optional[Text] = None) -> Optional[AnyStr]:
        """
        Deprecated. Alias to KubernetesAvailableResourceTypes.get_group(), which should be used instead.
        """
        return self.get_group(kind=kind, api_version=api_version)

    def get_group(self, kind: Text, api_version: Optional[Text] = None) -> Optional[AnyStr]:
        """
        Returns the group for the requested resource type.

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: The group of the requested resource type, or None if the requested resource type wasn't found.
        """
        _, type_details, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        if type_found:
            return type_details[self.Keys.GROUP]

        return None

    def get_kind(self, resource_type: Text) -> Optional[Text]:
        """
        Return kind value for the requested resource type.

        :param resource_type: The resource type value of the resource whose kind value will be retrieved.
        :return: The kind value of the requested resource type.
        """
        try:
            return self._api_resource_types[resource_type][KubernetesResourceKeys.KIND]
        except KeyError:
            return None

    def get_name(self, kind: Text, api_version: Optional[Text] = None) -> Optional[AnyStr]:
        """
        Returns the name value of the requested resource type. This value can be used in Kubectl.get_resource[s]()
        requests to get all resources of a given type, regardless of version or group.

        NOTE: This value may lead to ambiguous results if more than one type defines the same name value.
              Use KubernetesAvailableResourceTypes.get_type() to avoid ambiguous results.

        Example::

            kubectl = Kubectl()
            api_resources = kubectl.api_resources()
            deployment_type_name = api_resources.get_name(kind="Deployment", api_version="apps/v1")

            print(deployment_type_name)
            >> deployments

            deployments = kubectl.get_resources(deployment_type_name)

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: The name of the requested resource type, or None if the requested resource type wasn't found.
        """
        _, type_details, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        if type_found:
            return type_details[self.Keys.NAME]

        return None

    def is_namespaced(self, kind: Text, api_version: Optional[Text] = None) -> Optional[bool]:
        """
        Is the requested resource type namespaced?

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: True if the resource type is namespaced, otherwise False; or None if the resource type wasn't found.
        """
        _, type_details, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        if type_found:
            return type_details[self.Keys.NAMESPACED]

        return None

    def get_short_name(self, kind: Text, api_version: Optional[Text] = None) -> Optional[AnyStr]:
        """
        Returns the short name for the requested resource type.

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: The short name of the requested resource type, or None if the resource type wasn't found.
        """
        _, type_details, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        if type_found:
            return type_details[self.Keys.SHORT_NAME]

        return None

    def get_type(self, kind: Text, api_version: Optional[Text] = None) -> Optional[AnyStr]:
        """
        Returns the qualified type value (i.e., <name>.<group>) of the requested resource type. This value can be used
        in Kubectl.get_resource[s]() requests to get all versions of a resource under a specific group. This value
        helps negate the possibility of ambiguous results (i.e., types with the same name value).

        Example::

            kubectl = Kubectl()
            api_resources = kubectl.api_resources()
            deployment_type = api_resources.get_type(kind="Deployment", api_version="apps/v1")

            print(deployment_type)
            >> deployments.apps

            deployments = kubectl.get_resources(deployment_type)


        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: The qualified type value of the requested resource type, or None if the requested resource type wasn't
                 found.
        """
        qualified_type, _, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        if type_found:
            return qualified_type

        return None

    def get_type_fully_qualified(self, kind: Text, api_version: Optional[Text] = None) -> Optional[AnyStr]:
        """
        Returns the fully-qualified type value of the requested resource type. A fully-qualified type consists of the
        resource type name, version, and group formatted like: <name>.<version>.<group>. This value can be used in
        Kubectl.get_resource[s]() requests to get a specific version of the requested resource type under a specific
        group.

        NOTE: All versions of kubectl prior to v1.20.0 do not return version information for api-resources. When using
        a version of kubectl older than the v1.20.0 version, this value will be the same as the value returned by
        KubernetesAvailableResourceTypes.get_type().

        Example::

            kubectl = Kubectl()
            api_resources = kubectl.api_resources()
            fully_qualified_deployment_type = \
                api_resources.get_type_fully_qualified(kind="Deployment, api_version="apps/v1")

            print(fully_qualified_deployment_type)
            >> deployments.v1.apps

            deployments_v1 = kubectl.get_resources(fully_qualified_deployment_type)

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: The fully-qualified type value of the requested resource type, or None if the requested resource type
                 wasn't found.
        """
        qualified_type, type_details, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        if type_found:
            if not type_details[self.Keys.VERSION]:
                # if a version isn't defined, return the qualified type since the values will be the same
                return qualified_type
            elif not type_details[self.Keys.GROUP]:
                # if a group isn't defined, this resource type is in the k8s core api and the qualified type is
                # all that can be used
                return qualified_type
            else:
                # if both a version and group are defined, build the fully-qualified type
                name: Text = type_details[self.Keys.NAME]
                version: Text = type_details[self.Keys.VERSION]
                group: Text = type_details[self.Keys.GROUP]
                return f"{name}.{version}.{group}"

        return None

    def get_verbs(self, kind: Text, api_version: Optional[Text] = None) -> Optional[List[Text]]:
        """
        Returns the list of verbs defined for the requested resource type.

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: The list of verbs defined for the requested resource type, or None if the resource type wasn't found.
        """
        _, type_details, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        if type_found:
            return type_details[self.Keys.VERBS]

        return None

    def get_version(self, kind: Text, api_version: Optional[Text] = None) -> Optional[Text]:
        """
        Returns the version defined for the requested resource type.

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: The version defined for the requested resource type, or None if the resource type wasn't found.
        """
        _, type_details, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        if type_found:
            return type_details[self.Keys.VERSION]

        return None

    def resource_type_as_dict(self, kind: Text, api_version: Optional[Text] = None) -> Optional[Tuple[AnyStr, Dict]]:
        """
        Returns the qualified type value of the requested resource type and the type details in a Python-native
        dictionary representation.

        The returned dictionary is structured like so::

            {
                "group": "",
                "kind": "",
                "name": "",
                "namespaced": bool,
                "shortname": "",
                "verbs": [],
                "version": ""
            }

        :param kind: The kind value of the resource type being requested.
        :param api_version: The "apiVersion" (as defined by Kubernetes: <group>/<version>) of the resource type being
                            requested. If provided, this value is used to avoid ambiguous results (i.e., resource types
                            with the same kind value).
        :return: A tuple containing [0] - the qualified type value of the requested resource type, and [2] - a
        dictionary representation of the requested resource type, or None if the resource wasn't found.
        """
        qualified_type, type_details, type_found = self._find_resource_type(kind=kind, api_version=api_version)

        if type_found:
            return qualified_type, type_details

        return None

    def kind_as_dict(self, kind: Text, api_version: Optional[Text] = None) -> Optional[Tuple[AnyStr, Dict]]:
        """
        Deprecated. Alias to KubernetesAvailableResourceTypes.resource_type_as_dict(), which should be used instead.
        """
        return self.resource_type_as_dict(kind=kind, api_version=api_version)

    def as_dict(self) -> Dict:
        """
        Returns a Python-native dictionary representation of all API resource types returned by kubectl for the
        targeted namespace.

        The returned dictionary is structured like so::

            {
                "<type>": {
                    "group": "",
                    "kind": "",
                    "name": "",
                    "namespaced": bool,
                    "shortname": "",
                    "verbs": [],
                    "version": ""
                },
                ...
            }

        :return: A Python-native dictionary representation of all API resource types returned by kubectl for the
        targeted namespace.
        """
        return self._api_resource_types


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
        if isinstance(o, KubernetesAvailableResourceTypes):
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
        return self._resource.get(KubernetesResourceKeys.API_VERSION)

    def get_kind(self) -> AnyStr:
        """
        Returns the 'kind' value of this Resource.

        :return: This Resource's 'kind' value.
        """
        return self._resource.get(KubernetesResourceKeys.KIND)

    def get_metadata(self) -> Optional[Dict]:
        """
        Returns the 'metadata' dictionary for this Resource.

        :return: This Resource's 'metadata' dictionary.
        """
        return self._resource.get(KubernetesResourceKeys.METADATA)

    def get_metadata_value(self, key: Text) -> Optional[Any]:
        """
        Returns the given key's value from the 'metadata' dictionary.

        :param key: The key of the value to return.
        :return: The value mapped to the given key, or None if the given key doesn't exist.
        """
        try:
            return self._resource[KubernetesResourceKeys.METADATA][key]
        except KeyError:
            return None

    def get_annotations(self) -> Optional[Dict]:
        """
        Returns the dictionary of all annotations defined for this Resource.

        :return: A dictionary of all annotations defined for this Resource.
        """
        return self.get_metadata_value(KubernetesResourceKeys.ANNOTATIONS)

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
        return self.get_annotation(KubernetesResourceKeys.ANNOTATION_COMPONENT_NAME)

    def get_sas_component_version(self) -> Optional[AnyStr]:
        """
        Returns the component version of the KubernetesResource.

        :return: This resource's component version, or None if the 'sas.com/component-version' annotation doesn't
                 exist.
        """
        return self.get_annotation(KubernetesResourceKeys.ANNOTATION_COMPONENT_VERSION)

    def get_sas_version(self) -> Optional[AnyStr]:
        """
        returns the version of the KubernetesResource.

        :return: This resource's version, or None if the 'sas.com/version' annotation doesn't exist.
        """
        return self.get_annotation(KubernetesResourceKeys.ANNOTATION_VERSION)

    def get_creation_timestamp(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.creationTimestamp' value for this Resource.

        :return: This Resource's 'metadata.creationTimestamp' value.
        """
        return self.get_metadata_value(KubernetesResourceKeys.CREATION_TIMESTAMP)

    def get_data(self) -> Optional[Dict]:
        """
        Returns the 'data' dictionary for this Resource.

        :return: This Resource's 'data' dictionary.
        """
        return self._resource.get(KubernetesResourceKeys.DATA)

    def get_generation(self) -> Optional[int]:
        """
        Returns the 'metadata.generation" value for this Resource.

        :return: This Resource's 'metadata.generation' value.
        """
        return self.get_metadata_value(KubernetesResourceKeys.GENERATION)

    def get_labels(self) -> Optional[Dict]:
        """
        Returns the metadata labels for this Resource.

        :return: This resource's metadata labels.
        """
        return self.get_metadata_value(KubernetesResourceKeys.LABELS)

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
        return self.get_metadata_value(KubernetesResourceKeys.NAME)

    def get_namespace(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.namespace" value for this Resource.

        :return: This Resource's 'metadata.namespace' value.
        """
        return self.get_metadata_value(KubernetesResourceKeys.NAMESPACE)

    def get_parameter_value(self, key: Text) -> Optional[Any]:
        """
        Returns the given key's value from the 'parameters' dictionary.

        :param key: The key of the value to return.
        :return: The value mapped to the given key, or None if the given key doesn't exist.
        """
        try:
            return self._resource[KubernetesResourceKeys.PARAMETERS][key]
        except KeyError:
            return None

    def get_provisioner(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.creationTimestamp' value for this Resource.

        :return: This Resource's 'metadata.creationTimestamp' value.
        """
        return self._resource.get(KubernetesResourceKeys.PROVISIONER)

    def get_resource_version(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.resourceVersion" value for this Resource.

        :return: This Resource's 'metadata.resourceVersion' value.
        """
        return self.get_metadata_value(KubernetesResourceKeys.RESOURCE_VERSION)

    def get_self_link(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.selfLink" value for this Resource.

        :return: This Resource's 'metadata.selfLink' value.
        """
        return self.get_metadata_value(KubernetesResourceKeys.SELF_LINK)

    def get_uid(self) -> Optional[AnyStr]:
        """
        Returns the 'metadata.uid" value for this Resource.

        :return: This Resource's 'metadata.uid' value.
        """
        return self.get_metadata_value(KubernetesResourceKeys.UID)

    def get_spec(self) -> Optional[Dict]:
        """
        Returns the 'spec' dictionary for this Resource.

        :return: This Resource's 'spec' dictionary.
        """
        return self._resource.get(KubernetesResourceKeys.SPEC)

    def get_spec_value(self, key: Text) -> Optional[Any]:
        """
        Returns the given key's value from the 'spec' dictionary.

        :param key: The key of the value to return.
        :return: The value mapped to the given key, or None if the given key doesn't exist.
        """
        try:
            return self._resource[KubernetesResourceKeys.SPEC][key]
        except KeyError:
            return None

    def get_status(self) -> Optional[Dict]:
        """
        Returns the 'status' dictionary for this Resource.

        :return: This Resource's 'status' dictionary.
        """
        return self._resource.get(KubernetesResourceKeys.STATUS)

    def get_status_value(self, key: Text) -> Optional[Any]:
        """
        Returns the given key's value from the 'status' dictionary.

        :param key: The key of the value to return.
        :return: The value mapped to the given key, or None if the given key doesn't exist.
        """
        try:
            return self._resource[KubernetesResourceKeys.STATUS][key]
        except KeyError:
            return None

    def as_dict(self) -> Dict:
        """
        Returns this KubernetesResource as a native 'dict' object.

        :return: A native 'dict' version of this Kubernetes resource.
        """
        return self._resource
