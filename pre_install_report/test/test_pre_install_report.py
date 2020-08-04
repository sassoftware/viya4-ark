
####################################################################
# ### test_pre_install_report.py                                 ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import os
import sys

import pprint
import json
import logging

from pint import UnitRegistry
from pre_install_report.library.utils import viya_constants
from pre_install_report.library.pre_install_check import ViyaPreInstallCheck
from pre_install_report.library.pre_install_check_permissions import PreCheckPermissions
from viya_arkcd_library.jinja2.sas_jinja2 import Jinja2TemplateRenderer
from viya_arkcd_library.logging import ViyaARKCDLogger

_SUCCESS_RC_ = 0
_BAD_OPT_RC_ = 1
_BAD_ENV_RC_ = 2
_BAD_CONFIG_RC_ = 3
_BAD_CONFIG_JSON_RC_ = 4
_CONNECTION_ERROR_RC_ = 5
_NAMESPACE_NOT_FOUND_RC_ = 6
_RUNTIME_ERROR_RC_ = 7

# setup sys.path for import of viya_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)))
# turn off logging
sas_logger = ViyaARKCDLogger("test_report.log", logging_level=logging.NOTSET, logger_name="my_logger")


def test_get_storage_classes_json():
    vpc = createViyaPreInstallCheck()
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
    vpc = createViyaPreInstallCheck()
    cluster_info = "Kubernetes master is running at https://0.0.0.0:6443\n" + \
                   "KubeDNS is running at " + \
                   "https://0.0.0.0:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy\n"
    data = vpc._read_cluster_info_output(cluster_info)
    assert(not os.path.exists("temp_cluster_info.txt"))
    assert(len(str(data)) > 0)


def test_delete_temp_file():
    vpc = createViyaPreInstallCheck()
    file_name = "temp_cluster_info_test.txt"
    data = "Some data"
    file = open(file_name, "w+")
    file.writelines(str(data))
    file.close()
    assert(os.path.exists(file_name))
    vpc._delete_temp_file(file_name)
    assert (not os.path.exists("temp_cluster_info.txt"))


def test_get_master_nodes_json():
    vpc = createViyaPreInstallCheck()
    cluster_info = "Kubernetes master is running at https://0.0.0.0:6443\n" + \
                   "KubeDNS is running at " + \
                   "https://0.0.0.0:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy\n"
    master_data = vpc._check_master(cluster_info)
    assert master_data[0]['totalMasters'] == '1'
    assert master_data[0]['status'] == 0
    assert "Kubernetes master is running at https://0.0.0.0:6443" in master_data[0]['firstFailure']


def test_ranchersingle_get_master_nodes_json():
    vpc = createViyaPreInstallCheck()
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
    vpc = createViyaPreInstallCheck()
    cluster_info = "Kubernetes master is running at https://node3:6443\n" + \
        "CoreDNS is running at https://node3:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy\n" + \
        "                                                                                                  " + \
        "To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.\n"
    master_data = vpc._check_master(cluster_info)
    assert master_data[0]['totalMasters'] == '1'
    assert master_data[0]['status'] == 0
    assert "Kubernetes master is running at https://node3:6443" in master_data[0]['firstFailure']


def test_get_nested_nodes_info():
    vpc = createViyaPreInstallCheck()
    releases = (viya_constants.KUBELET_VERSION_14,
                viya_constants.KUBELET_VERSION_15,
                viya_constants.KUBELET_VERSION_16,
                viya_constants.KUBELET_VERSION_17)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/nodes_info.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data)

    storage_data = []
    configs_data = []

    global_data = []
    # Register Python Package Pint definitions
    quantity_ = register_pint()
    cluster_info = "Kubernetes master is running at https://0.0.0.0:6443\n"
    global_data = vpc.evaluate_nodes(nodes_data, global_data, releases, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:
        assert global_data[0]['totalWorkers'] in '3: Current: 3, Expected: Minimum 1'

        assert global_data[2]['aggregate_cpu_failures'] in 'Current: 10.1, Expected: 12, Issues Found: 2'
        assert global_data[3]['aggregate_memory_failures'] in 'Current: 62.3276481628418 Gi, Expected: 56G,' \
                                                              ' Issues Found: 1'

        assert global_data[4]['aggregate_kubelet_failures'] in '1, Check Kubelet Version on nodes. Issues Found: 1'

    template_render(global_data, configs_data, storage_data, 'nested_nodes_info.html')


def test_ranchersingle_get_nested_nodes_info():
    vpc = createViyaPreInstallCheck()
    releases = (viya_constants.KUBELET_VERSION_14,
                viya_constants.KUBELET_VERSION_15,
                viya_constants.KUBELET_VERSION_16,
                viya_constants.KUBELET_VERSION_17)

    # debug = False
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/ranchersingle_nodes_info.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data)

    storage_data = []
    configs_data = []

    global_data = []
    cluster_info = "Kubernetes master is running at https://127.0.0.1:6443\n"
    quantity_ = register_pint()
    global_data = vpc.evaluate_nodes(nodes_data, global_data, releases, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:
        assert global_data[2]['aggregate_cpu_failures'] in 'Current: 8, Expected: 12, Issues Found: 1'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 62.75947570800781 Gi, ' \
                                                              'Issues Found: 0'
        assert global_data[4]['aggregate_kubelet_failures'] in 'Check Kubelet Version on nodes. Issues Found: 0'

    template_render(global_data, configs_data, storage_data, 'ranchersingle_nested_nodes_info.html')


def test_ranchermulti_get_nested_nodes_info():
    vpc = createViyaPreInstallCheck()
    releases = (viya_constants.KUBELET_VERSION_14,
                viya_constants.KUBELET_VERSION_15,
                viya_constants.KUBELET_VERSION_16,
                viya_constants.KUBELET_VERSION_17)

    # debug = False
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/ranchermulti_nodes_info.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data)

    storage_data = []
    configs_data = []

    global_data = []
    cluster_info = "Kubernetes master is running at https://node3:6443\n"
    quantity_ = register_pint()
    global_data = vpc.evaluate_nodes(nodes_data, global_data, releases, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:

        assert global_data[2]['aggregate_cpu_failures'] in 'Expected: 12, Calculated: 40, Issues Found: 0'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 313.30909729003906 Gi, ' \
                                                              'Issues Found: 0'
        assert global_data[4]['aggregate_kubelet_failures'] in 'Check Kubelet Version on nodes. Issues Found: 0'

    template_render(global_data, configs_data, storage_data, 'ranchermulti_nested_nodes_info.html')


def test_get_no_config_info():
    vpc = createViyaPreInstallCheck()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/no_config_info.json')
    with open(datafile) as f:
        data = json.load(f)
    configs_data = []
    configs_data = vpc._get_config_current_context(data, configs_data)
    pprint.pprint(configs_data)
    assert configs_data == [[]]


def test_get_config_info():
    vpc = createViyaPreInstallCheck()
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
    vpc = createViyaPreInstallCheck()
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
    vpc = createViyaPreInstallCheck()
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
    vpc = createViyaPreInstallCheck()
    releases = (viya_constants.KUBELET_VERSION_14,
                viya_constants.KUBELET_VERSION_15,
                viya_constants.KUBELET_VERSION_16,
                viya_constants.KUBELET_VERSION_17)

    # debug = False
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/azure_terrform_multi_nodes_info.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data)

    storage_data = []
    configs_data = []

    global_data = []
    cluster_info = "Kubernetes master is running at https://node3:6443\n"
    quantity_ = register_pint()
    global_data = vpc.evaluate_nodes(nodes_data, global_data, releases, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:

        assert global_data[2]['aggregate_cpu_failures'] in 'Expected: 12, Calculated: 39.1, Issues Found: 0'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 135.50825119018555 Gi,' \
                                                              ' Issues Found: 0'
        assert global_data[4]['aggregate_kubelet_failures'] in 'Check Kubelet Version on nodes. Issues Found: 0'

    template_render(global_data, configs_data, storage_data, 'azure_terrform_multi_nodes_info.html')


def test_azure_multi_get_nested_nodes_info():
    vpc = createViyaPreInstallCheck()
    releases = (viya_constants.KUBELET_VERSION_14,
                viya_constants.KUBELET_VERSION_15,
                viya_constants.KUBELET_VERSION_16,
                viya_constants.KUBELET_VERSION_17)

    # debug = False
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'test_data/json_data/azure_multi_nodes_info.json')
    with open(datafile) as f:
        data = json.load(f)
    nodes_data = vpc.get_nested_nodes_info(data)

    storage_data = []
    configs_data = []

    global_data = []
    cluster_info = "Kubernetes master is running at https://node3:6443\n"
    quantity_ = register_pint()
    global_data = vpc.evaluate_nodes(nodes_data, global_data, releases, cluster_info, quantity_)
    pprint.pprint(global_data)
    for nodes in global_data:

        assert global_data[2]['aggregate_cpu_failures'] in 'Expected: 12, Calculated: 31.28, Issues Found: 0'
        assert global_data[3]['aggregate_memory_failures'] in 'Expected: 56G, Calculated: 93.6175537109375 Gi, ' \
                                                              'Issues Found: 0'
        assert global_data[4]['aggregate_kubelet_failures'] in '0, Check Kubelet Version on nodes.'

    template_render(global_data, configs_data, storage_data, 'azure_multi_nested_nodes_info.html')


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


def createViyaPreInstallCheck():
    sas_pre_check_report: ViyaPreInstallCheck = ViyaPreInstallCheck(sas_logger)
    return sas_pre_check_report


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
    assert namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS]in viya_constants.ADEQUATE_PERMS
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
