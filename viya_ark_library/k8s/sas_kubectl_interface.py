####################################################################
# ### sas_kubectl_interface.py                                   ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from abc import ABC, abstractmethod
from typing import AnyStr, Dict, List, Text, Union, Optional

from viya_ark_library.k8s.sas_k8s_objects import KubernetesAvailableResourceTypes, \
    KubernetesMetrics, \
    KubernetesResource


class KubectlInterface(ABC):
    """
    Abstract Base Class for creating a functional Python-native interface for the kubectl command-line utility.
    """

    @abstractmethod
    def get_namespace(self) -> Text:
        """
        Returns the namespace value determined during initialization.

        :return: The namespace value determined during object initialization.
        """
        pass

    @abstractmethod
    def do(self, command: Text, ignore_errors: bool = False, success_rcs: Optional[List[int]] = None) -> AnyStr:
        """
        Generic method for executing a kubectl command.

        :param command: The kubectl command to execute.
        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :param success_rcs: A list of return codes representing a successful execution of the command. If a None value
                            is provided, the default list "[0]" will be used.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: The stdout of the command that was executed.
        """
        pass

    @abstractmethod
    def api_resources(self, ignore_errors: bool = False) -> KubernetesAvailableResourceTypes:
        """
        Returns a KubernetesAvailableResourceTypes object defining all Kubernetes API resource types available in the
        targeted cluster. The values returned by Kubernetes on the initial call are cached and returned on any
        subsequent calls. This is because available resource types are not likely to change after the software is
        deployed. Other resources reported by kubectl may contain status or may in someway change during their life
        cycle, making caching disadvantageous. To clear the cached available resource types, use
        Kubectl.clear_api_resources_cache().

        Corresponding CLI command::

            $ kubectl api-resources -o wide

        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: A KubernetesAvailableResourceTypes object.
        """
        pass

    @abstractmethod
    def api_versions(self, ignore_errors: bool = False) -> List:
        """
        Returns a list of all Kubernetes API versions available in the targeted cluster. The values returned by
        Kubernetes on the initial call are cached and returned on any subsequent calls. This is because resource
        versions are not likely to change after the software is deployed. Other resources reported by kubectl may
        contain status or may in someway change during their life cycle, making caching disadvantageous. To clear the
        cached resource versions, use Kubectl.clear_api_versions_cache().

        Corresponding CLI command::

            $ kubectl api-versions

        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: A list of all available Kubernetes API versions.
        """
        pass

    @abstractmethod
    def can_i(self, action: Text, all_namespaces: bool = False, ignore_errors: bool = False) -> bool:
        """
        Determines if the currently configured user for kubectl has the ability to run the requested action. If so,
        True is returned, otherwise False.

        Corresponding CLI command::

            $ kubectl auth can-i <action> [--all-namespaces]

        :param action: The action for which permissions will be checked.
        :param all_namespaces: True if the specified action should be checked in all namespaces, otherwise False.
        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: True if the action can be performed, otherwise False.
        """
        pass

    @abstractmethod
    def config_view(self, ignore_errors: bool = False) -> Dict:
        """
        Returns the current kubectl Config resource as a Python-native dictionary.

        Corresponding CLI command::

            $ kubectl config view -o json

        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :return: A dictionary representing the kubectl Config resource.
        """
        pass

    @abstractmethod
    def cluster_info(self) -> Optional[AnyStr]:
        """
        Returns information about the cluster being targeted by kubectl.

        Corresponding CLI command::

            $ kubectl cluster-info

        :return: The cluster information returned for the targeted cluster as a string.
        """

    @abstractmethod
    def get_resources(self, type_version_group: Text, raw: bool = False) -> Union[Dict, List[KubernetesResource]]:
        """
        Issues a kubectl command to retrieve a list of Kubernetes resources.

        Corresponding CLI command::

            $ kubectl get <type_version_group> -o json

        :param type_version_group: The type name, version, and/or group of the resources to retrieve. Values accepted
                                   by kubectl are formatted like: name[.version][.group]. The name value is
                                   required and can be the plural or singular name of the resource type. The version
                                   and group values are optional, but must be specified in the order mentioned above.
                                   As a best practice, a qualified type value (formatted like: name.group) should
                                   be used so that the returned values don't include ambiguous results
                                   (i.e., results that have the same type name, but are defined under different API
                                   groups).
        :param raw: Return the response from kubectl as a Python-native dictionary, not a list of KubernetesResource
                    objects.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: If raw=True, the response from kubectl as a Python-native dictionary, otherwise a list (potentially
                 an empty list) of KubernetesResource objects for the requested Kubernetes resource type;
                 or None if the resource type was not accessible.
        """
        pass

    @abstractmethod
    def get_resource(self, type_version_group: Text, resource_name: Text, raw: bool = False,
                     ignore_errors: bool = False) -> Union[AnyStr, KubernetesResource]:
        """
        Issues a kubectl command to retrieve the definition of the requested Kubernetes resource, by name.

        Corresponding CLI command::

            $ kubectl get <type_version_group> <resource_name> -o json

        :param type_version_group: The type name, version, and/or group of the resources to retrieve. Values accepted
                                   by kubectl are formatted like: name[.version][.group]. The name value is
                                   required and can be the plural or singular name of the resource type. The version
                                   and group values are optional, but must be specified in the order mentioned above.
                                   As a best practice, a qualified type value (formatted like: name.group) should
                                   be used so that the returned values don't include ambiguous results
                                   (i.e., results that have the same type name, but are defined under different API
                                   groups).
        :param resource_name: The name of the resource to retrieve.
        :param raw: Return the raw response from kubectl as a string, not as a KubernetesResource object.
        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: If raw=True, the raw response from kubectl as a string, otherwise a KubernetesResource object
                 representing the requested resource.
        """
        pass

    @abstractmethod
    def logs(self, pod_name: Text, container_name: Optional[Text] = None, prefix: bool = True, tail: int = 10,
             ignore_errors: bool = False) -> List:
        """
        Retrieves logs from the pod with the given name.

        Corresponding CLI command::

            $ kubectl logs <pod_name> [<container_name>|--all-containers] [--prefix] --tail=<tail>

        :param pod_name: The name of the Pod whose logs should be retrieved.
        :param container_name: The name of the specific container whose log should be retrieved. If no container is
                               specified, the --all-containers option is used.
        :param prefix: True if the log lines should be prefixed with the container's name, otherwise False.
        :param tail: (default: 10) Limits the results to the given number of lines. Setting this to '-1' will return the
                     complete log.
        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: A list of the requested lines from the given Pod/Container logs.
        """
        pass

    @abstractmethod
    def manage_resource(self, action: Text, file: Text, ignore_errors: bool = False, ) -> AnyStr:
        """
        Manages (applies or deletes) a Kubernetes resource using a resource definition from a file.

        Corresponding CLI command::

            $ kubectl <apply|delete> -f <filename>

        :param action: "apply" or "delete". The action to take against the resource in the given file in Kubernetes.
        :param file: Path to the file containing the resource definition.
        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :return: The content written to stdout by kubectl.
        """
        pass

    @abstractmethod
    def top_nodes(self, ignore_errors: bool = False) -> KubernetesMetrics:
        """
        Returns a KubernetesMetrics object with top values for all Nodes in the targeted Kubernetes environment.

        Corresponding CLI command::

            $ kubectl top nodes --no-headers=true

        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: A KubernetesMetrics object containing Nodes and their top values.
        """
        pass

    @abstractmethod
    def top_pods(self, ignore_errors: bool = False) -> KubernetesMetrics:
        """
        Returns a KubernetesMetrics object with top values for all Pods in the targeted Kubernetes environment.

        Corresponding CLI command::

            $ kubectl top pods --no-headers=true

        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: A KubernetesMetrics object containing Pods and their top values.
        """
        pass

    @abstractmethod
    def version(self, ignore_errors: bool = False) -> Dict:
        """
        Returns a dictionary defining the client and server versions in the Kubernetes environment. The values returned
        by Kubernetes on the initial call are cached and returned on any subsequent calls. This is because client/server
        versions are not likely to change during the execution of Viya-ARK tools. Other resources reported by kubectl
        may contain status or may in someway change during their life cycle, making caching disadvantageous. To clear
        the cached version, use Kubectl.clear_version_cache().

        Corresponding CLI command::

            $ kubectl version -o json

        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: A dictionary of values for the Kubernetes client and server versions.
        """
        pass
