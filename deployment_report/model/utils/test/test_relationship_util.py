####################################################################
# ### test_relationship_util.py                                  ###
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

from typing import Dict, Text

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as ReportKeys
from deployment_report.model.utils import relationship_util
from deployment_report.model.utils.test import conftest

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest

# create an alias to the test values
TestVals: KubectlTest.Values = KubectlTest.Values()


####################################################################
# Unit Tests                                                     ###
####################################################################
def test_create_relationship_dict() -> None:
    """
    This test verifies that a relationship dictionary is correctly created.
    """
    # create dictionary
    rel: Dict = relationship_util.create_relationship_dict(
        resource_name="foo",
        resource_type=ResourceTypeValues.K8S_CORE_SERVICES)

    # make sure attributes are correct
    assert isinstance(rel, dict)
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME] == "foo"
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE] == ResourceTypeValues.K8S_CORE_SERVICES


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_define_node_to_pod_relationships(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the relationship between Nodes and Pods is correctly defined.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict, relationships were defined when the fixture was created
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # get the node
    node: Dict = gathered_resources[ResourceTypeValues.K8S_CORE_NODES][ITEMS_KEY][TestVals.RESOURCE_NODE_1_NAME]

    # make sure the relationships were defined and all exist
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in node[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 6

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE] == ResourceTypeValues.K8S_CORE_PODS
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME] == TestVals.COMPONENT_PROMETHEUS_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][1]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE] == ResourceTypeValues.K8S_CORE_PODS
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME] == TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][2]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE] == ResourceTypeValues.K8S_CORE_PODS
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME] == \
           TestVals.COMPONENT_SAS_CACHE_SERVER_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][3]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE] == ResourceTypeValues.K8S_CORE_PODS
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME] == \
           TestVals.COMPONENT_SAS_CAS_OPERATOR_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][4]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE] == ResourceTypeValues.K8S_CORE_PODS
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME] == TestVals.COMPONENT_SAS_CAS_SERVER_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][5]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE] == ResourceTypeValues.K8S_CORE_PODS
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME] == \
           TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_POD_NAME


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_define_pod_to_service_relationships(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the relationship between and pod and a service is correctly defined.

    :param only_nginx_simulation_fixture: test fixture
    """
    # get the gathered_resources dict, relationships were defined when the fixture was created
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # prometheus pod

    # get the Pod resource
    pod: Dict = \
        gathered_resources[ResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][TestVals.COMPONENT_PROMETHEUS_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]

    for rel in pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_PROMETHEUS_SERVICE_NAME and \
                rel_type == ResourceTypeValues.K8S_CORE_SERVICES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail("expected service relationship wasn't found for prometheus pod")

    # sas-annotations pod

    # get the Pod resource
    pod: Dict = gathered_resources[ResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]

    for rel in pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME and \
                rel_type == ResourceTypeValues.K8S_CORE_SERVICES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail("expected service relationship wasn't found for sas-annotations pod")

    # sas-cacheserver pod

    # get the Pod resource
    pod: Dict = gathered_resources[ResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CACHE_SERVER_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]

    for rel in pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_CACHE_SERVER_SERVICE_NAME and \
                rel_type == ResourceTypeValues.K8S_CORE_SERVICES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail("expected service relationship wasn't found for sas-cache-server pod")

    # sas-cas-operator pod

    # get the Pod resource
    pod: Dict = gathered_resources[ResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_OPERATOR_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]

    for rel in pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_CAS_OPERATOR_SERVICE_NAME and \
                rel_type == ResourceTypeValues.K8S_CORE_SERVICES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail("expected service relationship wasn't found for sas-cas-operator pod")

    # sas-cas-server pod

    # get the Pod resource
    pod: Dict = gathered_resources[ResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_SERVER_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]

    for rel in pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_CAS_SERVER_SERVICE_NAME and \
                rel_type == ResourceTypeValues.K8S_CORE_SERVICES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail(f"expected {TestVals.COMPONENT_SAS_CAS_SERVER_SERVICE_NAME} service relationship not found for "
                    "sas-cas-server pod")

    for rel in pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_CAS_SERVER_EXTNP_SERVICE_NAME and \
                rel_type == ResourceTypeValues.K8S_CORE_SERVICES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail(f"expected {TestVals.COMPONENT_SAS_CAS_SERVER_EXTNP_SERVICE_NAME} service relationship not found "
                    "for sas-cas-server pod")


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_CONTOUR_USED_SIMULATION_FIXTURE)
def test_define_service_to_ingress_relationships_contour(
        all_available_contour_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the service to httpproxy relationships are correctly defined.

    :param all_available_contour_used_simulation_fixture: test fixture
    """
    # get the gathered_resources dict, relationships were defined when fixture was created
    gathered_resources: Dict = all_available_contour_used_simulation_fixture.resource_cache()

    # get the Service resource
    service: Dict = gathered_resources[ResourceTypeValues.K8S_CORE_SERVICES][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in service[ReportKeys.ResourceDetails.EXT_DICT]

    for rel in service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_ANNOTATIONS_CONTOUR_HTTPPROXY_NAME and \
                rel_type == ResourceTypeValues.CONTOUR_HTTP_PROXIES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail(f"expected {ResourceTypeValues.CONTOUR_HTTP_PROXIES} relationship wasn't found for "
                    "sas-annotations service")


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_ISTIO_USED_SIMULATION_FIXTURE)
def test_define_service_to_ingress_relationships_istio(
        all_available_istio_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the service to virtual service relationships are correctly defined.

    :param all_available_istio_used_simulation_fixture: test fixture
    """
    # get the gathered_resources dict, relationships were defined when the fixture was created
    gathered_resources: Dict = all_available_istio_used_simulation_fixture.resource_cache()

    # get the Service resource
    service: Dict = gathered_resources[ResourceTypeValues.K8S_CORE_SERVICES][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in service[ReportKeys.ResourceDetails.EXT_DICT]

    for rel in service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_ANNOTATIONS_VIRTUAL_SERVICE_NAME and \
                rel_type == ResourceTypeValues.ISTIO_VIRTUAL_SERVICES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail(f"expected {ResourceTypeValues.ISTIO_VIRTUAL_SERVICES} relationship not found for "
                    "sas-annotations service")


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_NGINX_USED_SIMULATION_FIXTURE)
def test_define_service_to_ingress_relationships_nginx(
        all_available_nginx_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the relationships between Services and Ingress objects are correctly defined.

    :param all_available_nginx_used_simulation_fixture: test fixture
    """
    # get the gathered_resources dict, relationships were defined when the fixture was created
    gathered_resources: Dict = all_available_nginx_used_simulation_fixture.resource_cache()

    # get the Service details
    service: Dict = gathered_resources[ResourceTypeValues.K8S_CORE_SERVICES][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]

    # makes sure relationship is defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in service[ReportKeys.ResourceDetails.EXT_DICT]

    for rel in service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME_DEPRECATED_DEFINITION and \
                rel_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail(f"expected {ResourceTypeValues.K8S_EXTENSIONS_INGRESSES} relationship not found for "
                    "sas-annotations service")

    for rel in service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME and \
                rel_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail(f"expected {ResourceTypeValues.K8S_NETWORKING_INGRESSES} relationship not found for "
                    "sas-annotations service")


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_OPENSHIFT_USED_SIMULATION_FIXTURE)
def test_define_service_to_ingress_relationships_openshift(
        all_available_openshift_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the service to route relationships are correctly defined.

    :param all_available_openshift_used_simulation_fixture: test fixture
    """
    # get the gathered_resources dict, relationships were defined when the fixture was created
    gathered_resources: Dict = all_available_openshift_used_simulation_fixture.resource_cache()

    # get the Service resource
    service: Dict = gathered_resources[ResourceTypeValues.K8S_CORE_SERVICES][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in service[ReportKeys.ResourceDetails.EXT_DICT]

    for rel in service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]:
        rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]
        # make sure the relationship attributes are correct
        if rel_name == TestVals.COMPONENT_SAS_ANNOTATIONS_OPENSHIFT_ROUTE_NAME and \
                rel_type == ResourceTypeValues.OPENSHIFT_ROUTES:
            # the expected relationship was found, break the loop
            break
    else:
        pytest.fail(f"expected {ResourceTypeValues.OPENSHIFT_ROUTES} relationship not found for sas-annotations "
                    "service")
