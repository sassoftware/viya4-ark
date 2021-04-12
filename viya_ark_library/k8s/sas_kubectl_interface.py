####################################################################
# ### sas_kubectl_interface.py                                   ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from abc import ABC, abstractmethod
from typing import AnyStr, Dict, List, Text, Union, Optional

from viya_ark_library.k8s.sas_k8s_objects import KubernetesApiResources, KubernetesMetrics, KubernetesResource


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
    def do(self, command: Text, ignore_errors: bool = False) -> AnyStr:
        """
        Generic method for executing a kubectl command.

        :param command: The kubectl command to execute.
        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: The stdout of the command that was executed.
        """
        pass

    @abstractmethod
    def api_resources(self, ignore_errors: bool = False) -> KubernetesApiResources:
        """
        Returns an ApiResources object defining all kubernetes API resources.

        Corresponding CLI command::

            $ kubectl api-resources -o wide

        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: An ApiResources object.
        """
        pass

    @abstractmethod
    def api_versions(self, ignore_errors: bool = False) -> List:
        """
        Returns a list of all kubernetes API versions.

        Corresponding CLI command::

            $ kubectl api-versions

        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: A list of all Kubernetes API versions.
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
    def manage_resource(self, action: Text, file: Text, ignore_errors: bool = False, ) -> AnyStr:
        """
        Returns the ouput from a apply -f or,  delete -f kubectl command as a string

        Corresponding CLI command::

            $ kubectl apply -f <filename> or  kubectl delete -f <filename>

        :param action:  apply or delete specified deployment file
        :param file: name of file with path
        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :return: A the output as a string
        """
        pass

    @abstractmethod
    def config_view(self, ignore_errors: bool = False) -> Dict:
        """
        Returns the current kubectl config as a Python-native dict (or as a raw string if raw=True).

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
        Returns the output from the cluster-info command

        CLI command::

            $ kubectl cluster-info

        :return: The stdout of the command that was executed.
        """

    @abstractmethod
    def get_resources(self, k8s_api_resource: Text, raw: bool = False) -> Union[Dict, List[KubernetesResource]]:
        """
        Issues a kubectl command to retrieve a list of Kubernetes resources.

        Corresponding CLI command::

            $ kubectl get <k8s_resource> -o json

        :param k8s_api_resource: The Kubernetes resource to retrieve.
        :param raw: Return the raw response from kubectl, not a Python native object.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: If raw=True, the raw response from kubectl, otherwise a list (including empty list) of Resource objects
                 for the requested Kubernetes resource or None if the resource was not accessible.
        """
        pass

    @abstractmethod
    def get_resource(self, k8s_api_resource: Text, resource_name: Text, raw: bool = False,
                     ignore_errors: bool = False) -> Union[AnyStr, KubernetesResource]:
        """
        Issues a kubectl command to retrieve the definition of the requested Kubernetes resource.

        Corresponding CLI command::

            $ kubectl get <k8s_resource> <resource_name> -o json

        :param k8s_api_resource: The Kubernetes resource to retrieve.
        :param resource_name: The name of the resource to retrieve.
        :param raw: Return the raw response from kubectl, not a Python native object.
        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: If raw=True, the raw response from kubectl, otherwise a Resource object representing the requested
                 resource.
        """
        pass

    @abstractmethod
    def logs(self, pod_name: Text, container_name: Optional[Text] = None, prefix: bool = True, tail: int = 10,
             ignore_errors: bool = False) -> List:
        """
        Retrieves logs from the pod with the given name.

        Corresponding CLI command::

            $ kubectl logs <pod_name> [--all-containers] [--prefix] --tail=<tail>

        :param pod_name: The name of the Pod whose logs should be retrieved.
        :param container_name: The name of the specific container whose log should be retrieved. If not container is
                               specified, the --all-containers option is used.
        :param prefix: True if the log lines should be prefixed with the container's name, otherwise False.
        :param tail: (default: 10) Limits the results to the given number of lines. Setting this to '-1' will return the
                     complete log.
        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: A list of the requested lines from the given Pods logs.
        """
        pass

    @abstractmethod
    def top_nodes(self, ignore_errors: bool = False) -> KubernetesMetrics:
        """
        Returns a KuberentesMetrics object with top values for all Nodes in the Kubernetes environment.

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
        Returns a KubernetesMetrics object with top values for all Pods in the Kubernetes environment.

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
        Returns a dictionary defining the client and server versions in the Kubernetes environment.

        Corresponding CLI command::

        $ kubectl version -o json

        :param ignore_errors: True if errors encountered during execution should be ignored (a message will be printed
                              to stdout), otherwise False.
        :raises CalledProcessError: If the command returns a non-zero return code.
        :return: A dictionary of values for the Kubernetes client and server versions.
        """
        pass
