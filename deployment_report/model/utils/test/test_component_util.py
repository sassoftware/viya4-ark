####################################################################
# ### test_component_util.py                                     ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import pytest

from typing import Dict

from deployment_report.model.static.viya_deployment_report_keys import ITEMS_KEY, NAME_KEY
from deployment_report.model.utils import component_util
from deployment_report.model.utils.test import conftest

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest

# create alias to KubectlTest Values class
TestVals: KubectlTest.Values = KubectlTest.Values()


####################################################################
# Unit Tests                                                     ###
####################################################################
@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_aggregate_resources_prometheus(only_nginx_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the prometheus component are correctly aggregated to create
    the full component definition.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the prometheus pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_PROMETHEUS_POD_NAME]

    # aggregate the resources in the prometheus component
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_PROMETHEUS_NAME

    # make sure the correct number of resources were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_PROMETHEUS_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_PROMETHEUS_RESOURCES_DICT.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.NO_INGRESS_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_annotations_no_ingress(no_ingress_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the full component definition when no ingress is found.

    :param no_ingress_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = no_ingress_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NO_INGRESS

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NO_INGRESS.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_CONTOUR_USED_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_annotations_all_available_contour_used(
        all_available_contour_used_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when all ingress resource types are present but Contour is providing ingress
    control.

    :param all_available_contour_used_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = all_available_contour_used_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_CONTOUR

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_CONTOUR.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_ISTIO_USED_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_annotations_all_available_istio_used(
        all_available_istio_used_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when all ingress resource types are defined but Istio is providing ingress control.

    :param all_available_istio_used_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = all_available_istio_used_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_ISTIO

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_ISTIO.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_NGINX_USED_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_annotations_all_available_nginx_used(
        all_available_nginx_used_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when all ingress resource types are defined but NGINX is providing ingress control.

    :param all_available_nginx_used_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = all_available_nginx_used_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NGINX

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NGINX.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_OPENSHIFT_USED_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_annotations_all_available_openshift_used(
        all_available_openshift_used_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when all ingress resource types are defined but OpenShift is providing ingress
    control.

    :param all_available_openshift_used_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = all_available_openshift_used_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_OPENSHIFT

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_OPENSHIFT.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ONLY_CONTOUR_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_annotations_only_contour(only_contour_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when only Contour resources are found.

    :param only_contour_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_contour_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_CONTOUR

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_CONTOUR.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ONLY_ISTIO_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_annotations_only_istio(only_istio_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when only Istio resources are found.

    :param only_istio_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_istio_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_ISTIO

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_ISTIO.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_annotations_only_nginx(only_nginx_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when only NGINX resources are found.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NGINX

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NGINX.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ONLY_OPENSHIFT_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_annotations_only_openshift(only_openshift_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when only OpenShift resources are found.

    :param only_openshift_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_openshift_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_OPENSHIFT

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_OPENSHIFT.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_cache_server(only_nginx_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-cacheserver component are correctly aggregated to
    create the component definition.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-cacheserver pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CACHE_SERVER_POD_NAME]

    # aggregate the resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_CACHE_SERVER_NAME

    # make sure the right number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_CACHE_SERVER_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_CACHE_SERVER_RESOURCE_DICT.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_cas_operator(only_nginx_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-cas-operator component are correctly aggregated to
    create the component definition.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-cas-operator pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_OPERATOR_POD_NAME]

    # aggregate the resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_CAS_OPERATOR_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_CAS_OPERATOR_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_CAS_OPERATOR_RESOURCE_DICT.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_cas_server(only_nginx_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-cas-server component are correctly aggregated to
    create the component definition.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-cas-server pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_SERVER_POD_NAME]

    # aggregate the resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_CAS_SERVER_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_CAS_SERVER_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_CAS_SERVER_RESOURCE_DICT.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_aggregate_resources_sas_scheduled_backup_job(only_nginx_simulation_fixture: conftest.DSA):
    """
    This test verifies that all resources which comprise the sas-scheduled-backup-job component are correctly aggregated
    to create the component definition.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-scheduled-backup-job pod
    pod: Dict = gathered_resources[KubernetesResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_POD_NAME]

    # aggregate the resources
    component_util.aggregate_resources(resource_details=pod,
                                       component=component,
                                       resource_cache=gathered_resources)

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for resource_type, name_list in TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_RESOURCE_DICT.items():
        assert resource_type in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][resource_type]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][resource_type]
