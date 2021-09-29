####################################################################
# ### test_resource_util.py                                      ###
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

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as ReportKeys
from deployment_report.model.utils.test import conftest

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest

# alias to KubectlTest.Values to shorten name
TestVals: KubectlTest.Values = KubectlTest.Values()


####################################################################
# Unit Tests                                                     ###
####################################################################
@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_NGINX_USED_SIMULATION_FIXTURE)
def test_gather_details_all_resources(
        all_available_nginx_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param all_available_nginx_used_simulation_fixture: test fixture
    """
    gathered_resources: Dict = all_available_nginx_used_simulation_fixture.resource_cache()

    # make sure the correct number of resources categories are defined

    assert len(gathered_resources) == TestVals.RESOURCE_LIST_ALL_COUNT

    for kind in TestVals.RESOURCE_LIST_ALL:
        assert kind in gathered_resources
        assert gathered_resources[kind][ReportKeys.ResourceTypeDetails.AVAILABLE] is True


@pytest.mark.usefixtures(conftest.ONLY_CONTOUR_SIMULATION_FIXTURE)
def test_gather_details_only_contour(only_contour_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param only_contour_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_contour_simulation_fixture.resource_cache()

    # make sure the correct number of resources categories are defined
    assert len(gathered_resources) == TestVals.RESOURCE_LIST_CONTOUR_COUNT

    for kind in TestVals.RESOURCE_LIST_CONTOUR:
        assert kind in gathered_resources
        assert gathered_resources[kind][ReportKeys.ResourceTypeDetails.AVAILABLE] is True


@pytest.mark.usefixtures(conftest.ONLY_ISTIO_SIMULATION_FIXTURE)
def test_gather_details_only_istio(only_istio_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param only_istio_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_istio_simulation_fixture.resource_cache()

    # make sure the correct number of resources categories are defined
    assert len(gathered_resources) == TestVals.RESOURCE_LIST_ISTIO_COUNT

    for kind in TestVals.RESOURCE_LIST_ISTIO:
        assert kind in gathered_resources
        assert gathered_resources[kind][ReportKeys.ResourceTypeDetails.AVAILABLE] is True


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_only_nginx(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the correct number of resources categories are defined
    assert len(gathered_resources) == TestVals.RESOURCE_LIST_NGINX_COUNT

    for kind in TestVals.RESOURCE_LIST_NGINX:
        assert kind in gathered_resources
        assert gathered_resources[kind][ReportKeys.ResourceTypeDetails.AVAILABLE] is True


@pytest.mark.usefixtures(conftest.ONLY_OPENSHIFT_SIMULATION_FIXTURE)
def test_gather_details_only_openshift(only_openshift_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param only_openshift_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_openshift_simulation_fixture.resource_cache()

    # make sure the correct number of resources categories are defined
    assert len(gathered_resources) == TestVals.RESOURCE_LIST_OPENSHIFT_COUNT

    for kind in TestVals.RESOURCE_LIST_OPENSHIFT:
        assert kind in gathered_resources
        assert gathered_resources[kind][ReportKeys.ResourceTypeDetails.AVAILABLE] is True


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_cas_deployments(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about CASDeployment resources are in the gathered details.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the CASDeployment count is correct
    assert gathered_resources[ResourceTypeValues.SAS_CAS_DEPLOYMENTS][ReportKeys.ResourceTypeDetails.COUNT] == \
           TestVals.RESOURCE_CAS_DEPLOYMENT_COUNT

    for name in TestVals.RESOURCE_CAS_DEPLOYMENT_LIST:
        # make sure the expected CASDeployment is available by name
        assert name in gathered_resources[ResourceTypeValues.SAS_CAS_DEPLOYMENTS][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_cron_jobs(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about CronJob resources are in the gathered details.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_details: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the CronJob count is correct
    assert gathered_details[ResourceTypeValues.K8S_BATCH_CRON_JOBS][ReportKeys.ResourceTypeDetails.COUNT] == \
           TestVals.RESOURCE_CRON_JOB_COUNT

    for name in TestVals.RESOURCE_CRON_JOB_LIST:
        # make sure the expected CronJob is available by name
        assert name in gathered_details[ResourceTypeValues.K8S_BATCH_CRON_JOBS][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_deployments(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts) -> None:
    """
    This test verifies that expected details about Deployment resources are in the gathered details.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the Deployment resource count is correct
    assert gathered_resources[ResourceTypeValues.K8S_APPS_DEPLOYMENTS][ReportKeys.ResourceTypeDetails.COUNT] == \
           TestVals.RESOURCE_DEPLOYMENT_COUNT

    for name in TestVals.RESOURCE_DEPLOYMENT_LIST:
        # make sure the expected Deployment is available by name
        assert name in gathered_resources[ResourceTypeValues.K8S_APPS_DEPLOYMENTS][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_CONTOUR_USED_SIMULATION_FIXTURE)
def test_gather_details_httpproxy_all_available_contour_used(
        all_available_contour_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about HTTPProxy resources are in the gathered details.

    :param all_available_contour_used_simulation_fixture: test fixture
    """
    gathered_resources: Dict = all_available_contour_used_simulation_fixture.resource_cache()

    # make sure the HTTPProxy resource count is correct
    assert gathered_resources[ResourceTypeValues.CONTOUR_HTTP_PROXIES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_HTTPPROXY_COUNT

    for name in TestVals.RESOURCE_HTTPPROXY_LIST:
        # make sure the expected HTTPProxy is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resources[ResourceTypeValues.CONTOUR_HTTP_PROXIES][
            ITEMS_KEY]


@pytest.mark.usefixtures(conftest.ONLY_CONTOUR_SIMULATION_FIXTURE)
def test_gather_details_httpproxy_only_contour(only_contour_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about HTTPProxy resources are in the gathered details.

    :param only_contour_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_contour_simulation_fixture.resource_cache()

    # make sure the HTTPProxy resource count is correct
    assert gathered_resources[ResourceTypeValues.CONTOUR_HTTP_PROXIES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_HTTPPROXY_COUNT

    for name in TestVals.RESOURCE_HTTPPROXY_LIST:
        # make sure the expected HTTPProxy is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resources[ResourceTypeValues.CONTOUR_HTTP_PROXIES][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.NO_INGRESS_SIMULATION_FIXTURE)
def test_gather_details_httpproxy_no_ingress(no_ingress_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that no details are gathered about HTTPProxy resources if no ingress kinds are found.

    :param no_ingress_simulation_fixture: test fixture
    """
    assert ResourceTypeValues.CONTOUR_HTTP_PROXIES not in no_ingress_simulation_fixture.resource_cache()


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_NGINX_USED_SIMULATION_FIXTURE)
def test_gather_details_ingresses_all_nginx_used(
        all_available_nginx_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about Ingress resources are in the gathered details.

    :param all_available_nginx_used_simulation_fixture: test fixture.
    """
    gathered_resources: Dict = all_available_nginx_used_simulation_fixture.resource_cache()

    # make sure the Ingress resource count is correct
    assert gathered_resources[ResourceTypeValues.K8S_NETWORKING_INGRESSES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_NETWORKING_INGRESS_COUNT

    for name in TestVals.RESOURCE_NETWORKING_INGRESS_LIST:
        # make sure the expected Deployment is available by name
        # relationships have not yet been defined between Ingress and Service objects
        assert name in gathered_resources[ResourceTypeValues.K8S_NETWORKING_INGRESSES][ITEMS_KEY]

    assert gathered_resources[ResourceTypeValues.K8S_EXTENSIONS_INGRESSES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_EXTENSIONS_INGRESS_COUNT

    for name in TestVals.RESOURCE_EXTENSIONS_INGRESS_LIST:
        # make sure the expected Deployment is available by name
        # relationships have not yet been defined between Ingress and Service objects
        assert name in gathered_resources[ResourceTypeValues.K8S_EXTENSIONS_INGRESSES][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_ingresses_only_nginx(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about Ingress resources are in the gathered details.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the Ingress resource count is correct
    assert gathered_resources[ResourceTypeValues.K8S_NETWORKING_INGRESSES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_NETWORKING_INGRESS_COUNT

    for name in TestVals.RESOURCE_NETWORKING_INGRESS_LIST:
        # make sure the expected Deployment is available by name
        # relationships have not yet been defined between Ingress and Service objects
        assert name in gathered_resources[ResourceTypeValues.K8S_NETWORKING_INGRESSES][ITEMS_KEY]

    assert gathered_resources[ResourceTypeValues.K8S_EXTENSIONS_INGRESSES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_EXTENSIONS_INGRESS_COUNT

    for name in TestVals.RESOURCE_EXTENSIONS_INGRESS_LIST:
        # make sure the expected Deployment is available by name
        # relationships have not yet been defined between Ingress and Service objects
        assert name in gathered_resources[ResourceTypeValues.K8S_EXTENSIONS_INGRESSES][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.NO_INGRESS_SIMULATION_FIXTURE)
def test_gather_details_ingresses_no_ingress(no_ingress_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that no details are gathered about Ingress resources if no ingress kinds are found.

    :param no_ingress_simulation_fixture: test fixture
    """
    assert ResourceTypeValues.K8S_EXTENSIONS_INGRESSES not in no_ingress_simulation_fixture.resource_cache()


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_jobs(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about Job resources are in the gathered details.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_resource: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the Job resource count is correct
    assert gathered_resource[ResourceTypeValues.K8S_BATCH_JOBS][ReportKeys.ResourceTypeDetails.COUNT] == \
           TestVals.RESOURCE_JOB_COUNT

    for name in TestVals.RESOURCE_JOB_LIST:
        # make sure the expected Job is available by name
        assert name in gathered_resource[ResourceTypeValues.K8S_BATCH_JOBS][ITEMS_KEY]

        # the Job object is owned by the CronJob object, make sure it has an ext.relationships definition with 1
        # relationship
        assert len(gathered_resource[ResourceTypeValues.K8S_BATCH_JOBS][ITEMS_KEY][name][
            ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_pods(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about Pod resources are in the gathered details.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_resource: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the Pod resource count is correct
    assert gathered_resource[ResourceTypeValues.K8S_CORE_PODS][ReportKeys.ResourceTypeDetails.COUNT] == \
           TestVals.RESOURCE_POD_COUNT

    for name in TestVals.RESOURCE_POD_LIST:
        # make sure the expected Pod is available by name
        assert name in gathered_resource[ResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY]

        # the Pod object is owned by controller objects and may be related to a service, make sure at least 1
        # relationship is defined
        assert len(gathered_resource[ResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY][name][
                       ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) > 0


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_replica_sets(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about ReplicaSet resources are in the gathered details.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the ReplicaSet resource count is correct
    assert gathered_resources[ResourceTypeValues.K8S_APPS_REPLICA_SETS][ReportKeys.ResourceTypeDetails.COUNT] == \
           TestVals.RESOURCE_REPLICA_SET_COUNT

    for name in TestVals.RESOURCE_REPLICA_SET_LIST:
        # make sure the expected ReplicaSet is available by name
        assert name in gathered_resources[ResourceTypeValues.K8S_APPS_REPLICA_SETS][ITEMS_KEY]

        # the ReplicaSet object is owned Deployment objects, make sure it has an ext.relationships definition with 1
        # relationship
        assert len(gathered_resources[ResourceTypeValues.K8S_APPS_REPLICA_SETS][ITEMS_KEY][name][
                       ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_OPENSHIFT_USED_SIMULATION_FIXTURE)
def test_gather_details_route_all_openshift_used(
        all_available_openshift_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about Route resources are in the gathered details.

    :param all_available_openshift_used_simulation_fixture: test fixture
    """
    gathered_resources: Dict = all_available_openshift_used_simulation_fixture.resource_cache()

    # make sure the Route resource count is correct
    assert gathered_resources[ResourceTypeValues.OPENSHIFT_ROUTES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_ROUTE_COUNT

    for name in TestVals.RESOURCE_ROUTE_LIST:
        # make sure the expected Route is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resources[ResourceTypeValues.OPENSHIFT_ROUTES][
            ITEMS_KEY]


@pytest.mark.usefixtures(conftest.ONLY_OPENSHIFT_SIMULATION_FIXTURE)
def test_gather_details_route_only_openshift(only_openshift_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about Route resources are in the gathered details.

    :param only_openshift_simulation_fixture: test fixture
    """
    gathered_resource: Dict = only_openshift_simulation_fixture.resource_cache()

    # make sure the Route resource count is correct
    assert gathered_resource[ResourceTypeValues.OPENSHIFT_ROUTES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_ROUTE_COUNT

    for name in TestVals.RESOURCE_ROUTE_LIST:
        # make sure the expected Route is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resource[ResourceTypeValues.OPENSHIFT_ROUTES][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.NO_INGRESS_SIMULATION_FIXTURE)
def test_gather_details_route_no_ingress(no_ingress_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that no details are gathered about Ingress resources if no ingress kinds are found.

    :param no_ingress_simulation_fixture: test fixture
    """
    assert ResourceTypeValues.OPENSHIFT_ROUTES not in no_ingress_simulation_fixture.resource_cache()


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_services(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about Service resources are in the gathered details.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the Service resource count is correct
    assert gathered_resources[ResourceTypeValues.K8S_CORE_SERVICES][ReportKeys.ResourceTypeDetails.COUNT] == \
           TestVals.RESOURCE_SERVICE_COUNT

    for name in TestVals.RESOURCE_SERVICE_LIST:
        # make sure the expected Service is available by name
        # relationships to pods and networking objects have not yet been made
        assert name in gathered_resources[ResourceTypeValues.K8S_CORE_SERVICES][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_gather_details_stateful_sets(only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about StatefulSet resources are in the gathered details.

    :param only_nginx_simulation_fixture: test fixture
    """
    gathered_resources: Dict = only_nginx_simulation_fixture.resource_cache()

    # make sure the StatefulSet resource count is correct
    assert gathered_resources[ResourceTypeValues.K8S_APPS_STATEFUL_SETS][ReportKeys.ResourceTypeDetails.COUNT] == \
           TestVals.RESOURCE_STATEFUL_SET_COUNT

    # make sure the expected StatefulSet is available by name
    assert TestVals.COMPONENT_SAS_CACHE_SERVER_STATEFUL_SET_NAME in \
        gathered_resources[ResourceTypeValues.K8S_APPS_STATEFUL_SETS][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_ISTIO_USED_SIMULATION_FIXTURE)
def test_gather_details_virtual_services_all_istio_used(
        all_available_istio_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about VirtualService resources are in the gathered details.

    :param all_available_istio_used_simulation_fixture: test fixture
    """
    gathered_resource: Dict = all_available_istio_used_simulation_fixture.resource_cache()

    # make sure the VirtualService resource count is correct
    assert gathered_resource[ResourceTypeValues.ISTIO_VIRTUAL_SERVICES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_VIRTUAL_SERVICE_COUNT

    for name in TestVals.RESOURCE_VIRTUAL_SERVICE_LIST:
        # make sure the expected VirtualService is available by name
        # relationships to Service objects have not yet been made
        assert name in \
               gathered_resource[ResourceTypeValues.ISTIO_VIRTUAL_SERVICES][
                   ITEMS_KEY]


@pytest.mark.usefixtures(conftest.ONLY_ISTIO_SIMULATION_FIXTURE)
def test_gather_details_virtual_services_only_istio(
        only_istio_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that expected details about VirtualService resources are in the gathered details.

    :param only_istio_simulation_fixture: test fixture
    """
    gathered_resource: Dict = only_istio_simulation_fixture.resource_cache()

    # make sure the VirtualService resource count is correct
    assert gathered_resource[ResourceTypeValues.ISTIO_VIRTUAL_SERVICES][
               ReportKeys.ResourceTypeDetails.COUNT] == TestVals.RESOURCE_VIRTUAL_SERVICE_COUNT

    for name in TestVals.RESOURCE_VIRTUAL_SERVICE_LIST:
        # make sure the expected VirtualService is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resource[ResourceTypeValues.ISTIO_VIRTUAL_SERVICES][ITEMS_KEY]


@pytest.mark.usefixtures(conftest.NO_INGRESS_SIMULATION_FIXTURE)
def test_gather_details_virtual_service_no_ingress(
        no_ingress_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that no details are gathered about VirtualService resources if no ingress kinds are found.

    :param no_ingress_simulation_fixture: test fixture
    """
    assert ResourceTypeValues.ISTIO_VIRTUAL_SERVICES not in no_ingress_simulation_fixture.resource_cache()
