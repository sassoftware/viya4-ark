####################################################################
# ### model.py                                                   ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import datetime
import os
import sys

from multiprocessing import Pool, TimeoutError
from multiprocessing.pool import ApplyResult
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Text, Tuple

from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface
from viya_ark_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from viya_ark_library.structured_logging.parser import SASStructuredLoggingParser


####################################################################
# Class: PodLogDownloader                                        ###
####################################################################
class PodLogDownloader(object):
    """
    PodLogDownloader is responsible for configuring and executing asynchronous log gathering for all or a select
    number of pods in a given namespace.
    """
    # parameter default values
    DEFAULT_OUTPUT_DIR: Text = "sas-k8s-logs"
    DEFAULT_PROCESSES: int = 2
    DEFAULT_TAIL: int = 25000
    DEFAULT_WAIT = 30

    def __init__(self, kubectl: KubectlInterface, output_dir: Text = DEFAULT_OUTPUT_DIR,
                 processes: int = DEFAULT_PROCESSES, wait: int = DEFAULT_WAIT) -> None:
        """
        PodLogDownloader is responsible for configuring and executing asynchronous log gathering for all or a select
        number of pods in a given namespace.

        :param kubectl: KubectlInterface object used for requesting information from the Kubernetes server.
        :param output_dir: Location where resulting log files will be written.
        :param processes: Number of concurrent, asynchronous processes to execute for retrieving pod logs.
        :param wait: Time, in seconds, to wait before a log retrieval process is terminated.
        :raises AttributeError: If the number of concurrent processes is less than 1 or the process wait time is less
                                than 0.
        """
        if processes < 1:
            raise AttributeError("The processes value must be greater than 0")

        if wait < 0:
            raise AttributeError("The wait value must be 0 or greater")

        self._kubectl = kubectl
        self._output_dir = output_dir
        self._processes = processes
        self._pool = Pool(processes=processes)
        self._wait = wait

    def download_logs(self, selected_components: Optional[List[Text]] = None, tail: int = DEFAULT_TAIL) \
            -> Tuple[Text, List[Text]]:
        """
        Downloads the log files for all or a select group of pods and their containers. A status summary is prepended
        to the downloaded log file.

        :param selected_components: List of component names for which logs should be retrieved.
        :param tail: Lines of recent log file to retrieve.

        :raises KubectlRequestForbiddenError: If list pods is forbidden in the given namespace.
        :raises NoPodsError: If pods can be listed but no pods are found in the given namespace.
        :raises NoMatchingPodsError: If no available pods match a component in the selected_components

        :returns: A tuple containing the absolute output directory and a list of names for any pods for which the
                  timeout was reached when gathering the log.
        """
        # get the current namespace
        namespace = self._kubectl.get_namespace()

        # get all available pods
        try:
            available_pods: List[KubernetesResource] = self._kubectl.get_resources("pods")
        except CalledProcessError:
            # if a CalledProcessError is raised when gathering pods, surface an error up to stop the program #
            raise KubectlRequestForbiddenError(f"Listing pods is forbidden in namespace [{namespace}]. "
                                               "Make sure KUBECONFIG is correctly set and that the correct namespace "
                                               "is being targeted. A namespace can be given on the command line using "
                                               "the \"--namespace=\" option.")

        # if an error didn't occur getting pods, but none were found, raise a NoPodsError
        if len(available_pods) == 0:
            raise NoPodsError(f"No pods were found in namespace [{namespace}].")

        # create a list to hold the pods that will be run against
        selected_pods: List[KubernetesResource] = list()

        # filter list of pods down to selected components
        if selected_components is not None and len(selected_components) > 0:
            for pod in available_pods:
                # check for a component-name annotation match
                if pod.get_sas_component_name() in selected_components:
                    selected_pods.append(pod)

                # check if the pod has a container with a name in the selected components list
                else:
                    containers: List[Dict] = pod.get_spec_value(KubernetesResource.Keys.CONTAINERS)
                    for container in containers:
                        name: Text = container.get("name")

                        if name in selected_components:
                            selected_pods.append(pod)
                            # break the loop and move to the next pod since this pod is now in the list
                            break

            # if no pods matched the selected_components filter, raise a NoMatchingPodsError
            if len(selected_pods) == 0:
                raise NoMatchingPodsError(f"No pods in namespace [{namespace}] matched the provided components filter: "
                                          f"[{', '.join(selected_components)}]")
        else:
            # if selected components weren't provided, use the complete list of available pods
            selected_pods.extend(available_pods)

        # a NoPodsError would have been raised if there are no pods in the namespace and a NoMatchingPodsError would
        # have been raised if no pods matched the selected_components
        # at this point, pods are available for gathering logs

        # create the output dir, if needed
        self._output_dir = os.path.join(self._output_dir, datetime.datetime.now().strftime("%Y-%m-%dT%H_%M_%S"))
        os.makedirs(self._output_dir, exist_ok=True)

        # create the list of pooled asynchronous processes
        write_log_processes: List[_LogDownloadProcess] = list()
        for pod in selected_pods:
            process = self._pool.apply_async(self._write_log, args=(self._kubectl, pod, tail, self._output_dir))
            download_process = _LogDownloadProcess(pod.get_name(), process)
            write_log_processes.append(download_process)

        # run the processes
        timeout_pods: List[Text] = list()
        for process in write_log_processes:
            try:
                process.get_process().get(timeout=self._wait)
            except TimeoutError:
                timeout_pods.append(process.get_pod_name())

        return os.path.abspath(self._output_dir), timeout_pods

    @staticmethod
    def _write_log(kubectl: KubectlInterface, pod: KubernetesResource, tail: int, output_dir: Text) -> None:
        """
        Internal method used for gathering the status and log for each container in the provided pod and writing
        the gathered information to an on-disk log file.

        :param kubectl: The kubectl object configured for interfacing with the Kubernetes cluster.
        :param pod: KubernetesResource representation of the pod whose logs will be retrieved.
        :param tail: Lines of recent log file to retrieve.
        :param output_dir: The directory where log files should be written.
        """
        # if this pod is not a SAS-provided resource, skip it
        if not pod.is_sas_resource():
            return

        # get the containerStatuses for this pod
        container_statuses: List[Dict] = pod.get_status_value(KubernetesResource.Keys.CONTAINER_STATUSES)

        # for each container status in the list, gather status and print values and log into file
        for container_status_dict in container_statuses:
            # create object to get container status values
            container_status = _ContainerStatus(container_status_dict)

            # build the output file name
            # if there are no containers to report on, return
            if len(container_statuses) == 0:
                return
            # if there is only one container, only include the pod name in the log file name
            elif len(container_statuses) == 1:
                output_file_path = f"{output_dir}{os.sep}{pod.get_name()}.log"
            # if there is more than one container, include both the pod and container name in the log file name
            else:
                output_file_path = f"{output_dir}{os.sep}{pod.get_name()}_{container_status.get_name()}.log"

            # open the output file for writing
            with open(output_file_path, "w", encoding="utf-8") as output_file:
                # template for a line in the log header
                header_tmpl = "# {:<25} {}\n"

                # write status information at the top of the log
                output_file.write(("#" * 50) + "\n")
                output_file.write("# Container Status\n")
                output_file.write("#\n")
                output_file.writelines(header_tmpl.format("sas-component-name:", pod.get_sas_component_name()))
                output_file.writelines(header_tmpl.format("sas-component-version:", pod.get_sas_component_version()))
                for key, value in container_status.get_headers_dict().items():
                    output_file.writelines(header_tmpl.format(f"{key}:", value))

                # close the status header
                output_file.writelines(("#" * 50) + "\n\n")

                # call kubectl to get the log for this container
                try:
                    log = kubectl.logs(pod_name=f"{pod.get_name()} {container_status.get_name()}",
                                       all_containers=False, prefix=False, tail=tail)
                except CalledProcessError:
                    # print a message to stderr if the log file could not be retrieved for this container
                    print(f"\nERROR: A log could not be retrieved for the container [{container_status.get_name()}] "
                          f"in pod [{pod.get_name()}] in namespace [{kubectl.get_namespace()}]", file=sys.stderr)

                # parse any structured logging
                file_content = SASStructuredLoggingParser.parse_log(log)

                # write the retrieved log to the file
                output_file.write("Beginning log...\n\n")
                output_file.write("\n".join(file_content))


####################################################################
# Class: NoMatchingPodsError                                     ###
####################################################################
class NoMatchingPodsError(RuntimeError):
    """
    RuntimeError raised when no pods match the selected pods.
    """
    def __init__(self, message):
        super().__init__(message)


####################################################################
# Class: NoPodsError                                             ###
####################################################################
class NoPodsError(RuntimeError):
    """
    RuntimeError raised when no pods are discovered in the target environment.
    """
    def __init__(self, message):
        super().__init__(message)


####################################################################
# Class: _ContainerStatus                                        ###
####################################################################
class _ContainerStatus(object):
    """
    Internal class used to represent and provide access to values in the containerStatus dictionary returned by
    kubectl for each container in a pod.
    """

    def __init__(self, container_status_dict: Dict) -> None:
        """
        Internal class used to represent and provide access to values in the containerStatus dictionary returned by
        kubectl for each container in a pod.

        :param container_status_dict: The container status dictionary from the pod resources.
        """
        self._container_status_dict: Dict = container_status_dict

    def _get_value(self, key: Text) -> Any:
        """
        Internal method for generically retrieving a value in the dictionary.

        :param key: The key for the value to be retrieved.
        :return: The value associated with the provided key.
        """
        value = self._container_status_dict.get(key)
        if value is None:
            # return an empty string for printing in the log
            return ""

        return value

    def get_image(self) -> Text:
        """
        Returns the containerStatus.image value.

        :return: The containerStatus.image value
        """
        return self._get_value(KubernetesResource.Keys.IMAGE)

    def get_name(self) -> Text:
        """
        Returns the containerStatus.name value.

        :return: The containerStatus.name value
        """
        return self._get_value(KubernetesResource.Keys.NAME)

    def is_ready(self) -> Text:
        """
        Returns the containerStatus.ready value.

        :return: The containerStatus.ready value.
        """
        return str(self._get_value(KubernetesResource.Keys.READY))

    def get_restart_count(self) -> Text:
        """
        Returns the containerStatus.restartCount value.

        :return: The containerStatus.restartCount value.
        """
        return str(self._get_value(KubernetesResource.Keys.RESTART_COUNT))

    def is_started(self) -> Text:
        """
        Returns the containerStatus.started value.

        :return: The containerStatus.started value.
        """
        return str(self._get_value(KubernetesResource.Keys.STARTED))

    def get_state_dict(self) -> Dict[Text, Text]:
        """
        Returns a flattened version of the containerStatus.state dictionary with one level of keys for the current
        container state.

        :return: A flattened containerStatus.state dictionary.
        """
        # get the containerStatus.state dict
        container_state: Dict = self._container_status_dict.get(KubernetesResource.Keys.STATE)

        # create a dictionary to hold the state values
        state_dict: Dict = dict()

        # if there is no state dict, return the empty dict object
        if not container_state:
            return state_dict

        # handle the "running" state
        if "running" in container_state:
            running: Dict = container_state["running"]
            state_dict["container-state"] = "running"
            state_dict["container-started-at"] = running["startedAt"]

        # handle the terminated state
        elif "terminated" in container_state:
            terminated: Dict = container_state["terminated"]
            state_dict["container-state"] = "terminated"
            state_dict["container-state-reason"] = terminated["reason"]
            state_dict["container-started-at"] = terminated["startedAt"]
            state_dict["container-finished-at"] = terminated["finishedAt"]

        # handle the waiting state
        elif "waiting" in container_state:
            waiting: Dict = container_state["waiting"]
            state_dict["container-state"] = "waiting"
            state_dict["container-state-reason"] = waiting["reason"]

        return state_dict

    def get_headers_dict(self) -> Dict[Text, Text]:
        """
        Returns a dictionary of all status values to be printed as log headers.

        :return: A dictionary of all status values.
        """
        headers_dict: Dict = dict()

        # load values into headers dict
        headers_dict["container-name"] = self.get_name()
        headers_dict["container-image"] = self.get_image()
        headers_dict["container-is-started"] = self.is_started()
        headers_dict["container-is-ready"] = self.is_ready()
        headers_dict["container-restarts"] = self.get_restart_count()

        # add in state values
        headers_dict.update(self.get_state_dict())

        # return the dict
        return headers_dict


####################################################################
# Class: _LogDownloadProcess                                     ###
####################################################################
class _LogDownloadProcess(object):

    def __init__(self, pod_name: Text, process: ApplyResult):
        """
        Constructs a new _LogDownloadProcess instance.

        :param pod_name: The name of pod targeted by this process.
        :param process: The reference to the Asynchronous download process.
        """
        self._pod_name: Text = pod_name
        self._process: ApplyResult = process

    def get_pod_name(self) -> Text:
        """
        Returns the name of the pod being targeted by this _LogDownloadProcess.

        :return: The name of the pod whose logs are being targeted.
        """
        return self._pod_name

    def get_process(self) -> ApplyResult:
        """
        Returns the process reference for the asynchronous log download process.

        :return: The reference to the process for downloading the pod logs.
        """
        return self._process
