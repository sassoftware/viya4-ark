####################################################################
# ### sas_kubectl.py                                             ###
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
from subprocess import CalledProcessError, check_output, DEVNULL
from collections.abc import MutableMapping

# header values used in retrieving values returned by kubectl
HEADER_NAME = 'NAME'
HEADER_SHORTNAME = 'SHORTNAMES'
HEADER_APIGROUP = 'APIGROUP'
HEADER_NAMESPACED = 'NAMESPACED'
HEADER_KIND = 'KIND'
HEADER_VERBS = 'VERBS'


class Kubectl(object):
    """
    The Kubectl class represents the 'kubectl' command-line utility, allowing consumers to
    execute requests to a Kubernetes cluster via functionality provided by the command-line utility.
    """
    def __init__(self, executable='kubectl', global_opts=''):
        """
        Constructor for Kubectl class.

        :param executable: The name of the executable to use in shell executions.
        :param global_opts: Any global options to apply to all Kubectl executions.
        """
        self.executable = '{} {}'.format(executable, global_opts)

    def do(self, command, ignore_errors=False):
        """
        Generic method for executing a kubectl command.

        Raises
        ---------
        CalledProccessError             if the command returns a non-zero return code

        :param command: The kubectl command to execute.
        :param ignore_errors: True if errors encountered during execution should be ignored
            (a message will be printed to stdout), otherwise False.
        :return: The stdout of the command that was executed.
        """
        try:
            return check_output(f'{self.executable} {command}', shell=True, stderr=DEVNULL)
        except CalledProcessError as e:
            if not ignore_errors:
                raise e
            print(f'[WARN ] Error ignored executing: {self.executable} {command} \
                    (rc: {e.returncode} | output: {e.output})')

    def api_resources(self, ignore_errors=False):
        """
        Returns an ApiResources object defining all kubernetes API resources.

        Corresponding CLI command:
        $ kubectl api-resources -o wide

        Raises
        ---------
        CalledProccessError             if the command returns a non-zero return code

        :param ignore_errors: True if errors encountered during execution should be
            ignored (a message will be printed to stdout), otherwise False.
        :return: An ApiResources object.
        """
        # call kubectl to get resources
        api_resource_info = self.do('api-resources -o wide', ignore_errors)
        api_resource_lines = api_resource_info.decode().split('\n')
        api_resource_headers = api_resource_lines[0]

        # get the index of all expected headers
        name_index = api_resource_headers.index(HEADER_NAME)
        shortname_index = api_resource_headers.index(HEADER_SHORTNAME)
        apigroup_index = api_resource_headers.index(HEADER_APIGROUP)
        namespaced_index = api_resource_headers.index(HEADER_NAMESPACED)
        kind_index = api_resource_headers.index(HEADER_KIND)
        verbs_index = api_resource_headers.index(HEADER_VERBS)

        # set up the dictionary that will be returned
        api_resources = dict()

        # iterate over all lines
        for api_resource_line in api_resource_lines[1:]:
            name = ''
            shortname = ''
            api_group = ''
            namespaced = ''
            kind = ''

            # get the name value
            for char in api_resource_line[name_index:]:
                if char != ' ':
                    name = name + char
                else:
                    break

            # make sure a name was found
            if name == '':
                continue

            # get the shortname value
            for char in api_resource_line[shortname_index:]:
                if char != ' ':
                    shortname = shortname + char
                else:
                    break

            # get the api group value
            for char in api_resource_line[apigroup_index:]:
                if char != ' ':
                    api_group = api_group + char
                else:
                    break

            # get the namespaced value
            for char in api_resource_line[namespaced_index:]:
                if char != ' ':
                    namespaced = namespaced + char
                else:
                    break

            # make namespaced a bool
            namespaced = bool(namespaced)

            # get the kind value
            for char in api_resource_line[kind_index:]:
                if char != ' ':
                    kind = kind + char
                else:
                    break

            # get the verbs values:
            verb_str = ''
            for char in api_resource_line[verbs_index:]:
                if char == '[':
                    pass
                elif char != ']':
                    verb_str = verb_str + char
                else:
                    break

            # convert verb_str to list
            if ' ' in verb_str:
                verbs = verb_str.split()
            else:
                verbs = list()

            api_resources[kind] = dict()
            api_resources[kind][self.ApiResources.Keys.NAME] = name
            api_resources[kind][self.ApiResources.Keys.SHORT_NAME] = shortname
            api_resources[kind][self.ApiResources.Keys.API_GROUP] = api_group
            api_resources[kind][self.ApiResources.Keys.NAMESPACED] = namespaced
            api_resources[kind][self.ApiResources.Keys.VERBS] = verbs

        return self.ApiResources(api_resources)

    def api_versions(self, ignore_errors=False):
        """
        Returns a list of all kubernetes API versions.

        Corresponding CLI command:
        $ kubectl api-versions

        Raises
        ---------
        CalledProccessError             if the command returns a non-zero return code

        :param ignore_errors: True if errors encountered during execution should be ignored
            (a message will be printed to stdout), otherwise False.
        :return: A list of all Kubernetes API versions.
        """
        api_version_info = self.do('api-versions', ignore_errors)
        return api_version_info.decode().split('\n')

    def can_i(self, action, all_namespaces=False, ignore_errors=False):
        """
        Determines if the currently configured user for kubectl has the ability to run the requested action. If so,
        True is returned, otherwise False.

        Corresponding CLI command:
        $ kubectl auth can-i <action> [--all-namespaces]

        Raises
        ---------
        CalledProccessError             if the command returns a non-zero return code

        :param action: The action for which permissions will be checked.
        :param all_namespaces: True if the specified action should be checked in all namespaces, otherwise False.
        :param ignore_errors: True if errors encountered during execution should be ignored
            (a message will be printed to stdout), otherwise False.
        :return: True if the action can be performed, otherwise False.
        """
        # define the command
        cmd = f'auth can-i {action} --quiet'

        # add the all-namespaces option, if specified
        if all_namespaces:
            cmd = f'{cmd} --all-namespaces'

        # run the command
        try:
            self.do(cmd, ignore_errors)
        except CalledProcessError as proc_error:
            # in quiet mode, only an exit code is returned
            # if that code is one, then the action is not allowed
            if proc_error.returncode == 1:
                return False
            else:
                raise proc_error

        # at this point, a 0 must have been returned
        # the action is allowed
        return True

    def get_resources(self, k8s_api_resource, raw=False):
        """
        Issues a kubectl command to retrieve a list of Kubernetes resources.

        Corresponding CLI command:
        $ kubectl get <k8s_resource> -o json

        :param k8s_api_resource: The Kubernetes resource to retrieve.
        :param raw: Return the raw response from kubectl, not a Python native object.
        :return: If raw=True, the raw response from kubectl, otherwise a list
            (including empty list) of Resource objects for the requested Kubernetes resource or None if the
            resource was not accessible.
        """
        try:
            # get the JSON representation of all requested kubernetes API resources
            resource_json = self.do(f'get {k8s_api_resource} -o json')

            # return the raw response, if requested
            if raw:
                return json.loads(resource_json.decode())
                # return resource_json

            # convert json into python native list
            resources_list = json.loads(resource_json.decode()).get(self.Resource.Keys.ITEMS)

            # iterate all dictionary definitions in the list and create Resource objects
            resources = list()
            for resource_dict in resources_list:
                resources.append(self.Resource(resource_dict))

            # return the list of Resource objects
            return resources
        except CalledProcessError:
            return None

    def get_resource(self, k8s_api_resource, resource_name, raw=False, ignore_errors=False):
        """
        Issues a kubectl command to retrieve the definition of the requested Kubernetes resource.

        Corresponding CLI command:
        $ kubectl get <k8s_resource> <resource_name> -o json

        Raises
        ---------
        CalledProccessError             if the command returns a non-zero return code

        :param k8s_api_resource: The Kubernetes resource to retrieve.
        :param resource_name: The name of the resource to retrieve.
        :param raw: Return the raw response from kubectl, not a Python native object.
        :param ignore_errors: True if errors encountered during execution should be ignored
            (a message will be printed to stdout), otherwise False.
        :return: If raw=True, the raw response from kubectl, otherwise a Resource object
            representing the requested resource.
        """
        resource_json = self.do(f'get {k8s_api_resource} {resource_name} -o json', ignore_errors)

        # return the raw response, if requested
        if raw:
            return resource_json

        return self.Resource(resource_json.decode())

    def logs(self, pod_name, all_containers=True, prefix=True, tail=10, ignore_errors=False):
        """
        Retrieves logs from the pod with the given name.

        Corresponding CLI command:
        $ kubectl logs <pod_name> [--all-containers] [--prefix] --tail=<tail>

        Raises
        ---------
        CalledProccessError             if the command returns a non-zero return code

        :param pod_name: The name of the Pod whose logs should be retrieved.
        :param all_containers: True if logs should include all containers in the Pod, otherwise False.
        :param prefix: True if the log lines should be prefixed with the container's name, otherwise False.
        :param tail: (default: 10) Limits the results to the given number of lines.
            Setting this to '-1' will return the complete log.
        :param ignore_errors: True if errors encountered during execution should be ignored
            (a message will be printed to stdout), otherwise False.
        :return: A list of the requested lines from the given Pods logs.
        """
        cmd = f'logs {pod_name} --tail={tail}'

        if all_containers:
            cmd = f'{cmd} --all-containers'

        if prefix:
            cmd = f'{cmd} --prefix'

        pod_logs_raw = self.do(cmd, ignore_errors)
        return pod_logs_raw.decode().split('\n')

    def top_nodes_admin(self, ignore_errors=False):
        """
        Returns a Metrics object with top values for all Nodes in the Kubernetes environment.

        Corresponding CLI command:
        $ kubectl top nodes --no-headers=true

        Raises
        ---------
        CalledProccessError             if the command returns a non-zero return code

        :param ignore_errors: True if errors encountered during execution should be ignored
            (a message will be printed to stdout), otherwise False.
        :return: A Metrics object containing Nodes and their top values.
        """
        # get the top values
        top_nodes_raw = self.do('top nodes --no-headers=true', ignore_errors)
        top_nodes_lines = top_nodes_raw.decode().split('\n')

        # store the top nodes values
        top_nodes_info = dict()

        # format data returned from call
        for top_nodes_line in top_nodes_lines:
            # split by whitespace
            node_info = top_nodes_line.split()

            # make sure the right number of attributes exist
            if len(node_info) == 5:
                node_name = node_info[0]

                top_nodes_info[node_name] = dict()
                top_nodes_info[node_name][self.Metrics.Keys.CPU_CORES] = node_info[1]
                top_nodes_info[node_name][self.Metrics.Keys.CPU_USED] = node_info[2]
                top_nodes_info[node_name][self.Metrics.Keys.MEMORY_BYTES] = node_info[3]
                top_nodes_info[node_name][self.Metrics.Keys.MEMORY_USED] = node_info[4]

        return self.Metrics(top_nodes_info)

    def top_pods(self, ignore_errors=False):
        """
        Returns a Metrics object with top values for all Pods in the Kubernetes environment.

        Corresponding CLI command:
        $ kubectl top pods --no-headers=true

        Raises
        ---------
        CalledProccessError             if the command returns a non-zero return code

        :param ignore_errors: True if errors encountered during execution should be ignored
            (a message will be printed to stdout), otherwise False.
        :return: A Metrics object containing Pods and their top values.
        """
        # get the top values
        top_pods_raw = self.do('top pods --no-headers=true', ignore_errors)
        top_pods_lines = top_pods_raw.decode().split('\n')

        # store the top pods values
        top_pods_info = dict()

        # format data from call
        for top_pods_line in top_pods_lines:
            # split by whitespace
            pod_info = top_pods_line.split()

            # make sure the right number of attributes exist
            if len(pod_info) == 3:
                pod_name = pod_info[0]

                top_pods_info[pod_name] = dict()
                top_pods_info[pod_name][self.Metrics.Keys.CPU_CORES] = pod_info[1]
                top_pods_info[pod_name][self.Metrics.Keys.CPU_USED] = None
                top_pods_info[pod_name][self.Metrics.Keys.MEMORY_BYTES] = pod_info[2]
                top_pods_info[pod_name][self.Metrics.Keys.MEMORY_USED] = None

        return self.Metrics(top_pods_info)

    def version(self, ignore_errors=False):
        """
        Returns a dictionary defining the client and server versions in the Kubernetes environment.

        Corresponding CLI command:
        $ kubectl version -o json

        Raises
        ---------
        CalledProccessError             if the command returns a non-zero return code

        :param ignore_errors: True if errors encountered during execution should be ignored
            (a message will be printed to stdout), otherwise False.
        :return: A dictionary of values for the Kubernetes client and server versions.
        """
        version_json = self.do('version -o json', ignore_errors)
        return json.loads(version_json.decode())

    ###################################################################################
    #                                                                                 #
    # Class: JSONEncoder                                                              #
    #                                                                                 #
    ###################################################################################
    class JSONEncoder(json.JSONEncoder):
        """
        Custom JSONEncoder implementation used to handle the JSON serialization of Kubectl response objects.
        """

        def default(self, o):
            if isinstance(o, Kubectl.Resource):
                return o.as_dict()
            if isinstance(o, Kubectl.ApiResources):
                return o.as_dict()
            if isinstance(o, Kubectl.Metrics):
                return o.as_dict()
            else:
                return o.__dict__

    ###################################################################################
    #                                                                                 #
    # Class: ApiResources                                                             #
    #                                                                                 #
    ###################################################################################
    class ApiResources(object):
        """
        Class representing the response returned from the `kubectl api-resources` command.
        """

        class Keys(object):
            """
            Class defining static references to key value used in the ApiResources dictionary representation.
            """
            API_GROUP = 'apiGroup'
            NAME = 'name'
            NAMESPACED = 'namespaced'
            SHORT_NAME = 'shortname'
            VERBS = 'verbs'

        def __init__(self, api_resources_dict):
            """
            Constructor for ApiResources objects.

            :param api_resources_dict: The dictionary representing all API resources.
            """
            self._api_resources = api_resources_dict

        def is_available(self, kind):
            """
            Is the given kind available in the environment?

            :param kind: The kind whose availability should be checked.
            :return: True if the kind is available, otherwise False.
            """
            return kind in self._api_resources

        def get_api_group(self, kind):
            """
            Returns the API group for the given kind.

            :param kind: The kind whose API group value will be retrieved.
            :return: The API group of the given kind, or None if the given kind does not exist.
            """
            try:
                return self._api_resources[kind][self.Keys.API_GROUP]
            except KeyError:
                return None

        def get_name(self, kind):
            """
            Returns the API name for the given kind. This value can be used in "get" requests via Kubectl.

            Example
            -------
            kubectl = Kubectl()
            api_resources = kubectl.get_api_resources()
            deployments = kubectl.get_resources(api_resources.get_name(<kind>)

            :param kind: The kind whose name value will be retrieved.
            :return: The API name of the given kind, or None if the given kind does not exist.
            """
            try:
                return self._api_resources[kind][self.Keys.NAME]
            except KeyError:
                return None

        def is_namespaced(self, kind):
            """
            Is the given kind namespaced?

            :param kind: The kind whose namspaced designation will be returned.
            :return: True if the kind is namespaced, otherwise False or None if the kind does not exist.
            """
            try:
                return self._api_resources[kind][self.Keys.NAMESPACED]
            except KeyError:
                return None

        def get_short_name(self, kind):
            """
            Returns the short API name for the given kind.

            :param kind: The kind whose short name value will be retrieved.
            :return: The API short name of the given kind, or None if the kind does not exist.
            """
            try:
                return self._api_resources[kind][self.Keys.SHORT_NAME]
            except KeyError:
                return None

        def get_verbs(self, kind):
            """
            Returns the list of verbs defined for the given kind.

            :param kind: The kind whose verbs list will be returned.
            :return: The list of verbs defined for the given kind, or None if the kind does not exist.
            """
            try:
                return self._api_resources[kind][self.Keys.VERBS]
            except KeyError:
                return None

        def kind_as_dict(self, kind):
            """
            Returns the given kind in a Python-native dictionary representation.

            The returned dictionary is structured like so:
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

        def as_dict(self):
            """
            Returns a dictionary representation of the API resources.

            The returned dictionary is structured like so:
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
    # Class: Resource                                                                 #
    #                                                                                 #
    ###################################################################################
    class Resource(MutableMapping):
        """
        A MutableMapping implementation that holds the data defining a Kubernetes resource and provides
        methods for retrieving values.
        """

        class Keys(object):
            """
            Class providing static access to commonly used key names in Resource objects (list is not all-inclusive).
            """
            ADDRESSES = 'addresses'
            ANNOTATIONS = 'annotations'
            ANNOTATION_PROXY_BODY_SIZE = 'nginx.ingress.kubernetes.io/proxy-body-size'
            ANNOTATION_COMPONENT_NAME = 'sas.com/component-name'
            ANNOTATION_COMPONENT_VERSION = 'sas.com/component-version'
            ANNOTATION_VERSION = 'sas.com/version'
            API_VERSION = 'apiVersion'
            BACKEND = 'backend'
            CAPACITY = 'capacity'
            CLUSTER_IP = 'clusterIP'
            CONTAINER_STATUSES = 'containerStatuses'
            CONTAINERS = 'containers'
            CREATION_TIMESTAMP = 'creationTimestamp'
            DESTINATION = 'destination'
            ENV = 'env'
            GATEWAYS = 'gateways'
            GENERATION = 'generation'
            HTTP = 'http'
            HOST = 'host'
            HOSTS = 'hosts'
            HOST_IP = 'hostIP'
            IMAGE = 'image'
            IMAGES = 'images'
            INIT_CONTAINERS = 'initContainers'
            ITEMS = 'items'
            KIND = 'kind'
            LABEL_CAS_NODE_TYPE = 'cas-node-type'
            LABEL_CAS_SERVER = 'cas-server'
            LABEL_MANAGED_BY = 'app.kubernetes.io/managed-by'
            LABEL_PG_CLUSTER = 'pg-cluster'
            LABEL_PG_DEPLOYMENT_NAME = 'deployment-name'
            LABEL_PG_SERVICE_NAME = 'service-name'
            LABEL_SAS_DEPLOYMENT = 'sas.com/deployment'
            LABELS = 'labels'
            MATCH = 'match'
            MATCH_LABELS = 'matchLabels'
            METADATA = 'metadata'
            NAME = 'name'
            NAMESPACE = 'namespace'
            NODE_INFO = 'nodeInfo'
            NODE_NAME = 'nodeName'
            OWNER_REFERENCES = 'ownerReferences'
            PATH = 'path'
            PATHS = 'paths'
            PHASE = 'phase'
            POD_CIDR = 'podCIDR'
            POD_CIDRS = 'podCIDRs'
            POD_IP = 'podIP'
            POD_IPS = 'podIPs'
            PORTS = 'ports'
            READY = 'ready'
            RESOURCES = 'resources'
            RESOURCE_VERSION = 'resourceVersion'
            RESTART_COUNT = 'restartCount'
            ROUTE = 'route'
            RULES = 'rules'
            SELECTOR = 'selector'
            SELF_LINK = 'selfLink'
            SERVICE_PORT = 'servicePort'
            SERVICE_NAME = 'serviceName'
            SPEC = 'spec'
            START_TIME = 'startTime'
            STARTED = 'started'
            STATE = 'state'
            STATUS = 'status'
            TEMPLATE = 'template'
            UID = 'uid'

        class Kinds(object):
            """
            Class defining commonly used Kubernetes kind names for SAS deployments (list is not all-inclusive).

            All available kinds can be discovered by calling the Kubectl.get_api_resources() method.
            """
            CAS_DEPLOYMENT = 'CASDeployment'
            CRUNCHY_PG_BACKUP = 'Pgbackup'
            CRUNCHY_PG_CLUSTER = 'Pgcluster'
            CRUNCHY_PG_POLICY = 'Pgpolicy'
            CRUNCHY_PG_REPLICA = 'Pgreplica'
            CRUNCHY_PG_TASK = 'Pgtask'
            DEPLOYMENT = 'Deployment'
            ENDPOINT = 'Endpoint'
            INGRESS = 'Ingress'
            ISTIO_VIRTUAL_SERVICE = 'VirtualService'
            JOB = 'Job'
            NODE = 'Node'
            NODE_METRICS = 'NodeMetrics'
            POD = 'Pod'
            POD_METRICS = 'PodMetrics'
            REPLICA_SET = 'ReplicaSet'
            SERVICE = 'Service'
            STATEFUL_SET = 'StatefulSet'

        def __init__(self, resource):
            """
            Constructor for Resource class.

            :param resource: A dict, bytes, or str object representing the Kubernetes resource. An AttributeError
                             is raised if the provided resource is not an instance of dict, bytes, or str.
            """
            if isinstance(resource, dict):
                self._resource = resource
            elif isinstance(resource, bytes):
                self._resource = json.loads(resource.decode())
            elif isinstance(resource, str):
                self._resource = json.loads(resource)
            else:
                raise AttributeError(f'{self.__class__.__name__}."resource" must by of type [dict, bytes, str].')

        def __getitem__(self, key):
            """
            Implemented method for retrieving an item from the Resource data structure.

            :param key: The key of the item to retrieve.
            :return: The value mapped to the provided key.
            """
            return self._resource[key]

        def __setitem__(self, key, value):
            """
            Implemented method for setting a new key/value pair in the Resource data structure.

            :param key: The new key to add to the data structure.
            :param value: The value mapped to the given key.
            """
            self._resource[key] = value

        def __delitem__(self, key):
            """
            Implemented method for removing a key and value from the Resource data structure.

            :param key: The key to remove from the data structure.
            """
            del self._resource[key]

        def __iter__(self):
            """
            Implemented method for returning an iterator for the Resource data structure.

            :return: The iterator for this data structure.
            """
            return iter(self._resource)

        def __len__(self):
            """
            Implemented method for returning the length of the Resource data structure.

            :return: The length of the data structure.
            """
            return len(self._resource)

        def get_api_version(self):
            """
            Returns the 'apiVersion' value of this Resource.

            :return: This Resource's 'apiVersion' value.
            """
            return self._resource.get(self.Keys.API_VERSION)

        def get_kind(self):
            """
            Returns the 'kind' value of this Resource.

            :return: This Resource's 'kind' value.
            """
            return self._resource.get(self.Keys.KIND)

        def get_metadata(self):
            """
            Returns the 'metadata' dictionary for this Resource.

            :return: This Resource's 'metadata' dictionary.
            """
            return self._resource.get(self.Keys.METADATA)

        def get_metadata_value(self, key):
            """
            Returns the given key's value from the 'metadata' dictionary.

            :param key: The key of the value to return.
            :return: The value mapped to the given key, or None if the given key doesn't exist.
            """
            try:
                return self._resource[self.Keys.METADATA][key]
            except KeyError:
                return None

        def get_annotations(self):
            """
            Returns the dictionary of all annotations defined for this Resource.

            :return: A dictionary of all annotations defined for this Resource.
            """
            return self.get_metadata_value(self.Keys.ANNOTATIONS)

        def get_annotation(self, annotation):
            """
            Returns the value of the given annotation.

            :param annotation: The key of the annotation to retrieve.
            :return: The value mapped to the given annotation, or None if the given annotation doesn't exist.
            """
            annotations = self.get_annotations()
            if annotations is None:
                return None
            return annotations.get(annotation)

        def get_sas_component_name(self):
            """
            Returns the component name of the KubernetesResource.

            :return: This resource's component name, or None if the 'sas.com/component-name' annotation doesn't exist.
            """
            return self.get_annotation(self.Keys.ANNOTATION_COMPONENT_NAME)

        def get_sas_component_version(self):
            """
            Returns the component version of the KubernetesResource.

            :return: This resource's component version, or None if the 'sas.com/component-version'
                annotation doesn't exist.
            """
            return self.get_annotation(self.Keys.ANNOTATION_COMPONENT_VERSION)

        def get_sas_version(self):
            """
            returns the version of the KubernetesResource.

            :return: This resource's version, or None if the 'sas.com/version' annotation doesn't exist.
            """
            return self.get_annotation(self.Keys.ANNOTATION_VERSION)

        def get_creation_timestamp(self):
            """
            Returns the 'metadata.creationTimestamp' value for this Resource.

            :return: This Resource's 'metadata.creationTimestamp' value.
            """
            return self.get_metadata_value(self.Keys.CREATION_TIMESTAMP)

        def get_generation(self):
            """
            Returns the 'metadata.generation" value for this Resource.

            :return: This Resource's 'metadata.generation' value.
            """
            return self.get_metadata_value(self.Keys.GENERATION)

        def get_labels(self):
            """
            Returns the metadata labels for this Resource.

            :return: This resource's metadata labels.
            """
            return self.get_metadata_value(self.Keys.LABELS)

        def get_label(self, label_key):
            """
            Returns the value of the given metadata label key.

            :param label_key: The key of the metadata label to retrieve.
            :return: The value of the the given key, or None if the given key does not exist.
            """
            try:
                return self.get_labels()[label_key]
            except KeyError:
                return None

        def get_name(self):
            """
            Returns the 'metadata.name" value for this Resource.

            :return: This Resource's 'metadata.name' value.
            """
            return self.get_metadata_value(self.Keys.NAME)

        def get_namespace(self):
            """
            Returns the 'metadata.namespace" value for this Resource.

            :return: This Resource's 'metadata.namespace' value.
            """
            return self.get_metadata_value(self.Keys.NAMESPACE)

        def get_resource_version(self):
            """
            Returns the 'metadata.resourceVersion" value for this Resource.

            :return: This Resource's 'metadata.resourceVersion' value.
            """
            return self.get_metadata_value(self.Keys.RESOURCE_VERSION)

        def get_self_link(self):
            """
            Returns the 'metadata.selfLink" value for this Resource.

            :return: This Resource's 'metadata.selfLink' value.
            """
            return self.get_metadata_value(self.Keys.SELF_LINK)

        def get_uid(self):
            """
            Returns the 'metadata.uid" value for this Resource.

            :return: This Resource's 'metadata.uid' value.
            """
            return self.get_metadata_value(self.Keys.UID)

        def get_spec(self):
            """
            Returns the 'spec' dictionary for this Resource.

            :return: This Resource's 'spec' dictionary.
            """
            return self._resource.get(self.Keys.SPEC)

        def get_spec_value(self, key):
            """
            Returns the given key's value from the 'spec' dictionary.

            :param key: The key of the value to return.
            :return: The value mapped to the given key, or None if the given key doesn't exist.
            """
            try:
                return self._resource[self.Keys.SPEC][key]
            except KeyError:
                return None

        def get_status(self):
            """
            Returns the 'status' dictionary for this Resource.

            :return: This Resource's 'status' dictionary.
            """
            return self._resource.get(self.Keys.STATUS)

        def get_status_value(self, key):
            """
            Returns the given key's value from the 'status' dictionary.

            :param key: The key of the value to return.
            :return: The value mapped to the given key, or None if the given key doesn't exist.
            """
            try:
                return self._resource[self.Keys.STATUS][key]
            except KeyError:
                return None

        def as_dict(self):
            """
            Returns this KubernetesResource as a native 'dict' object.

            :return: A native 'dict' version of this Kubernetes resource.
            """
            return self._resource

    ###################################################################################
    #                                                                                 #
    # Class: Metrics                                                                  #
    #                                                                                 #
    ###################################################################################
    class Metrics(object):
        """
        Class representing the response from `kubectl top <nodes/pods>` commands.
        """

        class Keys(object):
            """
            Class defining static references used in the dictionary representation of this object.
            """
            CPU_CORES = 'cpuCores'
            CPU_USED = 'cpuUsed'
            MEMORY_BYTES = 'memoryBytes'
            MEMORY_USED = 'memoryUsed'

        def __init__(self, metrics_dict):
            """
            Constructor for Metrics objects.

            :param metrics_dict: Dictionary defining the metrics for the requested resource.
            """
            self._metrics = metrics_dict

        def get_cpu_cores(self, name):
            """
            Returns the CPU used in cores for the given resource.

            :param name: The name of the pod/node.
            :return: CPU used in cores for the given pod/node, or None if the given node/pod isn't defined.
            """
            try:
                return self._metrics[name][self.Keys.CPU_CORES]
            except KeyError:
                return None

        def get_cpu_used(self, name):
            """
            Returns the CPU percentage used for the given node.

            NOTE: Will always return None for pods.

            :param name: The name of the resource.
            :return: The CPU percentage used for nodes, None for pods or if given Node isn't defined.
            """
            try:
                return self._metrics[name][self.Keys.CPU_USED]
            except KeyError:
                return None

        def get_memory_bytes(self, name):
            """
            Returns the memory used in bytes for the given pod/node.

            :param name: The name of the pod/node.
            :return: The memory used in bytes for the given pod/node, or None if the given node/pod isn't defined.
            """
            try:
                return self._metrics[name][self.Keys.MEMORY_BYTES]
            except KeyError:
                return None

        def get_memory_used(self, name):
            """
            Returns the memory percentage used for the given node.

            NOTE: Will always return None for pods.

            :param name: The name of the resource.
            :return: The memory percentage used for nodes, None for pods or if the given Node isn't defined.
            """
            try:
                return self._metrics[name][self.Keys.CPU_USED]
            except KeyError:
                return None

        def resource_metrics_as_dict(self, name):
            """
            Returns a dictionary representation of the metrics defined for the given resource.

            The returned dictionary is structured like so:
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

        def as_dict(self):
            """
            Returns a dictionary representation of this object.

            The returned dictionary is structured like so:
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
