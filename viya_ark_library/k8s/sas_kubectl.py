####################################################################
# ### sas_kubectl.py                                             ###
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

from subprocess import CalledProcessError, Popen, PIPE
from typing import AnyStr, Dict, List, Text, Union, Optional

from viya_ark_library.k8s.k8s_resource_keys import KubernetesResourceKeys
from viya_ark_library.k8s.sas_k8s_errors import NamespaceNotFoundError
from viya_ark_library.k8s.sas_k8s_objects import KubernetesAvailableResourceTypes, KubernetesMetrics, KubernetesResource
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface

# header values used in retrieving values returned by kubectl
_HEADER_NAME_ = "NAME"
_HEADER_SHORTNAME_ = "SHORTNAMES"
_HEADER_APIGROUP_ = "APIGROUP"
_HEADER_APIVERSION_ = "APIVERSION"
_HEADER_NAMESPACED_ = "NAMESPACED"
_HEADER_KIND_ = "KIND"
_HEADER_VERBS_ = "VERBS"


class Kubectl(KubectlInterface):
    """
    The Kubectl class represents the 'kubectl' command-line utility, allowing consumers to
    execute requests to a Kubernetes cluster via functionality provided by the command-line utility.
    """

    def __init__(self, executable: Text = "kubectl", namespace: Text = None, global_opts: Text = "") -> None:
        """
        Constructor for Kubectl class.

        :param executable: The name of the executable to use in shell executions.
        :param namespace: The namespace to target. If None, the current context will be checked for a namespace.
        :param global_opts: Any global options to apply to all Kubectl executions.
        :raises ConnectionError: If version information cannot be retrieved from the Kubernetes cluster. This does not
                                 require a namespace to be defined, so any failure would be the result of an inability
                                 to connect with the cluster.
        :raises NamespaceNotFoundError: If the namespace value passed via *namespace* does not exist in the target
                                        cluster or if a namespace value is not passed and one cannot be determined by
                                        evaluating the current context.
        """
        # define cache fields
        self._cached_api_resources: Optional[KubernetesAvailableResourceTypes] = None
        self._cached_api_versions: Optional[List] = None
        self._cached_version: Optional[Dict] = None

        # set the executable so validation calls can be made
        self.exec: Text = f"{executable} {global_opts}"

        # test the connection to the cluster
        # "kubectl version" doesn't require a namespace, but does establish a connection to the cluster
        try:
            self.version()
        except CalledProcessError:
            raise ConnectionError("A connection to the Kubernetes cluster could not be established. "
                                  "Make sure that kubectl is properly configured and the KUBECONFIG "
                                  "environment variable has a valid value on the machine where "
                                  "this command is being executed.")

        # check the namespace if an explicit value was passed
        if namespace is not None:
            try:
                # get the list of all namespaces
                existing_namespaces: List[KubernetesResource] = self.get_resources("namespaces")

                # loop over all existing namespaces and check for the given namespace
                for existing_namespace in existing_namespaces:
                    if existing_namespace.get_name() == namespace:
                        # if a match is found, break the loop to avoid the "else" execution
                        break
                else:
                    # if the loop did not break, or no namespaces are defined, then no match was found
                    # exit with an error
                    raise NamespaceNotFoundError(
                        f"The namespace [{namespace}] was not found in the target environment.")
            except CalledProcessError:
                # if the user is not able to get namespaces, then there is no way to verify the value they passed
                # assume the value is correct and move forward
                pass
        else:
            # if the namespace is None, check the current context
            config: Dict = self.config_view()

            # get the current context name
            current_context_name: Text = config.get("current-context")
            if current_context_name is not None:
                # get the list of contexts
                contexts: List = config.get("contexts")
                for context in contexts:
                    # get the context name
                    context_name: Text = context.get("name")

                    # check if this is the current context
                    if context_name == current_context_name:
                        # if this is the current context, check for a namespace definition
                        try:
                            namespace = context["context"]["namespace"]
                        except KeyError:
                            pass

                        # if the namespace was found or not, break since this is the current context
                        break

            # if a namespace was not defined in the current context, raise an error because the namespace was not
            # provided and it cannot be determined
            if namespace is None:
                raise NamespaceNotFoundError("The namespace could not be determined from the currently "
                                             "configured context. Update the current KUBECONFIG or provide a "
                                             "namespace using the \"--namespace=\" option.")

        # reset the executable with the namespace
        self.exec = f"{executable} -n {namespace} {global_opts}"
        self.namespace: Text = namespace

    def get_namespace(self) -> Text:
        return self.namespace

    def do(self, command: Text, ignore_errors: bool = False, success_rcs: Optional[List[int]] = None) \
            -> AnyStr:
        # set default return code list if one was not provided
        if success_rcs is None:
            success_rcs = [0]

        # define the process to run
        proc: Popen = Popen(f"{self.exec} {command}", shell=True, stdout=PIPE, stderr=PIPE)

        # execute the procedure
        stdout, stderr = proc.communicate()

        # get the return code
        rc: int = proc.returncode

        # check if an acceptable code was returned
        if rc not in success_rcs:
            if not ignore_errors:
                raise CalledProcessError(returncode=rc, cmd=f"{self.exec} {command}", output=stdout, stderr=stderr)
            else:
                print(f"WARNING: Error encountered executing: {self.exec} {command} "
                      f"(rc: {rc} | stdout: {stdout} | stderr: {stderr})")

        # return the stdout
        return stdout

    def api_resources(self, ignore_errors: bool = False) -> KubernetesAvailableResourceTypes:
        # return the existing api resources if cached
        if self._cached_api_resources is not None:
            return self._cached_api_resources

        # get the api-resources and convert the response into a list
        api_resource_info: AnyStr = self.do("api-resources -o wide", ignore_errors)  # exec kubectl
        api_resource_lines: List = api_resource_info.decode().split("\n")  # split by newline
        api_resource_headers: Text = api_resource_lines[0]  # headers will be on the first line

        # get the index of all expected headers
        name_index: int = api_resource_headers.index(_HEADER_NAME_)
        shortname_index: int = api_resource_headers.index(_HEADER_SHORTNAME_)
        namespaced_index: int = api_resource_headers.index(_HEADER_NAMESPACED_)
        kind_index: int = api_resource_headers.index(_HEADER_KIND_)
        verbs_index: int = api_resource_headers.index(_HEADER_VERBS_)

        # the "APIGROUP" header is renamed to "APIVERSION" at kubectl v1.20.0
        # the value reported under "APIVERSION" == "APIGROUP"/<version>
        # a notable exception is resources under the k8s core api, whose group
        # is omitted (e.g., for Pods, "APIGROUP" == "" and "APIVERSION" = "v1")

        # track whether the "APIGROUP" or "APIVERSION" was provided
        is_api_version_formatted: bool = False

        try:
            # if the "APIGROUP" header is present, use its index
            group_or_version_index = api_resource_headers.index(_HEADER_APIGROUP_)
        except ValueError:
            # if the "APIVERSION" header is present, use its index
            # otherwise, let index() raise a ValueError if the header isn't found
            # the missing headers aren't hidden
            # this helps to identify when kubectl changes it's response such that
            # this method needs to be updated to adapt to new changes
            group_or_version_index = api_resource_headers.index(_HEADER_APIVERSION_)

            # note that the "APIVERSION" header was present
            is_api_version_formatted = True

        # set up the dictionary that will be returned
        api_resources: Dict = dict()

        # iterate over all lines
        for api_resource_line in api_resource_lines[1:]:
            group: Text = ""
            kind: Text = ""
            name: Text = ""
            namespaced_str: Text = ""
            shortname: Text = ""
            verbs: List[Text] = list()
            version: Text = ""

            # get the name value
            for char in api_resource_line[name_index:]:
                if char != " ":
                    name = f"{name}{char}"
                else:
                    break

            # make sure a name was found
            if name == "":
                continue

            # get the shortname value
            for char in api_resource_line[shortname_index:]:
                if char != " ":
                    shortname = f"{shortname}{char}"
                else:
                    break

            # get the api group or api version value
            apigroup_or_apiversion: Text = ""
            for char in api_resource_line[group_or_version_index:]:
                if char != " ":
                    apigroup_or_apiversion = f"{apigroup_or_apiversion}{char}"
                else:
                    break

            # get the namespaced value
            for char in api_resource_line[namespaced_index:]:
                if char != " ":
                    namespaced_str = f"{namespaced_str}{char}"
                else:
                    break

            # make namespaced a bool
            namespaced: bool = bool(namespaced_str)

            # get the kind value
            for char in api_resource_line[kind_index:]:
                if char != " ":
                    kind = f"{kind}{char}"
                else:
                    break

            # get the verbs values
            verb_str: Text = ""
            for char in api_resource_line[verbs_index:]:
                if char == "[":
                    pass
                elif char != "]":
                    verb_str = f"{verb_str}{char}"
                else:
                    break

            # convert verb_str to list
            if " " in verb_str:
                # if there are multiple verbs split them into a list
                verbs = verb_str.split()
            elif len(verb_str) > 0:
                # if there is only one, append it to the list
                verbs.append(verb_str)

            # process the group and version based on how the return value was formatted
            if is_api_version_formatted:
                # if the "APIVERSION" value contains a '/' then it has both group and version information
                if "/" in apigroup_or_apiversion:
                    # split the returned value by the right-most '/' to separate values
                    group_and_version: List[Text] = apigroup_or_apiversion.rsplit("/", 1)
                    group = group_and_version[0]  # the group is first value
                    version = group_and_version[1]  # the version is the second value
                else:
                    # if the "APIVERSION" was returned but does not contain a '/', then this
                    # resource is a member of the k8s core api whose group information is
                    # omitted, so the value returned represents only the version information
                    version = apigroup_or_apiversion
            else:
                # the "APIGROUP" value was returned, which doesn't include version information
                # group can be set to the value returned without processing
                group = apigroup_or_apiversion

            # it's possible that resource may have matching name and/or kind values
            # example:
            #    kind: Pgcluster, name: pgclusters, group: crunchydata.com
            #    kind: Pgcluster, name: pgclusters, group: webinfdsvr.sas.com
            #
            # for this reason, build a qualified name including the group information to
            # avoid ambiguity, k8s defines a qualified name as: <name>.<group>
            if group:
                qualified_name: Text = f"{name}.{group}"
            else:
                # resources in the k8s core api won't have a group value, just use the name
                qualified_name = name

            # add this resource to dictionary defining all resources
            # values are keyed on the qualified name of the resource to help avoid ambiguity
            api_resources[qualified_name]: Dict = dict()
            api_resources[qualified_name][KubernetesAvailableResourceTypes.Keys.GROUP]: Text = group
            api_resources[qualified_name][KubernetesAvailableResourceTypes.Keys.KIND]: Text = kind
            api_resources[qualified_name][KubernetesAvailableResourceTypes.Keys.NAME]: Text = name
            api_resources[qualified_name][KubernetesAvailableResourceTypes.Keys.NAMESPACED]: bool = namespaced
            api_resources[qualified_name][KubernetesAvailableResourceTypes.Keys.SHORT_NAME]: Text = shortname
            api_resources[qualified_name][KubernetesAvailableResourceTypes.Keys.VERBS]: List[Text] = verbs
            api_resources[qualified_name][KubernetesAvailableResourceTypes.Keys.VERSION]: Text = version

        # cache the response for subsequent calls
        self._cached_api_resources = KubernetesAvailableResourceTypes(api_resources)
        return self._cached_api_resources

    def api_versions(self, ignore_errors: bool = False) -> List:
        if self._cached_api_versions is not None:
            return self._cached_api_versions

        # get the api-versions and convert to list before returning
        api_version_info: AnyStr = self.do("api-versions", ignore_errors)
        self._cached_api_versions = api_version_info.decode().split("\n")
        return self._cached_api_versions

    def can_i(self, action: Text, all_namespaces: bool = False, ignore_errors: bool = False) -> bool:
        # define the command
        cmd: Text = f"auth can-i {action} --quiet"

        # add the all-namespaces option, if specified
        if all_namespaces:
            cmd = f"{cmd} --all-namespaces"

        # run the command
        try:
            self.do(cmd, ignore_errors)
        except CalledProcessError as proc_error:
            # in quiet mode, only an exit code is returned
            # if that code is '1', then the action is not allowed
            if proc_error.returncode == 1:
                return False
            else:
                raise proc_error

        # at this point, a 0 must have been returned
        # the action is allowed
        return True

    def clear_api_resources_cache(self):
        """
        Clears the api_resources cache so that the next execution of Kubectl.api_resources() returns the most current
        values as reported by Kubernetes.
        """
        self._cached_api_resources = None

    def clear_api_versions_cache(self):
        """
        Clears the api_versions cache so that the next execution of Kubectl.api_versions() returns the most current
        values as reported by Kubernetes.
        """
        self._cached_api_versions = None

    def clear_version_cache(self):
        """
        Clears the Kubernetes client/server version cache so that the next execution of Kubectl.version() returns
        the most current values as reported by Kubernetes.
        """
        self._cached_api_versions = None

    def config_view(self, ignore_errors: bool = False) -> Dict:
        # get the raw config response
        config_json = self.do("config view -o json", ignore_errors)

        # return the config as a Python-native dictionary
        return json.loads(config_json)

    def cluster_info(self) -> Optional[AnyStr]:
        # get the cluster-info output
        cmd: Text = "cluster-info"

        # run the command
        return self.do(cmd, False)

    def get_resources(self, type_version_group: Text, raw: bool = False) -> Union[Dict, List[KubernetesResource]]:
        # get the JSON representation of all requested kubernetes API resources
        resource_json: AnyStr = self.do(f"get {type_version_group} -o json")

        # return the raw response, if requested
        if raw:
            return json.loads(resource_json.decode())

        # convert json into python native list
        resources_list: List = json.loads(resource_json.decode()).get(KubernetesResourceKeys.ITEMS)

        # iterate all dictionary definitions in the list and create Resource objects
        resources: List[KubernetesResource] = list()
        for resource_dict in resources_list:
            resources.append(KubernetesResource(resource_dict))

        # return the list of KubernetesResource objects
        return resources

    def get_resource(self, type_version_group: Text, resource_name: Text, raw: bool = False,
                     ignore_errors: bool = False) -> Union[AnyStr, KubernetesResource]:
        # get the resource definition as a JSON str
        resource_json: AnyStr = self.do(f"get {type_version_group} {resource_name} -o json", ignore_errors)

        # return the raw response, if requested
        if raw:
            return resource_json

        return KubernetesResource(resource_json.decode())

    def logs(self, pod_name: Text, container_name: Optional[Text] = None, prefix: bool = True, tail: int = 10,
             ignore_errors: bool = False) -> List:

        # create the command to execute
        cmd: Text
        if not container_name:
            cmd = f"logs {pod_name} --all-containers --tail={tail}"
        else:
            cmd = f"logs {pod_name} {container_name} --tail={tail}"

        if prefix:
            cmd = f"{cmd} --prefix"

        pod_logs_raw: AnyStr = self.do(cmd, ignore_errors)
        if pod_logs_raw:
            return pod_logs_raw.decode().split("\n")
        return list()

    def manage_resource(self, action: Text, file: Text, ignore_errors: bool = False) -> AnyStr:
        # define the command
        cmd: Text = f"{action} -f {file}"

        # run the command
        return self.do(cmd, ignore_errors)

    def top_nodes(self, ignore_errors: bool = False) -> KubernetesMetrics:
        # get the top values
        top_nodes_raw: AnyStr = self.do("top nodes --no-headers=true", ignore_errors)
        top_nodes_lines: List = top_nodes_raw.decode().split("\n")

        # store the top nodes values
        top_nodes_info: Dict = dict()

        # format data returned from call
        for top_nodes_line in top_nodes_lines:
            # split by whitespace
            node_info: List = top_nodes_line.split()

            # make sure the right number of attributes exist
            if len(node_info) == 5:
                node_name: Text = node_info[0]

                top_nodes_info[node_name]: Dict = dict()
                top_nodes_info[node_name][KubernetesMetrics.Keys.CPU_CORES]: Text = node_info[1]
                top_nodes_info[node_name][KubernetesMetrics.Keys.CPU_USED]: Text = node_info[2]
                top_nodes_info[node_name][KubernetesMetrics.Keys.MEMORY_BYTES]: Text = node_info[3]
                top_nodes_info[node_name][KubernetesMetrics.Keys.MEMORY_USED]: Text = node_info[4]

        return KubernetesMetrics(top_nodes_info)

    def top_pods(self, ignore_errors: bool = False) -> KubernetesMetrics:
        # get the top values
        top_pods_raw: AnyStr = self.do("top pods --no-headers=true", ignore_errors)
        top_pods_lines: List = top_pods_raw.decode().split("\n")

        # store the top pods values
        top_pods_info: Dict = dict()

        # format data from call
        for top_pods_line in top_pods_lines:
            # split by whitespace
            pod_info: List = top_pods_line.split()

            # make sure the right number of attributes exist
            if len(pod_info) == 3:
                pod_name: Text = pod_info[0]

                top_pods_info[pod_name]: Dict = dict()
                top_pods_info[pod_name][KubernetesMetrics.Keys.CPU_CORES]: Text = pod_info[1]
                top_pods_info[pod_name][KubernetesMetrics.Keys.CPU_USED] = None
                top_pods_info[pod_name][KubernetesMetrics.Keys.MEMORY_BYTES]: Text = pod_info[2]
                top_pods_info[pod_name][KubernetesMetrics.Keys.MEMORY_USED] = None

        return KubernetesMetrics(top_pods_info)

    def version(self, ignore_errors: bool = False) -> Dict:
        if self._cached_version is not None:
            return self._cached_version

        # get the Kubernetes versions and convert to a dict before returning
        version_json: AnyStr = self.do("version -o json", ignore_errors)
        self._cached_version = json.loads(version_json.decode())
        return self._cached_version
