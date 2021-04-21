####################################################################
# ### test_viya_deployment_report_utils.py                       ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import copy
import pytest

from typing import Dict, List, Text

from deployment_report.model.static.viya_deployment_report_ingress_controller import \
    ViyaDeploymentReportIngressController as ExpectedIngressController
from deployment_report.model.static.viya_deployment_report_keys import ViyaDeploymentReportKeys as ReportKeys
from deployment_report.model.static.viya_deployment_report_keys import ITEMS_KEY
from deployment_report.model.utils.viya_deployment_report_utils import ViyaDeploymentReportUtils

from viya_ark_library.k8s.sas_k8s_objects import KubernetesApiResources, KubernetesResource
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest

# alias to KubectlTest.Values to shorten name
TestVals: KubectlTest.Values = KubectlTest.Values()


####################################################################
# Unit Test Fixtures                                             ###
####################################################################
@pytest.fixture(scope="module")
def gathered_resources() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is once at the beginning before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all Resources gathered starting with the Pods defined.
    """
    # set up kubectl and get API resources
    kubectl: KubectlTest = KubectlTest(ingress_simulator=KubectlTest.IngressSimulator.BOTH)
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # set up dict to hold gathered resources
    gathered_resources: Dict = dict()

    # create a list of resource kinds to gather
    # nodes and networking kinds do not typically have owning objects, so these need to be called individually
    kinds_list: List = [
        KubernetesResource.Kinds.CONFIGMAP,
        KubernetesResource.Kinds.INGRESS,
        KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE,
        KubernetesResource.Kinds.NODE,
        KubernetesResource.Kinds.POD,
        KubernetesResource.Kinds.SERVICE]

    for resource_kind in kinds_list:
        ViyaDeploymentReportUtils.gather_resource_details(
            kubectl=kubectl,
            gathered_resources=gathered_resources,
            api_resources=api_resources,
            resource_kind=resource_kind)

    return gathered_resources


####################################################################
# Unit Tests                                                     ###
####################################################################
def test_gather_resource_details(gathered_resources: Dict) -> None:
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.
    """
    # make sure the correct number of resources categories are defined
    assert len(gathered_resources) == TestVals.RESOURCE_KINDS_COUNT

    for kind in TestVals.RESOURCE_KINDS_LIST:
        assert kind in gathered_resources
        assert gathered_resources[kind][ReportKeys.KindDetails.AVAILABLE] is True


def test_gather_resource_details_cas_deployments(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about CASDeployment resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the CASDeployment count is correct
    assert gathered_resources[KubernetesResource.Kinds.CAS_DEPLOYMENT][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_CAS_DEPLOYMENT_COUNT

    for name in TestVals.RESOURCE_CAS_DEPLOYMENT_LIST:
        # make sure the expected CASDeployment is available by name
        assert name in gathered_resources[KubernetesResource.Kinds.CAS_DEPLOYMENT][ITEMS_KEY]

        # the CASDeployment object is a controller, make sure it has an ext.componentName definition
        assert ReportKeys.ResourceDetails.Ext.COMPONENT_NAME in \
            gathered_resources[KubernetesResource.Kinds.CAS_DEPLOYMENT][ITEMS_KEY][name][
                ReportKeys.ResourceDetails.EXT_DICT]


def test_gather_resource_details_cron_jobs(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about CronJob resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the CronJob count is correct
    assert gathered_resources[KubernetesResource.Kinds.CRON_JOB][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_CRON_JOB_COUNT

    for name in TestVals.RESOURCE_CRON_JOB_LIST:
        # make sure the expected CronJob is available by name
        assert name in gathered_resources[KubernetesResource.Kinds.CRON_JOB][ITEMS_KEY]

        # the CronJob object is a controller, make sure it has an ext.componentName definition
        assert ReportKeys.ResourceDetails.Ext.COMPONENT_NAME in gathered_resources[KubernetesResource.Kinds.CRON_JOB][
            ITEMS_KEY][name][ReportKeys.ResourceDetails.EXT_DICT]


def test_gather_resource_details_deployments(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about Deployment resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the Deployment resource count is correct
    assert gathered_resources[KubernetesResource.Kinds.DEPLOYMENT][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_DEPLOYMENT_COUNT

    for name in TestVals.RESOURCE_DEPLOYMENT_LIST:
        # make sure the expected Deployment is available by name
        assert name in gathered_resources[KubernetesResource.Kinds.DEPLOYMENT][ITEMS_KEY]

        # the Deployment object is a controller, make sure it has an ext.componentName definition
        assert ReportKeys.ResourceDetails.Ext.COMPONENT_NAME in \
            gathered_resources[KubernetesResource.Kinds.DEPLOYMENT][ITEMS_KEY][name][
                ReportKeys.ResourceDetails.EXT_DICT]


def test_gather_resource_details_ingresses(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about Ingress resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the Ingress resource count is correct
    assert gathered_resources[KubernetesResource.Kinds.INGRESS][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_INGRESS_COUNT

    for name in TestVals.RESOURCE_INGRESS_LIST:
        # make sure the expected Deployment is available by name
        # relationships have not yet been defined between Ingress and Service objects
        assert name in gathered_resources[KubernetesResource.Kinds.INGRESS][ITEMS_KEY]


def test_gather_resource_details_jobs(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about Job resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the Job resource count is correct
    assert gathered_resources[KubernetesResource.Kinds.JOB][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_JOB_COUNT

    for name in TestVals.RESOURCE_JOB_LIST:
        # make sure the expected Job is available by name
        assert name in gathered_resources[KubernetesResource.Kinds.JOB][ITEMS_KEY]

        # the Job object is owned by the CronJob object, make sure it has an ext.relationships definition with 1
        # relationship
        assert len(gathered_resources[KubernetesResource.Kinds.JOB][ITEMS_KEY][name][
            ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1


def test_gather_resource_details_pods(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about Pod resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the Pod resource count is correct
    assert gathered_resources[KubernetesResource.Kinds.POD][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_POD_COUNT

    for name in TestVals.RESOURCE_POD_LIST:
        # make sure the expected Pod is available by name
        assert name in gathered_resources[KubernetesResource.Kinds.POD][ITEMS_KEY]

        # the Pod object is owned by controller objects, make sure it has an ext.relationships definition with 1
        # relationship
        assert len(gathered_resources[KubernetesResource.Kinds.POD][ITEMS_KEY][name][
                       ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1


def test_gather_resource_details_replica_sets(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about ReplicaSet resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the ReplicaSet resource count is correct
    assert gathered_resources[KubernetesResource.Kinds.REPLICA_SET][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_REPLICA_SET_COUNT

    for name in TestVals.RESOURCE_REPLICA_SET_LIST:
        # make sure the expected ReplicaSet is available by name
        assert name in gathered_resources[KubernetesResource.Kinds.REPLICA_SET][ITEMS_KEY]

        # the ReplicaSet object is owned Deployment objects, make sure it has an ext.relationships definition with 1
        # relationship
        assert len(gathered_resources[KubernetesResource.Kinds.REPLICA_SET][ITEMS_KEY][name][
                       ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1


def test_gather_resource_details_services(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about Service resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the Service resource count is correct
    assert gathered_resources[KubernetesResource.Kinds.SERVICE][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_SERVICE_COUNT

    for name in TestVals.RESOURCE_SERVICE_LIST:
        # make sure the expected Service is available by name
        # relationships to pods and networking objects have not yet been made
        assert name in gathered_resources[KubernetesResource.Kinds.SERVICE][ITEMS_KEY]


def test_gather_resource_details_stateful_sets(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about StatefulSet resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the StatefulSet resource count is correct
    assert gathered_resources[KubernetesResource.Kinds.STATEFUL_SET][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_STATEFUL_SET_COUNT

    # make sure the expected StatefulSet is available by name
    assert TestVals.COMPONENT_SAS_CACHE_SERVER_STATEFUL_SET_NAME in \
        gathered_resources[KubernetesResource.Kinds.STATEFUL_SET][ITEMS_KEY]

    # the StatefulSet object is a controller, make sure it has an ext.componentName definition
    assert ReportKeys.ResourceDetails.Ext.COMPONENT_NAME in gathered_resources[KubernetesResource.Kinds.STATEFUL_SET][
        ITEMS_KEY][TestVals.COMPONENT_SAS_CACHE_SERVER_STATEFUL_SET_NAME][ReportKeys.ResourceDetails.EXT_DICT]


def test_gather_resource_details_virtual_services(gathered_resources: Dict) -> None:
    """
    This test verifies that expected details about VirtualService resources are in the gathered details.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # make sure the VirtualService resource count is correct
    assert gathered_resources[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_VIRTUAL_SERVICE_COUNT

    for name in TestVals.RESOURCE_VIRTUAL_SERVICE_LIST:
        # make sure the expected VirtualService is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resources[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE][ITEMS_KEY]


def test_gather_resource_details_from_services() -> None:
    """
    This test verifies that all Services are gathered. The CAS Services have owning objects which will also cause
    Deployments and CASDeployments to be discovered. This test is only concerned with Services and is meant to verify
    that gather_resource_details() doesn't raise an error if Pods are not available.
    """
    # set up kubectl and get API resources
    kubectl: KubectlTest = KubectlTest()
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # set up dict to hold gathered resources
    gathered_resources: Dict = dict()

    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.SERVICE)

    # make sure the correct number of resource categories were returned
    assert len(gathered_resources) == 3

    # make sure the correct number of services were returned
    assert gathered_resources[KubernetesResource.Kinds.SERVICE][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_SERVICE_COUNT

    # make sure the expected Services are available by name
    for service_name in TestVals.RESOURCE_SERVICE_LIST:
        assert service_name in gathered_resources[KubernetesResource.Kinds.SERVICE][ITEMS_KEY]


def test_gather_resource_details_from_ingresses() -> None:
    """
    This test verifies that all Ingresses are gathered. The ingress object doesn't have an owner, so only Ingresses
    will be gathered. This test is mean to make sure gather_resource_details() doesn't raise an error if other
    resources aren't available.
    """
    # set up kubectl and get API resources
    kubectl: KubectlTest = KubectlTest()
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # set up dict to hold gathered resources
    gathered_resources: Dict = dict()

    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.INGRESS)

    # make sure the correct number of resource categories were returned
    assert len(gathered_resources) == 1

    # make sure the correct number of Ingress objects were returned
    assert gathered_resources[KubernetesResource.Kinds.INGRESS][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_INGRESS_COUNT

    # make sure the expected Ingress is available
    for name in TestVals.RESOURCE_INGRESS_LIST:
        assert name in gathered_resources[KubernetesResource.Kinds.INGRESS][ITEMS_KEY]


def test_gather_resource_details_from_virtual_services() -> None:
    """
    This test verifies that all VirtualServices are gathered. The VirtualService object doesn't have an owner,
    so only VirtualServices will be gathered.
    """
    # set up kubectl and get API resources
    kubectl: KubectlTest = KubectlTest(ingress_simulator=KubectlTest.IngressSimulator.ISTIO_ONLY)
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # set up dict to hold gathered resources
    gathered_resources: Dict = dict()

    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE)

    # make sure the correct number of resource categories were returned
    assert len(gathered_resources) == 1

    # make sure the correct number of VirtualService objects were returned
    assert gathered_resources[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_VIRTUAL_SERVICE_COUNT

    # make sure the expected VirtualService is available
    for name in TestVals.RESOURCE_VIRTUAL_SERVICE_LIST:
        assert name in gathered_resources[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE][ITEMS_KEY]


def test_define_service_to_ingress_relationships(gathered_resources: Dict) -> None:
    """
    This test verifies that the relationships between Services and Ingress objects are correctly defined.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # call utils to define Service to Ingress relationships
    ViyaDeploymentReportUtils.define_service_to_ingress_relationships(
        gathered_resources_copy[KubernetesResource.Kinds.SERVICE],
        gathered_resources_copy[KubernetesResource.Kinds.INGRESS]
    )

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


def test_define_service_to_virtual_service_relationships(gathered_resources: Dict) -> None:
    """
    This test verifies that the service to virtual service relationships are correctly defined.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # call utils to define Service to VirtualService relationship
    ViyaDeploymentReportUtils.define_service_to_virtual_service_relationships(
        gathered_resources_copy[KubernetesResource.Kinds.SERVICE],
        gathered_resources_copy[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE]
    )

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


def test_define_pod_to_service_relationships(gathered_resources: Dict) -> None:
    """
    This test verifies that the relationship between and pod and a service is correctly defined.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # reset the relationship lists for pods to make the service relationships easier to verify
    for pod in gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY].values():
        pod[ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]: List = list()

    # call utils to define Pod to Service relationship
    ViyaDeploymentReportUtils.define_pod_to_service_relationships(
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


def test_define_node_to_pod_relationships(gathered_resources: Dict) -> None:
    """
    This test verifies that the relationship between Nodes and Pods is correctly defined.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # call utils to define Node to Pod relationship
    ViyaDeploymentReportUtils.define_node_to_pod_relationships(
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


def test_create_relationship_dict() -> None:
    """
    This test verifies that a relationship dictionary is correctly created.
    """
    # create dictionary
    rel: Dict = ViyaDeploymentReportUtils._create_relationship_dict(KubernetesResource.Kinds.SERVICE, "foo")

    # make sure attributes are correct
    assert isinstance(rel, dict)
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == KubernetesResource.Kinds.SERVICE
    assert rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == "foo"


def test_get_pod_metrics(gathered_resources: Dict) -> None:
    """
    This test verifies that pod metrics are correctly defined per pod when metrics are available.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # get the list of all pods
    pods: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD]

    # add the metrics
    ViyaDeploymentReportUtils.get_pod_metrics(kubectl=KubectlTest(), pods=pods)

    # verify that the metrics were added
    for pod in pods[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT in pod[ReportKeys.ResourceDetails.EXT_DICT]


def test_get_pod_metrics_unavailable(gathered_resources: Dict) -> None:
    """
    This test verifies that no errors are raised when pod metrics are not available.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # get the list of all pods
    pods: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD]

    # try to add the metrics
    ViyaDeploymentReportUtils.get_pod_metrics(kubectl=KubectlTest(include_metrics=False), pods=pods)

    # make sure the metrics dictionary was not added
    for pod in pods[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT not in pod[ReportKeys.ResourceDetails.EXT_DICT]


def test_get_node_metrics(gathered_resources: Dict) -> None:
    """
    This test verifies that node metrics are correctly defined per node when metrics are available.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # get the list of all nodes
    nodes: Dict = gathered_resources_copy[KubernetesResource.Kinds.NODE]

    # add the metrics
    ViyaDeploymentReportUtils.get_node_metrics(kubectl=KubectlTest(), nodes=nodes)

    # make sure the metrics were added
    for node in nodes[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT in node[ReportKeys.ResourceDetails.EXT_DICT]


def test_get_node_metrics_unavailable(gathered_resources: Dict) -> None:
    """
    This test verifies that no errors are raised when pod metrics are not available.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # get the list of all nodes
    nodes: Dict = gathered_resources_copy[KubernetesResource.Kinds.NODE]

    # try to add the metrics
    ViyaDeploymentReportUtils.get_node_metrics(kubectl=KubectlTest(include_metrics=False), nodes=nodes)

    # make sure the metrics dictionary was not added
    for node in nodes[ITEMS_KEY].values():
        assert ReportKeys.ResourceDetails.Ext.METRICS_DICT not in node[ReportKeys.ResourceDetails.EXT_DICT]


def test_determine_ingress_controller_nginx_only() -> None:
    """
    This test verifies that the ingress controller is correctly determined when only Ingress objects are available.
    """
    # create a KubectlTest instance configured to simulate only NGINX artifacts
    kubectl: KubectlTest = KubectlTest(ingress_simulator=KubectlTest.IngressSimulator.NGINX_ONLY)

    # get the list of api-resources with only NGINX kinds
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # create a dictionary to hold the gathered resources
    gathered_resources: Dict = dict()

    # gather Ingress objects
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.INGRESS
    )

    # gather VirtualService objects (this is how the ViyaDeploymentReport behaves)
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE
    )

    # call the utility method to determine the ingress controller
    ingress_controller: Text = ViyaDeploymentReportUtils.determine_ingress_controller(gathered_resources)

    # assert that NGINX controller was determined
    assert ingress_controller == ExpectedIngressController.KUBE_NGINX


def test_determine_ingress_controller_istio_only() -> None:
    """
    This test verifies that the ingress controller is correctly determined when only VirtualService objects are
    available.
    """
    # create a KubectlTest object configured to simulate only ISTIO artifacts
    kubectl: KubectlTest = KubectlTest(ingress_simulator=KubectlTest.IngressSimulator.ISTIO_ONLY)

    # get the api-resources without Ingress objects
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # create dictionary to hold gathered resources
    gathered_resources: Dict = dict()

    # gather Ingress objects (this is how ViyaDeploymentReport behaves)
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.INGRESS
    )

    # gather VirtualService objects
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE
    )

    # call the utility method to determine the ingress controller
    ingress_controller: Text = ViyaDeploymentReportUtils.determine_ingress_controller(gathered_resources)

    # assert that ISTIO controller was determined
    assert ingress_controller == ExpectedIngressController.ISTIO


def test_determine_ingress_controller_both_nginx_used() -> None:
    """
    This test verifies that the ingress controller is correctly determined when both Ingress and VirtualService
    resources are defined, but only Ingress objects are available.
    """
    # create a KubectlTest object configured to simulate having both resources but only Ingress objects created
    kubectl: KubectlTest = KubectlTest(ingress_simulator=KubectlTest.IngressSimulator.BOTH_RESOURCES_NGINX_USED)

    # get the api-resources with VirtualService and Ingress available
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # create a dictionary to hold the gathered resources
    gathered_resources: Dict = dict()

    # gather Ingress objects
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.INGRESS
    )

    # gather VirtualService objects
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE
    )

    # call the utility method to determine the ingress controller
    ingress_controller: Text = ViyaDeploymentReportUtils.determine_ingress_controller(gathered_resources)

    # assert that NGINX controller was determined
    assert ingress_controller == ExpectedIngressController.KUBE_NGINX


def test_determine_ingress_controller_both_istio_used() -> None:
    """
    This test verifies that the ingress controller is correctly determined when both Ingress and VirtualService
    resources are defined, but only VirtualService objects are available.
    """
    # create a KubectlTest object configured to simulate having both resources but only VirtualService objects created
    kubectl: KubectlTest = KubectlTest(ingress_simulator=KubectlTest.IngressSimulator.BOTH_RESOURCES_ISTIO_USED)

    # get the api-resources with both Ingress and VirtualService defined
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # create a dictionary to hold gathered resources
    gathered_resources: Dict = dict()

    # gather Ingress objects
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.INGRESS
    )

    # gather VirtualService objects
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE
    )

    # call the utility method to determine the ingress controller
    ingress_controller: Text = ViyaDeploymentReportUtils.determine_ingress_controller(gathered_resources)

    # assert that ISTIO controller was determined
    assert ingress_controller == ExpectedIngressController.ISTIO


def test_determine_ingress_controller_both(gathered_resources: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when both Ingress and VirtualService
    resources are defined, and both objects are available. This code path should determine the controller to be NGINIX
    as that is the first kind checked for.
    """
    # call the utility method to determine the ingress controller
    ingress_controller: Text = ViyaDeploymentReportUtils.determine_ingress_controller(gathered_resources)

    # assert that NGINX controller was not determined
    assert ingress_controller is ExpectedIngressController.KUBE_NGINX


def test_determine_ingress_controller_none() -> None:
    """
    This test verifies that a None value is returned for the ingress controller when neither Ingress or VirtualService
    objects are available.
    """
    # create a KubectlTest object configured to have neither Ingress or VirtualService
    kubectl: KubectlTest = KubectlTest(ingress_simulator=KubectlTest.IngressSimulator.NONE)

    # get the api-resources without Ingress or VirtualService
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # create a dictionary to hold gathered resources
    gathered_resources: Dict = dict()

    # gather Ingress objects
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.INGRESS
    )

    # gather VirtualService objects
    ViyaDeploymentReportUtils.gather_resource_details(
        kubectl=kubectl,
        gathered_resources=gathered_resources,
        api_resources=api_resources,
        resource_kind=KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE
    )

    # call the utility method to determine the ingress controller
    ingress_controller: Text = ViyaDeploymentReportUtils.determine_ingress_controller(gathered_resources)

    # assert that a controller was not determined
    assert ingress_controller is None


def test_aggregate_component_resources_prometheus(gathered_resources: Dict) -> None:
    """
    This test verifies that all resources which comprise the prometheus component are correctly aggregated to create
    the component definition.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # define pod to service relationships to allow for aggregation
    ViyaDeploymentReportUtils.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the prometheus pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][TestVals.COMPONENT_PROMETHEUS_POD_NAME]

    # aggregate the resources in the prometheus component
    ViyaDeploymentReportUtils.aggregate_component_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the correct number of resources were aggregated
    assert len(component) == TestVals.COMPONENT_PROMETHEUS_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_PROMETHEUS_RESOURCES_DICT.items():
        assert kind in component
        assert len(component[kind]) == len(name_list)
        for name in name_list:
            assert name in component[kind]


def test_aggregate_component_resources_sas_annotations(gathered_resources: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # define the pod to service relationships to allow for aggregation
    ViyaDeploymentReportUtils.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    ViyaDeploymentReportUtils.define_service_to_ingress_relationships(
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE],
        ingresses=gathered_resources_copy[KubernetesResource.Kinds.INGRESS]
    )

    # define the service to virtual service relationships to allow for aggregation
    ViyaDeploymentReportUtils.define_service_to_virtual_service_relationships(
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE],
        virtual_services=gathered_resources_copy[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE]
    )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    ViyaDeploymentReportUtils.aggregate_component_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the correct number of resource types were aggregated
    assert len(component) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT.items():
        assert kind in component
        assert len(component[kind]) == len(name_list)
        for name in name_list:
            assert name in component[kind]


def test_aggregate_component_resources_sas_cache_server(gathered_resources: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-cacheserver component are correctly aggregated to
    create the component definition.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # define the pod to service relationships to allow for aggregation
    ViyaDeploymentReportUtils.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-cacheserver pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CACHE_SERVER_POD_NAME]

    # aggregate the resources
    ViyaDeploymentReportUtils.aggregate_component_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the right number of resource types were aggregated
    assert len(component) == TestVals.COMPONENT_SAS_CACHE_SERVER_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_CACHE_SERVER_RESOURCE_DICT.items():
        assert kind in component
        assert len(component[kind]) == len(name_list)
        for name in name_list:
            assert name in component[kind]


def test_aggregate_component_resources_sas_cas_operator(gathered_resources: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-cas-operator component are correctly aggregated to
    create the component definition.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # define the pod to service relationships to allow for aggregation
    ViyaDeploymentReportUtils.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-cas-operator pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_OPERATOR_POD_NAME]

    # aggregate the resources
    ViyaDeploymentReportUtils.aggregate_component_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the correct number of resource types were aggregated
    assert len(component) == TestVals.COMPONENT_SAS_CAS_OPERATOR_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_CAS_OPERATOR_RESOURCE_DICT.items():
        assert kind in component
        assert len(component[kind]) == len(name_list)
        for name in name_list:
            assert name in component[kind]


def test_aggregate_component_resources_sas_cas_server(gathered_resources: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-cas-server component are correctly aggregated to
    create the component definition.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # define the pod to service relationships to allow for aggregation
    ViyaDeploymentReportUtils.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-cas-server pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_SERVER_POD_NAME]

    # aggregate the resources
    ViyaDeploymentReportUtils.aggregate_component_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the correct number of resource types were aggregated
    assert len(component) == TestVals.COMPONENT_SAS_CAS_SERVER_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_CAS_SERVER_RESOURCE_DICT.items():
        assert kind in component
        assert len(component[kind]) == len(name_list)
        for name in name_list:
            assert name in component[kind]


def test_aggregate_component_resources_sas_scheduled_backup_job(gathered_resources: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-scheduled-backup-job component are correctly aggregated
    to create the component definition.

    :param gathered_resources: The dictionary of all gathered resources provided by the gathered_resources fixture.
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources)

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-scheduled-backup-job pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_POD_NAME]

    # aggregate the resources
    ViyaDeploymentReportUtils.aggregate_component_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the correct number of resource types were aggregated
    assert len(component) == TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_RESOURCE_DICT.items():
        assert kind in component
        assert len(component[kind]) == len(name_list)
        for name in name_list:
            assert name in component[kind]
