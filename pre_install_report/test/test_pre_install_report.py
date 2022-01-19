
####################################################################
# ### test_pre_install_report.py                                 ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import os
import sys

import pprint
import json
import logging
import semantic_version

from pint import UnitRegistry
from pre_install_report.library.pre_install_utils import PreCheckUtils
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from pre_install_report.library.utils import viya_constants
from pre_install_report.library.pre_install_check import ViyaPreInstallCheck
from pre_install_report.library.pre_install_check_permissions import PreCheckPermissions
from viya_ark_library.jinja2.sas_jinja2 import Jinja2TemplateRenderer
from viya_ark_library.logging import ViyaARKLogger
from pre_install_report.pre_install_report import read_environment_var
from pre_install_report.library.utils import viya_messages

_SUCCESS_RC_ = 0
_BAD_OPT_RC_ = 1
_BAD_ENV_RC_ = 2
_BAD_CONFIG_RC_ = 3
_BAD_CONFIG_JSON_RC_ = 4
_CONNECTION_ERROR_RC_ = 5
_NAMESPACE_NOT_FOUND_RC_ = 6
_RUNTIME_ERROR_RC_ = 7

viya_kubelet_version_min = 'v1.14.0'
viya_min_aggregate_worker_CPU_cores = '12'
viya_min_aggregate_worker_memory = '56G'

# setup sys.path for import of viya_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)))
# turn off logging
sas_logger = ViyaARKLogger("test_report.log", logging_level=logging.NOTSET, logger_name="debug_logger")


def test_get_storage_classes_json():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/multi_storage_classes.json')
    with open(datafile) as f:
        data = json.load(f)
    global_data = []
    configs_data = []
    storage_data = vpc._get_storage_classes(data)
    print('\r', (storage_data[0]))
    print('\r', (storage_data[1]))
    assert len(storage_data) == 2

    template_render(global_data, configs_data, storage_data, 'storage_classes_info.html')


def test_read_cluster_info_output():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)
    cluster_info = "Kubernetes master is running at https://0.0.0.0:6443\n" + \
                   "KubeDNS is running at " + \
                   "https://0.0.0.0:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy\n"
    data = vpc._read_cluster_info_output(cluster_info)
    assert(not os.path.exists("temp_cluster_info.txt"))
    assert(len(str(data)) > 0)


def test_delete_temp_file():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    file_name = "temp_cluster_info_test.txt"
    data = "Some data"
    file = open(file_name, "w+")
    file.writelines(str(data))
    file.close()
    assert(os.path.exists(file_name))
    vpc._delete_temp_file(file_name)
    assert (not os.path.exists("temp_cluster_info.txt"))


def test_get_master_nodes_json():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    cluster_info = "Kubernetes master is running at https://0.0.0.0:6443\n" + \
                   "KubeDNS is running at " + \
                   "https://0.0.0.0:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy\n"
    master_data = vpc._check_master(cluster_info)
    assert master_data[0]['totalMasters'] == '1'
    assert master_data[0]['status'] == 0
    assert "Kubernetes master is running at https://0.0.0.0:6443" in master_data[0]['firstFailure']


def test_ranchersingle_get_master_nodes_json():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    cluster_info = "Kubernetes master is running at https://127.0.0.1:6443\n" + \
        "CoreDNS is running at " + \
        "https://127.0.0.1:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy\n" + \
        "Metrics-server is running at " + \
        "https://127.0.0.1:6443/api/v1/namespaces/kube-system/services/https:metrics-server:/proxy\n" + \
        "                                                                                                  " + \
        "To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.\n"

    master_data = vpc._check_master(cluster_info)
    assert master_data[0]['totalMasters'] == '1'
    assert master_data[0]['status'] == 0
    assert "Kubernetes master is running at https://127.0.0.1:6443" in master_data[0]['firstFailure']


def test_ranchermulti_get_master_nodes_json():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    cluster_info = "Kubernetes master is running at https://node3:6443\n" + \
        "CoreDNS is running at https://node3:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy\n" + \
        "                                                                                                  " + \
        "To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.\n"
    master_data = vpc._check_master(cluster_info)
    assert master_data[0]['totalMasters'] == '1'
    assert master_data[0]['status'] == 0
    assert "Kubernetes master is running at https://node3:6443" in master_data[0]['firstFailure']


def test_get_nested_nodes_info():

    viya_min_aggregate_worker_CPU_cores = '20'
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/nodes_info.json')
    # Register Python Package Pint definitions
    quantity_ = register_pint()
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data, quantity_)

    storage_data = []
    configs_data = []

    global_data = []
    assert vpc._workers == 3

    cluster_info = "Kubernetes master is running at https://0.0.0.0:6443\n"
    global_data = vpc.evaluate_nodes(nodes_data, global_data, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:
        assert global_data[0]['totalWorkers'] in '3: Current: 3, Expected: Minimum 1'
        assert global_data[2]['aggregate_cpu_failures'] in 'Current: 18.0, Expected: 20, Issues Found: 1'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 67.13 G,' \
                                                              ' Memory within Range,' \
                                                              ' Issues Found: 0'

        total_aggregate_memoryG = vpc.get_calculated_aggregate_memory()  # quantity_("62.3276481628418 Gi").to('G')
        assert str(round(total_aggregate_memoryG.to("G"), 2)) == '67.13 G'
        assert str(round(total_aggregate_memoryG.to("Gi"), 2)) == '62.52 Gi'
        assert global_data[4]['aggregate_kubelet_failures'] in 'Check Kubelet Version on nodes. Issues Found: 1.'

    template_render(global_data, configs_data, storage_data, 'nested_nodes_info.html')


def test_get_nested_millicores_nodes_info():
    viya_kubelet_version_min = 'v1.14.0'
    viya_min_aggregate_worker_CPU_cores = '20'
    viya_min_aggregate_worker_memory = '156G'
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)
    # Register Python Package Pint definitions
    quantity_ = register_pint()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/nodes_info_millicore.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data, quantity_)

    storage_data = []
    configs_data = []

    global_data = []

    cluster_info = "Kubernetes master is running at https://0.0b.0.0:6443\n"
    global_data = vpc.evaluate_nodes(nodes_data, global_data, cluster_info, quantity_)
    pprint.pprint(global_data)
    template_render(global_data, configs_data, storage_data, 'nested_millicores_nodes_info.html')
    for nodes in global_data:
        assert global_data[0]['totalWorkers'] in '3: Current: 3, Expected: Minimum 1'

        assert global_data[2]['aggregate_cpu_failures'] in 'Current: 2.5, Expected: 20, Issues Found: 1'
        assert global_data[3]['aggregate_memory_failures'] in 'Current: 68.16 G, Expected: 156G,' \
                                                              ' Issues Found: 1'
        total_calc_memoryG = vpc.get_calculated_aggregate_memory()
        assert str(round(total_calc_memoryG.to("G"), 2)) == '68.16 G'  # 68.16113098752
        assert global_data[4]['aggregate_kubelet_failures'] in 'Check Kubelet Version on nodes. Issues Found: 2.'

    template_render(global_data, configs_data, storage_data, 'nested_millicores_nodes_info.html')


def test_ranchersingle_get_nested_nodes_info():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)
    quantity_ = register_pint()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/ranchersingle_nodes_info.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data, quantity_)

    storage_data = []
    configs_data = []

    global_data = []
    cluster_info = "Kubernetes master is running at https://127.0.0.1:6443\n"

    global_data = vpc.evaluate_nodes(nodes_data, global_data, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:
        assert global_data[2]['aggregate_cpu_failures'] in 'Current: 8.0, Expected: 12, Issues Found: 1'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 67.39 G,' \
                                                              ' Memory within Range,' \
                                                              ' Issues Found: 0'
        total_calc_memoryG = vpc.get_calculated_aggregate_memory()
        assert str(round(total_calc_memoryG.to("G"), 2)) == '67.39 G'
        assert global_data[4]['aggregate_kubelet_failures'] in 'Check Kubelet Version on nodes. Issues Found: 0'

    template_render(global_data, configs_data, storage_data, 'ranchersingle_nested_nodes_info.html')


def test_ranchermulti_get_nested_nodes_info():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)
    quantity_ = register_pint()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/ranchermulti_nodes_info.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data, quantity_)

    storage_data = []
    configs_data = []

    global_data = []
    cluster_info = "Kubernetes master is running at https://node3:6443\n"

    global_data = vpc.evaluate_nodes(nodes_data, global_data, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:

        assert global_data[2]['aggregate_cpu_failures'] in 'Expected: 12, Calculated: 40.0, Issues Found: 0'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 336.94 G,' \
                                                              ' Memory within Range,' \
                                                              ' Issues Found: 0'
        assert global_data[4]['aggregate_kubelet_failures'] in 'Check Kubelet Version on nodes. Issues Found: 0'

    template_render(global_data, configs_data, storage_data, 'ranchermulti_nested_nodes_info.html')


def test_get_no_config_info():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/no_config_info.json')
    with open(datafile) as f:
        data = json.load(f)
    configs_data = []
    configs_data = vpc._get_config_current_context(data, configs_data)
    pprint.pprint(configs_data)
    assert configs_data == [[]]


def test_check_route_host_port():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/openshift_route.json')
    data = None
    with open(datafile) as f:
        data = json.load(f)
    route_k8s: KubernetesResource = KubernetesResource(data)
    assert route_k8s.get_kind() == "Route"

    pre_check_utils_params = {}
    pre_check_utils_params[viya_constants.KUBECTL] = None
    pre_check_utils_params["logger"] = sas_logger
    utils = PreCheckUtils(pre_check_utils_params)
    params = {}
    params[viya_constants.INGRESS_CONTROLLER] = viya_constants.OPENSHIFT_INGRESS
    params[viya_constants.INGRESS_HOST] = ''
    params[viya_constants.INGRESS_PORT] = ''
    params['logger'] = sas_logger
    params[viya_constants.PERM_CLASS] = utils
    permissions_check = PreCheckPermissions(params)

    permissions_check.set_route_k8s_resource(route_k8s)
    permissions_check.check_openshift_route_host_port()
    host = permissions_check.get_route_host()
    assert host == 'no-route-hostname-lasiva.apps.ocp47vmw02.devops.rnd.sas.com'


def test_get_config_info():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/config_info.json')
    with open(datafile) as f:
        data = json.load(f)
    configs_data = []
    storage_data = []
    global_data = []

    configs_data = vpc._get_config_current_context(data, configs_data)
    configs_data = vpc._get_config_contexts(data, configs_data)
    configs_data = vpc._get_config_clusters(data, configs_data)
    configs_data = vpc._get_config_users(data, configs_data)
    pprint.pprint(configs_data)
    assert (configs_data[0][0]['currentcontext']) == 'kubernetes-admin@kubernetes'
    assert(configs_data[1][0]['cluster']) == 'kubernetes'
    assert(configs_data[1][0]['clusteruser']) == 'kubernetes-admin'
    assert(configs_data[1][0]['contextName']) == 'kubernetes-admin@kubernetes'
    assert(configs_data[1][1]['cluster']) == 'kubernetesTest'
    assert(configs_data[1][1]['clusteruser']) == 'kubernetes-test'
    assert(configs_data[1][1]['contextName']) == 'kubernetes-test@kubernetesTest'
    assert(configs_data[2][0]['server']) == "https://0.0.0.0:6443"
    assert(configs_data[2][0]['clustername']) == "kubernetes"
    assert(configs_data[2][0]['server']) == "https://0.0.0.0:6443"
    assert(configs_data[2][0]['clustername']) == "kubernetes"
    assert(configs_data[3][0]['username']) == "kubernetes-admin"
    assert(configs_data[3][1]['username']) == "kubernetes-test"
    template_render(global_data, configs_data, storage_data, 'config_report.html')


def test_ranchersingle_test_get_config_info():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/ranchersingle_config_info.json')
    with open(datafile) as f:
        data = json.load(f)
    configs_data = []
    storage_data = []
    global_data = []

    configs_data = vpc._get_config_current_context(data, configs_data)
    configs_data = vpc._get_config_contexts(data, configs_data)
    configs_data = vpc._get_config_clusters(data, configs_data)
    configs_data = vpc._get_config_users(data, configs_data)
    pprint.pprint(configs_data)
    assert(configs_data[0][0]['currentcontext']) == 'default'
    assert(configs_data[2][0]['server']) == "https://127.0.0.1:6443"
    assert(configs_data[2][0]['clustername']) == "default"

    template_render(global_data, configs_data, storage_data, 'ranchersingle_config_report.html')


def test_ranchermulti_test_get_config_info():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/ranchermulti_config_info.json')
    with open(datafile) as f:
        data = json.load(f)
    configs_data = []
    storage_data = []
    global_data = []

    configs_data = vpc._get_config_current_context(data, configs_data)
    configs_data = vpc._get_config_contexts(data, configs_data)
    configs_data = vpc._get_config_clusters(data, configs_data)
    configs_data = vpc._get_config_users(data, configs_data)
    pprint.pprint(configs_data)
    assert(configs_data[0][0]['currentcontext']) == 'gelcluster'
    assert(configs_data[1][0]['cluster']) == 'gelcluster'
    assert(configs_data[1][0]['clusteruser']) == 'kube-admin-gelcluster'
    assert (configs_data[1][0]['contextName']) == 'gelcluster'
    assert(configs_data[2][0]['server']) == "https://node3:6443"
    assert(configs_data[2][0]['clustername']) == "gelcluster"
    assert (configs_data[3][0]['username']) == "kube-admin-gelcluster"
    template_render(global_data, configs_data, storage_data, 'ranchermulti_config_report.html')


def test_azure_terrform_multi_nodes_info():
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    quantity_ = register_pint()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/azure_terrform_multi_nodes_info.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data, quantity_)

    storage_data = []
    configs_data = []

    global_data = []
    cluster_info = "Kubernetes master is running at https://node3:6443\n"

    global_data = vpc.evaluate_nodes(nodes_data, global_data, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:

        assert global_data[2]['aggregate_cpu_failures'] in 'Expected: 12, Calculated: 39.1, Issues Found: 0'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 168.54 G,' \
                                                              ' Memory within Range,' \
                                                              ' Issues Found: 0'
        assert global_data[4]['aggregate_kubelet_failures'] in 'Check Kubelet Version on nodes. Issues Found: 0'

    template_render(global_data, configs_data, storage_data, 'azure_terrform_multi_nodes_info.html')


def test_azure_multi_get_nested_nodes_info():

    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    quantity_ = register_pint()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/azure_multi_nodes_info.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data, quantity_)

    storage_data = []
    configs_data = []

    global_data = []
    cluster_info = "Kubernetes master is running at https://node3:6443\n"

    for node in nodes_data:
        assert node['Ready'] in 'True'

    global_data = vpc.evaluate_nodes(nodes_data, global_data, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:

        assert global_data[2]['aggregate_cpu_failures'] in 'Expected: 12, Calculated: 32.0, Issues Found: 0'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 117.92 G,' \
                                                              ' Memory within Range,' \
                                                              ' Issues Found: 0'
        assert global_data[4]['aggregate_kubelet_failures'] in '0, Check Kubelet Version on nodes.'

    template_render(global_data, configs_data, storage_data, 'azure_multi_nested_nodes_info.html')


def test_azure_worker_nodes():
    viya_kubelet_version_min = 'v1.17.0'
    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    quantity_ = register_pint()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/azure_nodes_no_master.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data, quantity_)
    assert vpc._workers == 10

    storage_data = []
    configs_data = []

    global_data = []
    cluster_info = "Kubernetes master is running at https://node3:6443\n"
    issues_found = 8
    global_data = vpc.evaluate_nodes(nodes_data, global_data, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:
        assert global_data[2]['aggregate_cpu_failures'] in \
               'Expected: 12, Calculated: 143.74, Issues Found: 0'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 802.28 G,' \
                                                              ' Memory within Range,' \
                                                              ' Issues Found: 0'
        assert global_data[4]['aggregate_kubelet_failures'] in 'Check Kubelet Version on nodes. Issues Found: 10. ' \
                                                               'Check Node(s). All Nodes NOT in Ready Status. ' \
                                                               'Issues Found: ' + str(issues_found)

    template_render(global_data, configs_data, storage_data, 'azure_nodes_no_master.html')


def template_render(global_data, configs_data, storage_data, report):

    templates_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep + ".." \
        + os.sep + "templates" + os.sep

    report_file_path = report

    template_renderer = Jinja2TemplateRenderer(templates_dir=templates_dir)
    report_file_path = template_renderer.as_html("report_template_viya_pre_install_check.j2",
                                                 report_file_path,
                                                 trim_blocks=True, lstrip_blocks=True,
                                                 global_data=global_data, configs_data=configs_data,
                                                 storage_data=storage_data)
    print("Created: {}".format(report_file_path))


def register_pint():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, '../library/utils/kdefinitions.txt')
    ureg = UnitRegistry(datafile)
    quantity_ = ureg.Quantity
    return quantity_


def createViyaPreInstallCheck(viya_kubelet_version_min,
                              viya_min_aggregate_worker_CPU_cores,
                              viya_min_aggregate_worker_memory):

    sas_pre_check_report: ViyaPreInstallCheck = ViyaPreInstallCheck(sas_logger,
                                                                    viya_kubelet_version_min,
                                                                    viya_min_aggregate_worker_CPU_cores,
                                                                    viya_min_aggregate_worker_memory)

    return sas_pre_check_report


def test_get_calculated_aggregate_memory():

    vpc = createViyaPreInstallCheck(viya_kubelet_version_min,
                                    viya_min_aggregate_worker_CPU_cores,
                                    viya_min_aggregate_worker_memory)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/nodes_info.json')
    # Register Python Package Pint definitions
    quantity_ = register_pint()
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data, quantity_)

    global_data = []

    assert vpc.get_calculated_aggregate_memory() is None
    cluster_info = "Kubernetes master is running at https://0.0.0.0:6443\n"
    global_data = vpc.evaluate_nodes(nodes_data, global_data, cluster_info, quantity_)

    total_calc_memoryGi = vpc.get_calculated_aggregate_memory()
    assert str(round(total_calc_memoryGi.to('Gi'), 13)) == '62.5229606628418 Gi'


def test_kubconfig_file():
    old_kubeconfig = os.environ.get('KUBECONFIG')  # /Users/cat/doc
    os.environ['KUBECONFIG'] = 'blah_nonexistentfile_blah'
    new_kubeconfig = os.environ.get('KUBECONFIG')  # /Users/cat/doc
    assert new_kubeconfig == 'blah_nonexistentfile_blah'
    try:
        read_environment_var('KUBECONFIG')
    except SystemExit as exc:
        assert exc.code == viya_messages.BAD_ENV_RC_
        pass
    finally:
        os.environ['KUBECONFIG'] = str(old_kubeconfig)


def test_get_k8s_version():
    """
    Retrieve thhe server Kubernetes mjor and minor version using
    https://pypi.org/project/packaging/  20.9 initial version
    Used by python setup tools
    """
    # versions: Dict = self.utils.get_k8s_version()
    version_string = "1.18.9-eks-d1db3c"
    version_string2 = "1.19.0"

    params = {}
    params[viya_constants.INGRESS_CONTROLLER] = 'nginx'
    params[viya_constants.INGRESS_HOST] = '10.240.9.8'
    params[viya_constants.INGRESS_PORT] = '80'
    params['logger'] = sas_logger

    # initialize the PreCheckPermissions object
    perms = PreCheckPermissions(params)
    perms.set_k8s_git_version(version_string)

    # check curren version less than 1.20
    curr_version = semantic_version.Version(str(version_string2))
    assert (curr_version in semantic_version.SimpleSpec('<1.20'))
    assert (curr_version in semantic_version.SimpleSpec('==1.19'))

    # current version is less then 1.19
    curr_version = semantic_version.Version(str(version_string))
    assert (curr_version in semantic_version.SimpleSpec('<1.19'))


def test_check_permissions():
    # namespace = 'default'
    params = {}
    params[viya_constants.INGRESS_CONTROLLER] = 'nginx'
    params[viya_constants.INGRESS_HOST] = '10.240.9.8'
    params[viya_constants.INGRESS_PORT] = '80'
    params['logger'] = sas_logger

    # initialize the PreCheckPermissions object
    perms = PreCheckPermissions(params)
    cluster_permission_data = perms.get_cluster_admin_permission_data()
    assert len(cluster_permission_data) == 0
    namespace_admin_permission_data = perms.get_namespace_admin_permission_data()
    assert len(namespace_admin_permission_data) == 0
    ingress_data = perms.get_ingress_data()
    assert ingress_data[viya_constants.INGRESS_CONTROLLER] in 'nginx'
    namespace_admin_permission_aggregate = perms.get_namespace_admin_permission_aggregate()
    assert namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] in viya_constants.ADEQUATE_PERMS
    cluster_admin_permission_aggregate = perms.get_cluster_admin_permission_aggregate()
    assert cluster_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] in viya_constants.ADEQUATE_PERMS

    # Pytest not implemented currently.  Scaffolding TBD.  Currently requires live cluster
    # perms.check_sample_application(namespace, debug)
    # perms.check_sample_ingress(namespace, debug)
    # perms.check_deploy_crd(namespace, debug)
    # perms.check_rbac_role(namespace, debug)
    # perms.check_create_custom_resource(namespace, debug)
    # perms.check_get_custom_resource(namespace, debug)
    # perms.check_delete_custom_resource(namespace, debug)
    # perms.check_rbac_delete_role(namespace, debug)
    # perms.check_sample_response(debug)
    # perms.check_delete_crd(namespace, debug)
    # perms.check_delete_sample_application(namespace, debug)
    # perms.check_delete_sample_ingress(namespace, debug)
