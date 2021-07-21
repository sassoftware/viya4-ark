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
import copy
import pytest

from typing import Dict, List

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as ReportKeys
from deployment_report.model.utils import relationship_util

from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
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
    rel: Dict = relationship_util.create_relationship_dict(KubernetesResource.Kinds.SERVICE, "foo")

    # make sure attributes are correct
    assert isinstance(rel, dict)
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.SERVICE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == "foo"


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_define_node_to_pod_relationships(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that the relationship between Nodes and Pods is correctly defined.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # call utils to define Node to Pod relationship
    relationship_util.define_node_to_pod_relationships(
        gathered_resources_copy[KubernetesResource.Kinds.NODE],
        gathered_resources_copy[KubernetesResource.Kinds.POD]
    )

    # get the node
    node: Dict = gathered_resources_copy[KubernetesResource.Kinds.NODE][ITEMS_KEY][TestVals.RESOURCE_NODE_1_NAME]

    # make sure the relationships were defined and all exist
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in node[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 6

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.POD
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_PROMETHEUS_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][1]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.POD
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][2]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.POD
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_CACHE_SERVER_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][3]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.POD
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_CAS_OPERATOR_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][4]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.POD
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_CAS_SERVER_POD_NAME

    # get the relationship
    rel: Dict = node[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][5]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.POD
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_POD_NAME


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_define_pod_to_service_relationships(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that the relationship between and pod and a service is correctly defined.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # reset the relationship lists for pods to make the service relationships easier to verify
    for pod in gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY].values():
        pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]: List = list()

    # call utils to define Pod to Service relationship
    relationship_util.define_pod_to_service_relationships(
        gathered_resources_copy[KubernetesResource.Kinds.POD],
        gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # prometheus pod

    # get the Pod resource
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][TestVals.COMPONENT_PROMETHEUS_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1

    # get the relationship
    rel: Dict = pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.SERVICE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_PROMETHEUS_SERVICE_NAME

    # sas-annotations pod

    # get the Pod resource
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1

    # get the relationship
    rel: Dict = pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.SERVICE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME

    # sas-cacheserver pod

    # get the Pod resource
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CACHE_SERVER_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1

    # get the relationship
    rel: Dict = pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.SERVICE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_CACHE_SERVER_SERVICE_NAME

    # sas-cas-operator pod

    # get the Pod resource
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_OPERATOR_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1

    # get the relationship
    rel: Dict = pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.SERVICE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_CAS_OPERATOR_SERVICE_NAME

    # sas-cas-server pod

    # get the Pod resource
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_SERVER_POD_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in pod[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 2

    # get the relationship
    rel: Dict = pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.SERVICE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_CAS_SERVER_SERVICE_NAME

    # get the relationship
    rel: Dict = pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][1]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.SERVICE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_CAS_SERVER_EXTNP_SERVICE_NAME


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_contour_used")
def test_define_service_to_ingress_relationships_contour(gathered_resources_all_ingress_defined_contour_used: Dict) \
        -> None:
    """
    This test verifies that the service to httpproxy relationships are correctly defined.

    :param gathered_resources_all_ingress_defined_contour_used: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_all_ingress_defined_contour_used)

    # call utils to define Service to HTTPProxy relationship
    relationship_util.define_service_to_ingress_relationships(SupportedIngress.Controllers.CONTOUR,
                                                              gathered_resources_copy)

    # get the Service resource
    service: Dict = gathered_resources_copy[KubernetesResource.Kinds.SERVICE][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in service[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1

    # get the relationship
    rel: Dict = service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.CONTOUR_HTTPPROXY
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == \
        TestVals.COMPONENT_SAS_ANNOTATIONS_CONTOUR_HTTPPROXY_NAME


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_istio_used")
def test_define_service_to_ingress_relationships_istio(gathered_resources_all_ingress_defined_istio_used: Dict) \
        -> None:
    """
    This test verifies that the service to virtual service relationships are correctly defined.

    :param gathered_resources_all_ingress_defined_istio_used: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_all_ingress_defined_istio_used)

    # call utils to define Service to VirtualService relationship
    relationship_util.define_service_to_ingress_relationships(SupportedIngress.Controllers.ISTIO,
                                                              gathered_resources_copy)

    # get the Service resource
    service: Dict = gathered_resources_copy[KubernetesResource.Kinds.SERVICE][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in service[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1

    # get the relationship
    rel: Dict = service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == \
        TestVals.COMPONENT_SAS_ANNOTATIONS_VIRTUAL_SERVICE_NAME


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_nginx_used")
def test_define_service_to_ingress_relationships_nginx(gathered_resources_all_ingress_defined_nginx_used: Dict) -> None:
    """
    This test verifies that the relationships between Services and Ingress objects are correctly defined.

    :param gathered_resources_all_ingress_defined_nginx_used: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_all_ingress_defined_nginx_used)

    # call utils to define Service to Ingress relationships for nginx
    relationship_util.define_service_to_ingress_relationships(SupportedIngress.Controllers.NGINX,
                                                              gathered_resources_copy)

    # get the Service details
    service: Dict = gathered_resources_copy[KubernetesResource.Kinds.SERVICE][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]

    # makes sure relationship is defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in service[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 2

    # get the first relationship
    rel: Dict = service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.INGRESS
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == \
           TestVals.COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME_DEPRECATED_DEFINITION

    # get the second relationship
    rel: Dict = service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][1]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.INGRESS
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == TestVals.COMPONENT_SAS_ANNOTATIONS_INGRESS_NAME


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_openshift_used")
def test_define_service_to_ingress_relationships_openshift(
        gathered_resources_all_ingress_defined_openshift_used: Dict) -> None:
    """
    This test verifies that the service to route relationships are correctly defined.

    :param gathered_resources_all_ingress_defined_openshift_used: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_all_ingress_defined_openshift_used)

    # call utils to define Service to Route relationship
    relationship_util.define_service_to_ingress_relationships(SupportedIngress.Controllers.OPENSHIFT,
                                                              gathered_resources_copy)

    # get the Service resource
    service: Dict = gathered_resources_copy[KubernetesResource.Kinds.SERVICE][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_SERVICE_NAME]

    # make sure the relationship was defined and exists
    assert ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST in service[ReportKeys.ResourceDetails.EXT_DICT]
    assert len(service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1

    # get the relationship
    rel: Dict = service[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST][0]

    # make sure the relationship attributes are correct
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.OPENSHIFT_ROUTE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == \
        TestVals.COMPONENT_SAS_ANNOTATIONS_OPENSHIFT_ROUTE_NAME
