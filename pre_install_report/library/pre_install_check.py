#!/usr/bin/env python3
####################################################################
# ### pre_install_check.py                                       ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

import re
from time import gmtime, strftime
import datetime
import pprint
import sys
import os
import platform
import subprocess
from subprocess import CalledProcessError


# import pint to add, compare memory
from pint import UnitRegistry

from pre_install_report.library.utils import viya_constants
from pre_install_report.library.pre_install_check_permissions import PreCheckPermissions
from pre_install_report.library.pre_install_utils import PreCheckUtils
from viya_arkcd_library.k8s.sas_kubectl_interface import KubectlInterface
from viya_arkcd_library.jinja2.sas_jinja2 import Jinja2TemplateRenderer
from viya_arkcd_library.logging import ViyaARKCDLogger


PRP = pprint.PrettyPrinter(indent=4)
# Error Messages
CONFIG_ERROR = "Unable to read configuration file. Make " \
               "sure that kubectl" \
               " is properly configured and the KUBECONFIG " \
               "environment variable has a valid value"
KUBECONF_ERROR = "KUBECONFIG environment var must be set for the script " \
                "to access the Kubernetes cluster."

CHECK_NAMESPACE = ' Check available permissions in namespace and if it is valid: '
# command line return codes #
_SUCCESS_RC_ = 0
_BAD_OPT_RC_ = 1
_BAD_ENV_RC_ = 2
_BAD_CONFIG_RC_ = 3
_BAD_CONFIG_JSON_RC_ = 4
_CONNECTION_ERROR_RC_ = 5
_NAMESPACE_NOT_FOUND_RC_ = 6

# templates for output file names #
_REPORT_FILE_NAME_TMPL_ = "viya_pre_install_report_{}.html"
_REPORT_LOG_NAME_TMPL_ = "viya_pre_install_log_{}.log"
_FILE_TIMESTAMP_TMPL_ = "%Y-%m-%dT%H_%M_%S"

# set timestamp for report file
file_timestamp = datetime.datetime.now().strftime(_FILE_TIMESTAMP_TMPL_)

# templates for osuppported releases of Kubelet Versions #
releases = (viya_constants.KUBELET_VERSION_14,
            viya_constants.KUBELET_VERSION_15,
            viya_constants.KUBELET_VERSION_16,
            viya_constants.KUBELET_VERSION_17)


class ViyaPreInstallCheck():
    """
    A ViyaPreInstallCheck object represents a summary of resources currently detected on the target Kubernetes
    environment.

    A cache of Kubernetes resources are stored for access via the API.

    The gathered data can be written to disk as an HTML report and a JSON file containing the gathered data.
    """
    def __init__(self, sas_logger: ViyaARKCDLogger):
        """
        Constructor for ViyaPreInstallCheck object.
        """
        self._report_data = None
        self._kubectl: KubectlInterface = None
        self.sas_logger = sas_logger
        self.logger = self.sas_logger.get_logger()

    def check_details(self, kubectl, ingress_port, ingress_host, ingress_controller, output_dir):
        # Register Python Package Pint definitions

        self._kubectl = kubectl
        name_space = kubectl.get_namespace()
        self.logger.info("names_space: {} ".format(name_space))

        current_dir = os.path.dirname(os.path.abspath(__file__))
        datafile = os.path.join(current_dir, "utils" + os.sep + 'kdefinitions.txt')

        ureg = UnitRegistry(datafile)
        quantity_ = ureg.Quantity
        configs_data = self.get_config_info()
        cluster_info = self._get_master_json()
        master_data = self._check_master(cluster_info)
        namespace_data = []
        namespace_data = self._check_available_namespaces(self._get_namespaces_json(), namespace_data)

        storage_json = self._get_storage_json()
        storage_data = self._get_storage_classes(storage_json)

        nodes_json = self._get_nodes_json()
        nodes_data = self.get_nested_nodes_info(nodes_json)

        global_data = []
        global_data = self.evaluate_nodes(nodes_data, global_data, releases, cluster_info, quantity_)

        cluster_admin_permission_data, namespace_admin_permission_data, \
            ingress_data, ns_admin_permission_aggregate, \
            cluster_admin_permission_aggregate = self._check_permissions(ingress_controller, str(ingress_host),
                                                                         str(ingress_port))

        self.generate_report(global_data, master_data, configs_data,
                             storage_data,
                             namespace_data, cluster_admin_permission_data,
                             namespace_admin_permission_data,
                             ingress_data,
                             ns_admin_permission_aggregate,
                             cluster_admin_permission_aggregate,
                             output_dir)
        return

    def _read_environment_var(self, env_var):
        """
        This method verifies that the KUBECONFIG environment variable is set.

        :param env_var: Environment variable to check
        """
        try:
            value_env_var = os.environ[env_var]
        except Exception:
            self.logger.exception("CalledProcessorError")
            print(KUBECONF_ERROR)
            sys.exit(_BAD_ENV_RC_)

        return value_env_var

    def _get_nested_info(self, nested_nodes, extracted_nodes, search_key):

        try:
            for adtnode in nested_nodes:
                keys = adtnode.keys()
                for key in keys:
                    if key in search_key:
                        addrnode = [adtnode[key]]
                        extracted_nodes.append(addrnode)
            self.logger.debug("extracted nodes: {}".format(pprint.pformat(extracted_nodes)))
            return extracted_nodes
        except KeyError:
            return extracted_nodes

    def _get_config_current_context(self, config_json, configs_data):
        """
        Retrieve the current context from kubeconfig file.

        :config_json: json retrieved from the kubectl config view command
        :configs_data: list to which current context  list will be appended
        :return:    updated configs_data list
        """
        current_context_data = []

        if config_json:
            try:
                if len(config_json['current-context']) > 0:
                    config_data = {'currentcontext': config_json['current-context']}
                else:
                    config_data = {'currentcontext': CONFIG_ERROR}
            except KeyError:
                config_data = {'currentcontext': viya_constants.KEY_NOT_FOUND}
                print(CONFIG_ERROR)
                sys.exit(_BAD_CONFIG_JSON_RC_)

            current_context_data.append(config_data)

        self.logger.debug("current_context_data: " + pprint.pformat(current_context_data))

        configs_data.append(current_context_data)
        return configs_data

    def _get_config_contexts(self, config_json, configs_data):
        """
        Retrieve the available context name , cluster name, and cluster user from the kubectl command config view.

        :config_json: json retrieved from the kubectl config view command
        :configs_data: list to which current context  list will be appended
        :return:    updated configs_data list
        """

        context_data = []
        if config_json:
            try:
                for config in config_json['contexts']:
                    config_data = {}
                    try:
                        config_data['contextName'] = config['name']
                    except KeyError:
                        config_data['contextName'] = viya_constants.KEY_NOT_FOUND
                    try:
                        config_data['cluster'] = config['context']['cluster']
                    except KeyError:
                        config_data['cluster'] = viya_constants.KEY_NOT_FOUND
                    try:
                        config_data['clusteruser'] = config['context']['user']
                    except KeyError:
                        config_data['clusteruser'] = viya_constants.KEY_NOT_FOUND
                    context_data.append(config_data)
            except TypeError as error:
                self.logger.exception("TypeError {}".format(str(error)))
                print(CONFIG_ERROR)
                sys.exit(_BAD_CONFIG_JSON_RC_)

        self.logger.debug("context_data: {}".format(pprint.pformat(context_data)))

        configs_data.append(context_data)
        return configs_data

    def _get_config_clusters(self, config_json, configs_data):
        """
        Retrieve the available cluster and associated server names kubectl command config view.

        :config_json: json retrieved from the kubectl config view command
        :configs_data: list to which current context  list will be appended
        :return:    updated configs_data list
        """
        cluster_data = []

        if config_json:
            try:
                for config in config_json['clusters']:
                    config_data = {}
                    try:
                        config_data['clustername'] = config['name']
                    except KeyError:
                        config_data['clustername'] = viya_constants.KEY_NOT_FOUND
                    try:
                        config_data['server'] = config['cluster']['server']
                    except KeyError:
                        config_data['server'] = viya_constants.KEY_NOT_FOUND

                    cluster_data.append(config_data)
            except TypeError as error:
                self.logger.exception("TypeError".format(str(error)))
                print(CONFIG_ERROR)
                sys.exit(_BAD_CONFIG_JSON_RC_)

        self.logger.debug("cluster data: {}".format(pprint.pformat(cluster_data)))
        configs_data.append(cluster_data)
        return configs_data

    def _get_config_users(self, config_json, configs_data):
        """
        Retrieve any usernames from the from the kubectl command config view.

        :config_json: json retrieved from the kubectl config view command
        :configs_data: list to which current context  list will be appended
        :return:    updated configs_data list
        """
        cluster_data = []

        if config_json:
            try:
                for config in config_json['users']:
                    try:
                        config = {'username': config['name']}
                    except KeyError:
                        config = {'username': viya_constants.KEY_NOT_FOUND}
                    cluster_data.append(config)
            except TypeError as e:
                self.logger.exception("TypeError {}: ".format(str(e)))
                print(CONFIG_ERROR)
                sys.exit(_BAD_CONFIG_JSON_RC_)

        self.logger.debug("cluster_data: {}".format(pprint.pformat(cluster_data)))

        configs_data.append(cluster_data)
        return configs_data

    def _get_nodes_json(self):
        """
        Retrieve the nodes information from the Kubernetes cluster in json format.

        return:  nodes information in json format
        """
        nodes_json = self._get_raw_json("nodes")

        return nodes_json

    def _get_namespaces_json(self):
        """
        Retrieve the namespaces information from Kubernetes in json format.

        return:  namespaces information in json format
        """
        namespace_json = self._get_raw_json("namespaces")

        return namespace_json

    def _get_storage_json(self):
        """
        Retrieve the storage class information from Kubernetes in json format

        return:  storage class information in json format
        """
        storage_json = self._get_raw_json("storageclass")
        return storage_json

    def _get_storage_classes(self, storage_json):
        """
        Parse the storage class information into dictionary objects in a list

        storage_json:  json containing storage class information
        return:  list of dictionary objects detailing storage class information
        """
        storage_nodes = []
        default_cnt = 0

        if storage_json:
            for node in storage_json['items']:
                node_data = {}
                node_data['storageClassNameName'] = node['metadata']['name']

                try:
                    annotated_lines = node['metadata']['annotations']
                    for line in annotated_lines:
                        if "storageclass.beta.kubernetes.io/is-default-class" in line:
                            # node['metadata']['annotations']['storageclass.beta.kubernetes.io/is-default-class']
                            node_data['default'] = "true"
                            default_cnt += 1
                        else:
                            node_data['default'] = "false"
                    storage_nodes.append(node_data)
                except KeyError as e:
                    self.logger.exception("KeyError {}".format(str(e)))

        self.logger.debug("storage nodes: {}".format(pprint.pformat(storage_nodes)))
        storage_items = int(len(storage_nodes))
        self.logger.debug("Num of storage classes: {}".format(storage_items))

        storage_nodes = self._check_storage_classes(default_cnt, storage_nodes)
        return storage_nodes

    def _get_master_json(self):
        """
        Retrieve  the cluster info from Kubernetes

        return: Output from and rc from cluster-info command
        """
        kubectl = self._kubectl
        data = None
        try:
            data = kubectl.cluster_info()
        except CalledProcessError as proc_error:
            self.logger.exception('cluster-info return_code = {}'.format(str(proc_error.returncode)))
            if proc_error.returncode != 1:
                data = proc_error.output
            return str(data)
        self._read_cluster_info_output(data)
        return str(data)

    def _read_cluster_info_output(self, data):
        command = "cat "
        data = None
        file_name = "temp_cluste_info.txt"
        try:
            file = open(file_name, "w+")
            file.writelines(str(data))
            file.close()
        except Exception:
            self.logger.exception("Unable to save to {}".format(file_name))
            return data

        if platform.system() == "Windows":
            command = "type "
        try:
            data = subprocess.check_output(command + file_name, shell=True, universal_newlines=True)
        except CalledProcessError:
            self.logger.exception("Windows file_name failed {}".format(file_name))
            return data
        self._delete_temp_file(file_name)
        return str(data)

    def _delete_temp_file(self, file_name):
        if os.path.exists(file_name):
            os.remove(file_name)

    def _check_permissions(self, ingress_controller, ingress_host, ingress_port):
        """
        Check if permissions are adequate to complete Viya deployment with cluster admin
        and namespace admin lveles of access to cluster resources

        ingress_controller:  nginx/istio or other supported controller
        ingress_host: user specified host for ingress controller
        ingress_port: user specified  port for  ingress controller
        return: dictionary objects with the results of permissions checking
        """
        pre_check_utils_params = {}
        pre_check_utils_params[viya_constants.KUBECTL] = self._kubectl
        pre_check_utils_params["logger"] = self.sas_logger
        utils = PreCheckUtils(pre_check_utils_params)

        params = {}
        params[viya_constants.INGRESS_CONTROLLER] = ingress_controller
        params[viya_constants.INGRESS_HOST] = ingress_host
        params[viya_constants.INGRESS_PORT] = ingress_port
        params[viya_constants.PERM_CLASS] = utils
        params['logger'] = self.sas_logger

        # initialize the PreCheckPermissions object
        perms = PreCheckPermissions(params)
        namespace = self._kubectl.get_namespace()

        perms.check_sample_application()
        perms.check_sample_ingress()
        perms.check_deploy_crd()
        perms.check_rbac_role()
        perms.check_create_custom_resource()
        perms.check_get_custom_resource(namespace, )
        perms.check_delete_custom_resource()
        perms.check_rbac_delete_role()
        perms.check_sample_response()
        perms.check_delete_crd()
        perms.check_delete_sample_application()
        perms.check_delete_sample_ingress()

        return perms.get_cluster_admin_permission_data(), perms.get_namespace_admin_permission_data(),\
            perms.get_ingress_data(), perms.get_namespace_admin_permission_aggregate(), \
            perms.get_cluster_admin_permission_aggregate()

    def _escape_ansi(self, line):
        """
        Remove escape characters from input string

        line: input string
        return:  string without escape sequences
        """
        return re.sub('[^.,:/A-Za-z0-9]+', ' ', line).strip()

    def _check_master(self, cluster_info):
        """
        Parse the output from cluster info and return master info

        cluster_info: output from cluster info
        return: return list with master nodes detected
        """
        master_data = []
        master_nodes = {}
        masters = int(1)

        if cluster_info:
            # cluster_strings = cluster_info.splitlines()
            cluster_strings = str(cluster_info).split("\\n", maxsplit=1)
            master = str(cluster_strings[0])
            index = master.find("Kubernetes")
            no_color = self._escape_ansi(line=master[index:])
            master_nodes.update({'totalMasters': str(1)})
            if masters >= viya_constants.NUMBER_OF_MASTER_NODES:
                master_nodes.update({'status': 0})
                master_nodes.update({'issue': 'Issues Found: ' + str(0)})
                if cluster_strings[0]:
                    master_nodes.update({'firstFailure': str(no_color)})
        else:
            master_nodes.update({'totalMasters': str(viya_constants.SET) + ': 0, ' +
                                 str(viya_constants.EXPECTED) +
                                 ': Minimum ' +
                                 str(viya_constants.NUMBER_OF_MASTER_NODES)})
            master_nodes.update({'status': 1})
            master_nodes.update({'issue': master_nodes['totalMasters'] + ', ' + 'Issues Found: ' + str(1)})
            master_nodes.update({'firstFailure': 'Cluster information not available. Check permissions.'})

        master_data.append(master_nodes)
        self.logger.debug("master_data {}".format(pprint.pformat(master_data)))
        return master_data

    def _calculate_potential_workers(self, nodes_data):
        """
        Identify worker nodes in the cluster

        nodes_data: list of dict objects with node details
        return: number of sworker nodes detected.
        """
        workers = 0
        for node in nodes_data:
            if node['taint'] not in "NoSchedule":
                workers += 1
        return workers

    def _check_workers(self, global_data, nodes_data):
        """
        Check list of worker nodes information and calculate the total number of worker nodes
        and update it in the global data list.

        global_data:  list that contains lobal data about nodes
        nodes_data:  list of dict objects, each with node information
        return: updated global_data list with total number of worker nodes.
        """
        global_nodes = {}
        workers = self._calculate_potential_workers(nodes_data)

        global_nodes.update({'totalWorkers': str(workers) + ': ' +
                             str(viya_constants.SET + ': ' +
                             str(workers) + ', ' +
                             str(viya_constants.EXPECTED) +
                                 ': Minimum ' +
                                 str(viya_constants.NUMBER_OF_WORKER_NODES))})

        if workers < viya_constants.NUMBER_OF_WORKER_NODES:
            global_nodes.update({'status': 1})
            global_nodes.update({'issue': 'Issues Found: ' + str(1)})
            global_nodes.update({'firstFailure':
                                 str(viya_constants.SET + ': ' +
                                     str(workers) + ', ' +
                                     str(viya_constants.EXPECTED) +
                                     ': Minimum ' +
                                     str(viya_constants.NUMBER_OF_WORKER_NODES) +
                                     " \nCheck SAS Viya Documentation")})

        else:
            global_nodes.update({'status': 0})
            global_nodes.update({'issue': 'Issues Found: ' + str(0)})
            global_nodes.update(
                {'firstFailure': str(viya_constants.SET +
                                     ': ' + str(workers)
                                     + ', ' + str(viya_constants.EXPECTED)
                                     + ': ' +
                                     str(viya_constants.NUMBER_OF_WORKER_NODES))})
        global_data.append(global_nodes)
        self.logger.debug("global_nodes: {}".format(pprint.pformat(global_nodes)))
        return global_data

    def _set_time(self, global_data):
        """Set the current timestamp for the report in the global data list

        global_data: List to be updated
        return:  global_data list updated with current time to be added to the report
        """
        global_nodes = {}
        time_string = strftime("%m/%d/%Y, %H:%M:%S", gmtime())
        time_string = "GMT " + time_string

        global_nodes.update({'timestamp': str(time_string)})
        global_data.append(global_nodes)

        self.logger.debug("global data{} time{}".format(pprint.pformat(global_data), time_string))
        return global_data

    def _check_cpu_errors(self, global_data, total_alloc_cpu_cores, aggregate_cpu_failures):
        """
        Check if the aggregate allocatable CPUs across all worker nodes meets SAS total cpu requirements

        global_data: list with global data about worker nodes retrieved
        total_alloc_cpu_cores:  total cpu cores across all worker nodes calculated
        aggregate_cpu_failures:  count of cpu failures
        """
        aggregate_cpu_data = {}
        msg = ''
        error_msg = ""
        info_msg = str(viya_constants.EXPECTED) + ': ' + \
            viya_constants.TOTAL_CPU_CORES + \
            ', Calculated: ' + str(total_alloc_cpu_cores)

        if total_alloc_cpu_cores < int(viya_constants.TOTAL_CPU_CORES):
            aggregate_cpu_failures += 1
            # Check for combined cpu_core capacity of the Kubernetes nodes in cluster
        error_msg = viya_constants.SET + ': ' + \
            str(total_alloc_cpu_cores) + ', ' + \
            str(viya_constants.EXPECTED) + ': ' + \
            viya_constants.TOTAL_CPU_CORES
        if aggregate_cpu_failures > 0:
            msg = error_msg
        else:
            msg = info_msg
        aggregate_cpu_data.update({'aggregate_cpu_failures': msg + ', Issues Found: ' + str(aggregate_cpu_failures)})

        global_data.append(aggregate_cpu_data)

        return global_data

    def _check_memory_errors(self, global_data, total_allocatable_memory, quantity_, aggregate_memory_failures):
        """
        Check aggregate allocatable memory across all worker nodes against SAS total memory requirement in worker nodes

        global_data: list with global data about worker nodes retrieved
        total_allocatable_memory:  total allocatable memory calculated across all worker nodes calculated
        aggregate_memory_failures:  count of memory failures
        """
        aggregate_memory_data = {}
        error_msg = ""
        msg = ''
        info_msg = str(viya_constants.EXPECTED) + ': ' + \
            viya_constants.TOTAL_MEMORY + \
            ', Calculated: ' + str(total_allocatable_memory.to('Gi'))

        if total_allocatable_memory < quantity_(viya_constants.TOTAL_MEMORY):
            aggregate_memory_failures += 1
            # Check for combined cpu_core capacity of the Kubernetes nodes in cluster
        error_msg = viya_constants.SET + ': ' + \
            str(total_allocatable_memory.to('Gi')) + ', ' + \
            str(viya_constants.EXPECTED) + ': ' + \
            viya_constants.TOTAL_MEMORY

        if aggregate_memory_failures > 0:
            msg = error_msg
        else:
            msg = info_msg

        aggregate_memory_data.update({'aggregate_memory_failures': msg +
                                      ', Issues Found: ' + str(aggregate_memory_failures)})
        global_data.append(aggregate_memory_data)
        return global_data

    def _check_kubelet_errors(self, global_data, aggregate_kubelet_failures):
        """
        Check kubelet version against SAS kubelet version requirements

        global_data: list with global data about worker nodes retrieved
        aggregate_kubelet_failures:  count of kubelet version errors
        return: updated global data about worker nodes retrieved
        """
        aggregate_kubelet_data = {}
        aggregate_kubelet_data.update({'aggregate_kubelet_failures': str(aggregate_kubelet_failures)})
        if aggregate_kubelet_failures > 0:
            aggregate_kubelet_data.update({'aggregate_kubelet_failures':
                                           'Check Kubelet Version on nodes.' +
                                           ' Issues Found: ' + str(aggregate_kubelet_failures)})
        global_data.append(aggregate_kubelet_data)

        return global_data

    def _get_raw_json(self, k8s_resource):
        """
        Retrieve kubernetes resource in json format

        k8s_resource: Kubernetes resource iformation to retrieve
        return: information as raw json
        """
        kubectl = self._kubectl
        raw_json = None
        return_code = 0
        try:
            raw_json = kubectl.get_resources(k8s_resource, True)
        except CalledProcessError as cpe:
            return_code = str(cpe.returncode)
            self.logger.exception("resource {} return code".format(str(k8s_resource), str(return_code)))
            return raw_json

        self.logger.info("resource {} raw JSON {}".format(str(k8s_resource), str(raw_json)))
        assert isinstance(raw_json, object)
        return raw_json

    def _check_available_namespaces(self, namespaces_json, namespace_data):
        """Parse namespaces in input json

        namespaces_json: json with namespace information
        namespace_data: list with namespaces json
        return:  dictionary objects with namespace information updtaed in the namespace_data list
        """
        node_data = {}
        namespaces_str = ""

        if namespaces_json:
            for node in namespaces_json['items']:
                namespaces_str = namespaces_str + str(node['metadata']['name']) + ", \n"

        node_data['namespaces'] = namespaces_str
        namespace_data.append(node_data)
        return namespace_data

    def _check_storage_classes(self, default_cnt, storage_nodes):
        """
        Check Storage classes for not more than a single default storage class. Make sure there is at least one
        storge classs is present

        default_cnt: count of default storage classes
        storage_nodes: list of dict objcts with storage class information
        return:  list if dictionary objects with updated storage class information
        """
        aggregate_storage_failures = 0

        for node in storage_nodes:

            if int(default_cnt) > 1 and node['default'] == "true":
                aggregate_storage_failures += 1
                node.update({'status': 1})
                node.update({'issue': 'Issues Found: ' + str(1)})
                node.update(dict(firstFailure=viya_constants.SET
                                 + ': Multiple Default Storage Class found, '
                                 + str(viya_constants.EXPECTED)
                                 + ": Minimum 1"))
            else:
                node.update({'status': 0})
                node.update({'issue': 'Issues Found: ' + str(0)})
                node.update({'firstFailure': str("Issues Found: ") + str(aggregate_storage_failures)})

        storage_global = []
        storage_issue_data = {}
        if len(storage_nodes) < 1:
            aggregate_storage_failures += 1
        storage_issue_data['Issues'] = \
            str(viya_constants.SET) + \
            ': ' + str(len(storage_nodes)) + ', ' + \
            str(viya_constants.EXPECTED) + \
            ': Minimum 1' + ', ' \
            'Issues Found: ' + str(aggregate_storage_failures)
        storage_global.append(storage_issue_data)
        storage_global.append(storage_nodes)

        self.logger.debug("storage global {}".format(pprint.pformat(storage_global)))
        return storage_global

    def evaluate_nodes(self, nodes_data, global_data, releases, cluster_info, quantity_):
        """
        Parse the nodes information in list of dict objects and verify against SAS Specifications

        nodes_data: list dict object with node details
        global_data: list of dictionary object with global data for nodes
        return:  return ist of dictionary objects with updated information and status
        """

        aggregate_cpu_failures = int(0)
        aggregate_memory_failures = int(0)
        aggregate_kubelet_failures = int(0)
        total_cpu_cores = int(0)
        total_memory = quantity_("0Ki")
        total_allocatable_memory = quantity_("0Ki")
        for node in nodes_data:
            try:
                alloc_cpu_cores = int(node['allocatablecpu'])
            except ValueError:
                # CPU is measured in units called millicores. Each node in the cluster introspects the operating system
                # to determine the amount of CPU cores on the node and then multiples that value by 1000 to express
                # its total capacity.
                alloc_cpu_cores = int(str(node['allocatablecpu']).rstrip('m'))/1000
            # Node tainted with NoSchedule
            taint_effect = str(node['taint'])
            role = "non_worker"
            if taint_effect not in "NoSchedule":
                role = "worker"
            kubeletversion = str(node['kubeletversion'])
            alloc_memory = str(node['allocatableMemory'])
            total_memory = total_memory + quantity_(str(node['memory']))
            total_allocatable_memory = total_allocatable_memory + quantity_(alloc_memory)

            if role == 'worker':
                total_cpu_cores = total_cpu_cores + alloc_cpu_cores
                if alloc_cpu_cores >= int(viya_constants.MIN_WORKER_ALLOCATABLE_CPU):
                    self._set_status(0, node, 'cpu')
                else:
                    # may be master node
                    self._set_status(1, node, 'cpu')
                    # aggregate_all_failures += 1
                    aggregate_cpu_failures += 1
                    # TBD Check for minimum cpu_core per worked node.. What is mimimum? Set to 2 for now.
                    node['error']['cpu'] = viya_constants.SET + ': ' + \
                        str(alloc_cpu_cores) + ', ' + \
                        str(viya_constants.EXPECTED) + ': ' + \
                        viya_constants.MIN_WORKER_ALLOCATABLE_CPU

                if quantity_(alloc_memory) >= quantity_(viya_constants.MIN_ALLOCATABLE_WORKER_MEMORY):
                    self._set_status(0, node, 'allocatableMemory')
                else:
                    self._set_status(1, node, 'allocatableMemory')
                    node['error']['allocatableMemory'] = viya_constants.SET + \
                        ': ' + str(alloc_memory) + ', ' + \
                        str(viya_constants.EXPECTED) + ': ' + \
                        viya_constants.MIN_ALLOCATABLE_WORKER_MEMORY
                    aggregate_memory_failures += 1

            release_split = self.split_release(kubeletversion, '.', 2)
            if release_split in releases:
                self._set_status(0, node, 'kubeletversion')
            else:
                self._set_status(1, node, 'kubeletversion')
                node['error']['kubeletversion'] = viya_constants.SET + ': ' + \
                    kubeletversion + ', ' + \
                    str(viya_constants.EXPECTED) + ': ' + \
                    viya_constants.KUBELET_VERSION_14 \
                    + ' to ' + viya_constants.KUBELET_VERSION_17

                aggregate_kubelet_failures += 1
                self.logger.debug("node {} ".format(pprint.pformat(node)))
        global_data = self._check_workers(global_data, nodes_data)
        global_data = self._set_time(global_data)
        global_data = self._check_cpu_errors(global_data, total_cpu_cores, aggregate_cpu_failures)
        global_data = self._check_memory_errors(global_data, total_allocatable_memory, quantity_,
                                                aggregate_memory_failures)
        self._calculate_potential_workers(nodes_data)
        global_data = self._check_kubelet_errors(global_data, aggregate_kubelet_failures)

        global_data.append(nodes_data)
        self.logger.debug("nodes_data {}".format(pprint.pformat(nodes_data)))
        return global_data

    def _set_status(self, status, node, key):
        """Set the status flag on dictionary object with node details - to indicate compliance with
        cpu, memory kubelet version requirements

        status: status to be set on dict objectwith node details
        node: node dictionary object
        return:  return dictionary object with updated node status information
        """
        if status != 0:
            node.update({'status': status})
            node.update({'firstFailure': str("FAIL: " + key)})

        return node

    def get_nested_nodes_info(self, nodes_json):
        """
        Parse the json to load node information into a list of dictionary objects

        nodes_json:  nodes information in json format returned by kubectl
        return: list dictionary object with nodes information
        """

        nodes_data = []

        if nodes_json:
            for node in nodes_json['items']:
                node_data = {'error': {}, 'nodeName': node['metadata']['name'],
                             'cpu': node['status']['capacity']['cpu']}

                node_data['memory'] = node['status']['capacity']['memory']
                node_data['allocatableephemeral'] = node['status']['allocatable']['ephemeral-storage']
                node_data['allocatablecpu'] = node['status']['allocatable']['cpu']
                node_data['allocatableMemory'] = node['status']['allocatable']['memory']
                node_data['podscapacity'] = node['status']['capacity']['pods']
                node_data['kubeletversion'] = node['status']['nodeInfo']['kubeletVersion']
                node_data['containerRuntimeVersion'] = node['status']['nodeInfo']['containerRuntimeVersion']
                node_data['kernelVersion'] = node['status']['nodeInfo']['kernelVersion']
                node_data['osImage'] = node['status']['nodeInfo']['osImage']
                node_data['status'] = int(0)
                node_data['firstFailure'] = 'PASS'

                addresses = (node['status']['addresses'])
                address_type = []
                address_addr = []
                address_type = self._get_nested_info(addresses, address_type, 'type')
                address_addr = self._get_nested_info(addresses, address_addr, 'address')

                try:
                    taint_types = node['spec']['taints']
                    for tnode in taint_types:
                        taint_keys = tnode.keys()
                        for key in taint_keys:
                            if tnode[key] in 'NoSchedule':
                                node_data['taint'] = tnode[key]
                except KeyError:
                    node_data['taint'] = viya_constants.KEY_NOT_FOUND
                addr_len = len(address_type)
                for j in range(addr_len):
                    addr_t = str(address_type[j][0])
                    addr_a = str(address_addr[j][0])
                    node_data[addr_t] = addr_a

                conditions = (node['status']['conditions'])
                conditions_type = []
                conditions_status = []
                conditions_type = self._get_nested_info(conditions, conditions_type, 'type')
                conditions_status = self._get_nested_info(conditions, conditions_status, 'status')
                type_length = len(conditions_type)
                for i in range(type_length):
                    var1 = str(conditions_type[i][0])
                    var2 = str(conditions_status[i][0])
                    node_data[var1] = var2

                self.logger.debug("node data {}".format(pprint.pformat(node_data)))
                if node_data['taint'] not in "NoSchedule":
                    nodes_data.append(node_data)

        self.logger.debug("nodes_data {}".format(pprint.pformat(nodes_data)))
        return nodes_data

    def _get_config_json(self):
        """
        Retrieve  configuration information in json format

        return: configuration information in json format and return code from kubectl
        """
        kubectl = self._kubectl
        config_json = None
        return_code = 0
        try:
            config_json = kubectl.config_view(False)
        except CalledProcessError as cpe:
            return_code = cpe.returncode
            self.logger.exception("CalledProcessorError rc {}".format(str(return_code)))
            config_json = None

        self.logger.debug("config view JSON{} return_code{}".format(str(config_json), str(return_code)))
        return config_json, return_code

    def split_release(self, strng, sep, pos):
        """Splits the kubelet version release string """
        strng = strng.split(sep)
        return sep.join(strng[:pos])

    def get_config_info(self):
        """
        Parse the output all the information retrieved by kubectl config view command.

        return: A list of dictionary objects with config information
        """
        configs_data = []
        config_json, return_code = self._get_config_json()

        if return_code != 0:
            print(CONFIG_ERROR)
            sys.exit(_BAD_CONFIG_RC_)
        else:
            configs_data = self._get_config_current_context(config_json, configs_data)
            configs_data = self._get_config_contexts(config_json, configs_data)
            configs_data = self._get_config_clusters(config_json, configs_data)
            configs_data = self._get_config_users(config_json, configs_data)

        self.logger.debug("configs_data {}".format(configs_data))
        return configs_data

    def generate_report(self,
                        global_data,
                        master_data,
                        configs_data,
                        storage_data,
                        namespace_data,
                        cluster_admin_permission_data,
                        namespace_admin_permission_data,
                        ingress_data,
                        ns_admin_permission_aggregate,
                        cluster_admin_permission_aggregate,
                        output_directory=""):
        """
        Generate an HTML report with all the node and storage class details gathered in multiple lists.

        return: A list of dictionary objects with config information
        """
        # make sure path is valid #
        if output_directory != "" and not output_directory.endswith(os.sep):
            output_directory = output_directory + os.sep
        report_file_path = output_directory + _REPORT_FILE_NAME_TMPL_.format(file_timestamp)
        templates_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep + ".." \
            + os.sep + "templates" + os.sep

        template_renderer = Jinja2TemplateRenderer(templates_dir=templates_dir)
        report_file_path = \
            template_renderer.as_html(
                                   "report_template_viya_pre_install_check.j2",
                                   report_file_path,
                                   trim_blocks=True, lstrip_blocks=True,
                                   global_data=global_data, master_data=master_data,
                                   configs_data=configs_data,
                                   storage_data=storage_data,
                                   namespace_data=namespace_data,
                                   cluster_admin_permission_data=cluster_admin_permission_data.items(),
                                   namespace_admin_permission_data=namespace_admin_permission_data.items(),
                                   ingress_data=ingress_data.items(),
                                   namespace_admin_permission_aggregate=ns_admin_permission_aggregate['Permissions'],
                                   cluster_admin_permission_aggregate=cluster_admin_permission_aggregate['Permissions'])

        print("Created: {}".format(report_file_path))
        print("Created: {}".format(output_directory + _REPORT_LOG_NAME_TMPL_.format(file_timestamp)))
        print()

        return os.path.abspath(report_file_path)
