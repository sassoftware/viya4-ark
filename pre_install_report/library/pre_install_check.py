#!/usr/bin/env python3
####################################################################
# ### pre_install_check.py                                       ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021-2023, SAS Institute Inc., Cary, NC, USA.    ###
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
import pint
from subprocess import CalledProcessError
from typing import Text, Dict

# import pint to add, compare memory
import semantic_version
from pint import UnitRegistry

from pre_install_report.library.utils import viya_messages
from pre_install_report.library.utils import viya_constants
from pre_install_report.library.pre_install_check_permissions import PreCheckPermissions
from pre_install_report.library.pre_install_utils import PreCheckUtils
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface
from viya_ark_library.jinja2.sas_jinja2 import Jinja2TemplateRenderer
from viya_ark_library.logging import ViyaARKLogger

PRP = pprint.PrettyPrinter(indent=4)
# templates for output file names #
_REPORT_FILE_NAME_TMPL_ = "viya_pre_install_report_{}.html"
_REPORT_LOG_NAME_TMPL_ = "viya_pre_install_log_{}.log"
_FILE_TIMESTAMP_TMPL_ = "%Y-%m-%dT%H_%M_%S"

# set timestamp for report file
file_timestamp = datetime.datetime.now().strftime(_FILE_TIMESTAMP_TMPL_)


class ViyaPreInstallCheck():
    """
    A ViyaPreInstallCheck object represents a summary of resources currently detected on the target Kubernetes
    environment.

    A cache of Kubernetes resources are stored for access via the API.

    The gathered data can be written to disk as an HTML report and a JSON file containing the gathered data.
    """

    def __init__(self, sas_logger: ViyaARKLogger, viya_k8s_version_min,
                 viya_min_aggregate_worker_CPU_cores,
                 viya_min_aggregate_worker_memory):
        """
        Constructor for ViyaPreInstallCheck object.
        """
        self._report_data = None
        self._kubectl: KubectlInterface = None
        self.sas_logger = sas_logger
        self.logger = self.sas_logger.get_logger()
        self._viya_k8s_version_min = viya_k8s_version_min
        self._validated_kubernetes_version_min = None
        self._viya_min_aggregate_worker_CPU_cores: Text = viya_min_aggregate_worker_CPU_cores
        self._viya_min_aggregate_worker_memory: Text = viya_min_aggregate_worker_memory
        self._calculated_aggregate_memory = None
        self._workers = 0
        self._aggregate_nodeStatus_failures = 0
        self._k8s_server_version = None

    def _parse_release_info(self, release_info):
        """
        This method checks that the format of the VIYA_K8S_VERSION_MIN specified in the
        user modifiable ini file is valid.

        :param release_info: The minimum K8s version loaded from ini file.
        :return tuple of major version, minor version
        """
        try:
            info = tuple(release_info.split("."))
            if (len(info) == 2):
                x = [int(i) for a, i in enumerate(info)]
                self.logger.debug('release tuple to int {} '.format(x))
                k8s_min_rel_str = ''.join(release_info)
                self._validated_kubernetes_version_min = k8s_min_rel_str
            else:
                print('****' + viya_messages.KUBELET_VERSION_ERROR)
                sys.exit(viya_messages.BAD_OPT_RC_)

        except ValueError:
            print(viya_messages.KUBELET_VERSION_ERROR)
            sys.exit(viya_messages.BAD_OPT_RC_)

    def _validate_k8s_server_version(self, version):
        """
        Validate the major and minor parts of the kubernetes version.  The 3rd part is not specified in the Kubernetes
        cluster requirements
        """
        version_parts_to_validate = 2
        version_lst = version.split('.')
        if (len(version_lst) < version_parts_to_validate):
            self.logger.error(viya_messages.KUBERNETES_VERSION_ERROR.format(version))
            print(viya_messages.KUBERNETES_VERSION_ERROR.format(version))
            sys.exit(viya_messages.INVALID_K8S_VERSION_RC_)

        for i in range(version_parts_to_validate):
            if version_lst[i].startswith("0") or float(version_lst[i]) < 0:
                self.logger.error(viya_messages.KUBERNETES_VERSION_ERROR.format(version))
                print(viya_messages.KUBERNETES_VERSION_ERROR.format(version))
                sys.exit(viya_messages.INVALID_K8S_VERSION_RC_)
            i += 1
        return 0

    def _retrieve_k8s_server_version(self, utils):
        """
        Retrieve the Kubernetes server version and validate the git version
        """
        try:
            versions: Dict = utils.get_k8s_version()
            server_version = versions.get('serverVersion')
            git_version = str(server_version.get('gitVersion'))
            self.logger.debug("git_version {} ".format(git_version))
            # check git_version is not empty
            if git_version and git_version.startswith("v"):
                git_version = git_version[1:]
            self._validate_k8s_server_version(git_version)

            self.logger.info('Kubernetes Server version = {}'.format(git_version))
            return git_version
        except CalledProcessError as cpe:
            self.logger.exception('kubectl version command failed. Return code = {}'.format(str(cpe.returncode)))
            sys.exit(viya_messages.RUNTIME_ERROR_RC_)

    def _k8s_server_version_min(self):
        """
        Compare Kubernetes Version to the Minimum version expected. See
        https://pypi.org/project/semantic_version/  2.8.5 initial version
        """
        try:
            curr_version = semantic_version.Version(str(self._k8s_server_version))

            self._parse_release_info(self._viya_k8s_version_min)
            min_k8s_version = "<" + self._validated_kubernetes_version_min

            if(curr_version in semantic_version.SimpleSpec(min_k8s_version)):
                self.logger.error("This release of Kubernetes is not supported {}.{}.x"
                                  .format(str(curr_version.major),
                                          str(curr_version.minor)))
                return False
            else:
                return True
        except ValueError as cpe:
            self.logger.exception(viya_messages.EXCEPTION_MESSAGE.format(str(cpe)))
            sys.exit(viya_messages.RUNTIME_ERROR_RC_)

    def check_details(self, kubectl,
                      output_dir):
        self._kubectl = kubectl
        name_space = kubectl.get_namespace()
        self.logger.info("names_space: {} ".format(name_space))

        # Register Python Package Pint definitions
        current_dir = os.path.dirname(os.path.abspath(__file__))
        datafile = os.path.join(current_dir, "utils" + os.sep + 'kdefinitions.txt')

        ureg = UnitRegistry(datafile)
        quantity_ = ureg.Quantity

        pre_check_utils_params = {}
        pre_check_utils_params[viya_constants.KUBECTL] = self._kubectl
        pre_check_utils_params["logger"] = self.sas_logger
        utils = PreCheckUtils(pre_check_utils_params)

        self._k8s_server_version = self._retrieve_k8s_server_version(utils)

        configs_data = self.get_config_info()
        cluster_info = self._get_master_json()
        master_data = self._check_master(cluster_info)
        namespace_data = []
        namespace_data = self._check_available_namespaces(self._get_json("namespaces"), namespace_data)

        storage_json = self._get_json("storageclass")
        storage_data = self._get_storage_classes(storage_json)

        nodes_json = self._get_json("nodes")
        nodes_data = self.get_nested_nodes_info(nodes_json, quantity_)

        global_data = []
        global_data = self.evaluate_nodes(nodes_data, global_data, cluster_info, quantity_)

        params = {}
        params[viya_constants.PERM_CLASS] = utils
        params[viya_constants.SERVER_K8S_VERSION] = self._k8s_server_version
        params['logger'] = self.sas_logger

        permissions_check = PreCheckPermissions(params)
        self._check_permissions(permissions_check)

        test_list = [viya_constants.INSUFFICIENT_PERMS, viya_constants.PERM_SKIPPING]

        # Log Summary of Permissions Issues found
        if(any(ele in str(permissions_check.get_cluster_admin_permission_aggregate()) for ele in test_list)):
            self.logger.warn("WARN: Review Cluster Aggregate Report")
        if(any(ele in str(permissions_check.get_namespace_admin_permission_aggregate()) for ele in test_list)):
            self.logger.warn("WARN: Review Namespace Aggregate Report")

        self.generate_report(global_data, master_data, configs_data, storage_data, namespace_data,
                             permissions_check.get_cluster_admin_permission_data(),
                             permissions_check.get_namespace_admin_permission_data(),
                             permissions_check.get_namespace_admin_permission_aggregate(),
                             permissions_check.get_cluster_admin_permission_aggregate(),
                             output_dir)
        return

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
                    config_data = {'currentcontext': viya_messages.CONFIG_ERROR}
            except KeyError:
                config_data = {'currentcontext': viya_constants.KEY_NOT_FOUND}
                print(viya_messages.CONFIG_ERROR)
                self.logger.exception(viya_messages.CONFIG_ERROR)
                sys.exit(viya_messages.BAD_CONFIG_JSON_RC_)

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
                print(viya_messages.CONFIG_ERROR)
                sys.exit(viya_messages.BAD_CONFIG_JSON_RC_)

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
                self.logger.exception("TypeError {}".format(str(error)))
                print(viya_messages.CONFIG_ERROR)
                sys.exit(viya_messages.BAD_CONFIG_JSON_RC_)

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
                print(viya_messages.CONFIG_ERROR)
                sys.exit(viya_messages.BAD_CONFIG_JSON_RC_)

        self.logger.debug("cluster_data: {}".format(pprint.pformat(cluster_data)))

        configs_data.append(cluster_data)
        return configs_data

    def _get_json(self, k8sresource):
        """
        Retrieve the k8s resource information from the Kubernetes cluster in json format.

        return:  nodes information in json format
        """
        resource_json = self._get_raw_json(k8sresource)

        return resource_json

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
                try:
                    node_data['storageClassNameName'] = node['metadata']['name']
                    node_data['provisioner'] = node['provisioner']
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

    def _check_permissions(self, permissions_check: PreCheckPermissions):
        """
        Check if permissions are adequate to complete Viya deployment with cluster admin
        and namespace admin lveles of access to cluster resources

        permissions_check:  instance of PreCheckPermissions class
        """
        namespace = self._kubectl.get_namespace()
        permissions_check.get_sc_resources()

        permissions_check.manage_pvc(viya_constants.KUBECTL_APPLY, False)
        permissions_check.check_deploy_crd()
        permissions_check.check_rbac_role()
        permissions_check.check_create_custom_resource()
        permissions_check.check_get_custom_resource(namespace)

        permissions_check.check_delete_custom_resource()
        permissions_check.check_rbac_delete_role()
        permissions_check.check_delete_crd()

        # Check the status of deployed PVCs
        permissions_check.manage_pvc(viya_constants.KUBECTL_APPLY, True)
        # Delete all Deployed PVCs
        permissions_check.manage_pvc(viya_constants.KUBECTL_DELETE, False)

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
            master_nodes.update({'totalMasters': str(viya_constants.SET) + ': 0, ' + str(viya_constants.EXPECTED) +
                                ': Minimum ' + str(viya_constants.NUMBER_OF_MASTER_NODES)})
            master_nodes.update({'status': 1})
            master_nodes.update({'issue': master_nodes['totalMasters'] + ', ' + 'Issues Found: ' + str(1)})
            master_nodes.update({'firstFailure': 'Cluster information not available. Check permissions.'})

        master_data.append(master_nodes)
        self.logger.debug("master_data {}".format(pprint.pformat(master_data)))
        return master_data

    def _check_workers(self, global_data, nodes_data):
        """
        Check list of worker nodes information and calculate the total number of worker nodes
        and update it in the global data list.

        global_data:  list that contains lobal data about nodes
        nodes_data:  list of dict objects, each with node information
        return: updated global_data list with total number of worker nodes.
        """
        global_nodes = {}
        workers = self._workers

        global_nodes.update({'totalWorkers': str(workers) + ': ' + str(viya_constants.SET + ': ' + str(workers) +
                                                                       ', ' + str(viya_constants.EXPECTED) +
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
                                    " \nCheck SAS Viya Platform Documentation")})

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

    def _update_k8s_version(self, global_data, git_version):
        """Set the Cluster Kubernetes Version for the report in the global data list

        global_data: List to be updated
        return:  global_data list updated with Kubernetes Version to be added to the report
        """
        global_nodes = {}

        global_nodes.update({'k8sVersion': str(git_version)})
        global_data.append(global_nodes)

        self.logger.debug("global data{} Kubernetes Version {}".format(pprint.pformat(global_data), git_version))
        return global_data

    def _check_cpu_errors(self, global_data, total_capacity_cpu_cores: float, aggregate_cpu_failures):
        """
        Check if the aggregate CPUs across all worker nodes meets SAS total cpu requirements

        global_data: list with global data about worker nodes retrieved
        total_capacity_cpu_cores:  total cpu cores across all worker nodes calculated
        aggregate_cpu_failures:  count of cpu failures
        """
        aggregate_cpu_data = {}
        msg = ''
        error_msg = ""
        info_msg = str(viya_constants.EXPECTED) + ': ' + \
            self._viya_min_aggregate_worker_CPU_cores + \
            ', Calculated: ' + str(round(total_capacity_cpu_cores, 2))

        min_aggr_worker_cpu_core = self._get_cpu(self._viya_min_aggregate_worker_CPU_cores,
                                                 "VIYA_MIN_AGGREGATE_WORKER_CPU_CORES")

        if total_capacity_cpu_cores < min_aggr_worker_cpu_core:
            aggregate_cpu_failures += 1
            # Check for combined cpu_core capacity of the Kubernetes nodes in cluster
        error_msg = viya_constants.SET + ': ' + str(round(total_capacity_cpu_cores, 2)) + \
            ', ' + str(viya_constants.EXPECTED) + ': ' + self._viya_min_aggregate_worker_CPU_cores
        if aggregate_cpu_failures > 0:
            msg = error_msg
        else:
            msg = info_msg
        aggregate_cpu_data.update({'aggregate_cpu_failures': msg + ', Issues Found: ' + str(aggregate_cpu_failures)})

        global_data.append(aggregate_cpu_data)

        return global_data

    def _check_memory_errors(self, global_data, total_capacity_memory, quantity_, aggregate_memory_failures):
        """
        Check aggregate memory across all worker nodes against SAS total memory requirement in worker nodes

        global_data: list with global data about worker nodes retrieved
        total_capacity_memory:  total memory calculated across all worker nodes calculated
        aggregate_memory_failures:  count of memory failures
        """
        aggregate_memory_data = {}
        error_msg = ""
        msg = ''

        total_capacity_memory_toGB = total_capacity_memory.to('G')

        info_msg = str(viya_constants.EXPECTED) + ': ' + \
            self._viya_min_aggregate_worker_memory + \
            ', Calculated: ' + str(round(total_capacity_memory_toGB, 2))
        self._calculated_aggregate_memory = total_capacity_memory_toGB

        min_aggr_worker_memory = self._get_memory(self._viya_min_aggregate_worker_memory,
                                                  "VIYA_GENERIC_WORKER_MEMORY", quantity_)
        self.logger.info("percent {} percent of instance {} total capacity {}".format
                         (str(viya_constants.VIYA_PERCENTAGE_OF_INSTANCE),
                          str(min_aggr_worker_memory * (int(viya_constants.VIYA_PERCENTAGE_OF_INSTANCE) / 100)),
                          str(total_capacity_memory_toGB)))
        self.logger.info("input memory converted to G {}".format(str(min_aggr_worker_memory.to('G'))))
        if total_capacity_memory_toGB < \
                (min_aggr_worker_memory.to('G')) * (int(viya_constants.VIYA_PERCENTAGE_OF_INSTANCE) / 100):

            aggregate_memory_failures += 1
            # Check for combined cpu_core capacity of the Kubernetes nodes in cluster
        error_msg = viya_constants.SET + ': ' + \
            str(round(total_capacity_memory_toGB, 2)) + ', ' + \
            str(viya_constants.EXPECTED) + ': ' + self._viya_min_aggregate_worker_memory

        if aggregate_memory_failures > 0:
            msg = error_msg
        else:
            msg = info_msg + "," + viya_constants.MEMORY_WITHIN_RANGE

        aggregate_memory_data.update({'aggregate_memory_failures': msg +
                                     ', Issues Found: ' + str(aggregate_memory_failures)})
        global_data.append(aggregate_memory_data)
        return global_data

    def _check_k8s_errors(self, global_data, aggregate_k8s_failures):
        """
        Check Server k8s version against SAS k8s version requirements

        global_data: list with global data about worker nodes retrieved
        aggregate_k8s_failures:  count of k8s version errors
        return: updated global data about worker nodes retrieved
        """
        aggregate_k8s_data = {}
        node_status_msg = ""
        if self._aggregate_nodeStatus_failures > 0:
            node_status_msg = " Check Node(s). All Nodes NOT in Ready Status." \
                              + ' Issues Found: ' + str(self._aggregate_nodeStatus_failures)
        aggregate_k8s_data.update({'aggregate_k8s_failures': node_status_msg})
        if aggregate_k8s_failures > 0:
            aggregate_k8s_data.update({'aggregate_k8s_failures:':
                                       'Check K8s Version on nodes.' +
                                       ' Issues Found: ' + str(aggregate_k8s_failures) +
                                       '.' + node_status_msg})
        global_data.append(aggregate_k8s_data)

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
            self.logger.exception("resource {} return code {}".format(str(k8s_resource), str(return_code)))
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
                node.update(dict(firstFailure=viya_constants.SET + ': Multiple Default Storage Class found, ' +
                            str(viya_constants.EXPECTED) + ": Minimum 1"))
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

    def evaluate_nodes(self, nodes_data, global_data, cluster_info, quantity_):
        """
        Parse the nodes information in list of dict objects and verify against SAS Specifications

        nodes_data: list dict object with node details
        global_data: list of dictionary object with global data for nodes
        return:  return ist of dictionary objects with updated information and status
        """
        aggregate_cpu_failures = int(0)
        aggregate_memory_failures = int(0)
        aggregate_k8s_failures = int(0)
        total_cpu_cores = float(0)

        total_capacity_memory = quantity_("0G")
        # register percetage unit with Pint
        # ureg = pint.UnitRegistry()
        # Q = ureg.Quantity
        # ureg.define(UnitDefinition('percent', 'pct', (), ScaleConverter(1 / 100.0)))

        for node in nodes_data:
            self.logger.info("processing node " + pprint.pformat(node))
            capacity_cpu_cores = self._get_cpu_units(node, 'cpu')
            # alloc_cpu_cores = self._get_cpu_units(node, 'allocatablecpu')

            kubeletversion = str(node['kubeletversion'])
            capacity_memory = str(node['memory'])
            total_capacity_memory = total_capacity_memory + quantity_(capacity_memory).to('G')

            try:
                nodeReady = str(node['Ready'])
                if nodeReady == "True":
                    pass
                else:
                    self._aggregate_nodeStatus_failures += 1
            except KeyError:
                node['Ready'] = viya_constants.KEY_NOT_FOUND

            if node['worker']:
                total_cpu_cores = total_cpu_cores + capacity_cpu_cores
                self.logger.info("worker total_cpu_cores {}".format(str(total_cpu_cores)))

                self._set_status(0, node, 'cpu')
                node['error']['cpu'] = "See below."

                self._set_status(0, node, 'capacityMemory')
                node['error']['capacityMemory'] = "See below."

            if (self._k8s_server_version_min()):
                self._set_status(0, node, 'kubeletversion')
                self.logger.debug("node kubeletversion status 0 {} ".format(pprint.pformat(node)))
            else:
                self._set_status(1, node, 'kubeletversion')
                node['error']['kubeletversion'] = viya_constants.SET + ': ' + kubeletversion + ', ' + \
                    str(viya_constants.EXPECTED) + ': ' + self._validated_kubernetes_version_min + ' or later '

                aggregate_k8s_failures += 1
                self.logger.debug("aggregate_k8s_failures {} ".format(str(aggregate_k8s_failures)))
                self.logger.debug("node kubeletversion{} ".format(pprint.pformat(node)))

        global_data = self._check_workers(global_data, nodes_data)
        global_data = self._set_time(global_data)
        global_data = self._check_cpu_errors(global_data, total_cpu_cores, aggregate_cpu_failures)
        global_data = self._check_memory_errors(global_data, total_capacity_memory, quantity_,
                                                aggregate_memory_failures)

        global_data = self._check_k8s_errors(global_data, aggregate_k8s_failures)

        global_data.append(nodes_data)
        global_data = self._update_k8s_version(global_data, self._k8s_server_version)
        self.logger.debug("nodes_data {}".format(pprint.pformat(nodes_data)))
        return global_data

    def _get_cpu_units(self, node, key):
        """ Calculate the CPU cores if it has been expressed in millicores
            node: node dictionary object
            return:  value of vCPU
        """
        try:
            # ## Switch to capacity cpu core
            cpu_cores = float(node[key])
        except ValueError:
            # CPU is measured in units called millicores. Each node in the cluster introspects the operating system
            # to determine the amount of CPU cores on the node and then multiples that value by 1000 to express
            # its total capacity.
            cpu_cores = float(str(node[key]).rstrip('m')) / 1000

        self.logger.info("cpu_cores {} {}".format(key, str(cpu_cores)))
        return cpu_cores

    def _set_status(self, status, node, key):
        """Set the status flag on dictionary object with node details - to indicate compliance with
        cpu, memory k8s version requirements

        status: status to be set on dict objectwith node details
        node: node dictionary object
        return:  return dictionary object with updated node status information
        """
        if status != 0:
            node.update({'status': status})
            node.update({'firstFailure': str("FAIL: " + key)})

        return node

    def get_nested_nodes_info(self, nodes_json, quantity_):
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
                node_data['taintNoSchedule'] = False
                node_data['taintMaster'] = False
                node_data['worker'] = True

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
                            if tnode[key] == 'NoSchedule':
                                node_data.update({'taintNoSchedule': True})

                            if tnode[key] == 'node-role.kubernetes.io/master':
                                node_data.update({'taintMaster': True})

                except KeyError:
                    node_data['taint'] = viya_constants.KEY_NOT_FOUND
                try:
                    node_data['agentpool'] = (node['metadata']['labels']['agentpool'])
                except KeyError:
                    node_data['agentpool'] = viya_constants.KEY_NOT_FOUND
                try:
                    node_data['instance'] = (node['metadata']['labels']['node.kubernetes.io/instance-type'])
                except KeyError:
                    node_data['instance'] = viya_constants.KEY_NOT_FOUND

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

                if node_data['taintNoSchedule'] and node_data["taintMaster"]:
                    node_data.update({'worker': False})
                else:
                    nodes_data.append(node_data)
                    self._workers += 1

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

    def _get_memory(self, limit, key, quantity_):
        """
        Check that the memory specified in the viya_cluster_settings file is valid. Exit if
        pint package throws exceptions

        :param:  limit - value set in viya_cluster_settings
        :param:  key used viya_cluster_settings (VIYA_MIN_AGGREGATE_WORKER_MEMORY
                 VIYA_GENERIC_WORKER_MEMORY)
        :param   quantity_ is the Pint quantities object
        """
        try:
            input_memory = quantity_(limit)
            return input_memory
        except (pint.errors.UndefinedUnitError, pint.errors.DefinitionSyntaxError):
            print(viya_messages.LIMIT_ERROR.format(key, str(limit)))
            self.logger.exception(viya_messages.LIMIT_ERROR.format(key, str(limit)))
            sys.exit(viya_messages.BAD_OPT_RC_)

    def _get_cpu(self, limit, key):
        """
        Check that the cpu value specified in the viya_cluster_settings file is valid. Exit if
        it does not convert to float

        :param:  limit - value set in viya_cluster_settings
        :param:  key used viya_cluster_settings (VIYA_MIN_AGGREGATE_WORKER_CPU_CORES,
                 VIYA_GENEIC_WORKER_CPU)
        :return   cpu value as float
        """
        try:
            input_cpu = float(limit)
            return input_cpu
        except ValueError:
            print(viya_messages.LIMIT_ERROR.format(key, str(limit)))
            self.logger.exception(viya_messages.LIMIT_ERROR.format(key, str(limit)))
            sys.exit(viya_messages.BAD_OPT_RC_)

    def get_config_info(self):
        """
        Parse the output all the information retrieved by kubectl config view command.

        return: A list of dictionary objects with config information
        """
        configs_data = []
        config_json, return_code = self._get_config_json()

        if return_code != 0:
            print(viya_messages.CONFIG_ERROR)
            self.logger.error(viya_messages.CONFIG_ERROR)
            sys.exit(viya_messages.BAD_CONFIG_RC_)
        else:
            configs_data = self._get_config_current_context(config_json, configs_data)
            configs_data = self._get_config_contexts(config_json, configs_data)
            configs_data = self._get_config_clusters(config_json, configs_data)
            configs_data = self._get_config_users(config_json, configs_data)

        self.logger.debug("configs_data {}".format(configs_data))
        return configs_data

    def get_calculated_aggregate_memory(self):
        return self._calculated_aggregate_memory

    def set_k8s_version(self, version: Text):
        self._k8s_server_version = version

    def set_k8s_version_min(self, version: Text):
        self._viya_k8s_version_min = version

    def generate_report(self,
                        global_data,
                        master_data,
                        configs_data,
                        storage_data,
                        namespace_data,
                        cluster_admin_permission_data,
                        namespace_admin_permission_data,
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
        templates_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep + ".." + os.sep + "templates" + os.sep

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
                    namespace_admin_permission_aggregate=ns_admin_permission_aggregate['Permissions'],
                    cluster_admin_permission_aggregate=cluster_admin_permission_aggregate['Permissions'],
                    cluster_creation_info=viya_messages.CLUSTER_CREATION_INFO,
                    sizings_info=viya_messages.SIZINGS_INFO)

        print("Created: {}".format(report_file_path))
        print("Created: {}".format(output_directory + _REPORT_LOG_NAME_TMPL_.format(file_timestamp)))
        print()

        return os.path.abspath(report_file_path)
