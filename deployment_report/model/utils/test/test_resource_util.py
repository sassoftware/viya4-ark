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

from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest

# alias to KubectlTest.Values to shorten name
TestVals: KubectlTest.Values = KubectlTest.Values()


####################################################################
# Unit Tests                                                     ###
####################################################################
@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_nginx_used")
def test_gather_details_all_resources(gathered_resources_all_ingress_defined_nginx_used: Dict) -> None:
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param gathered_resources_all_ingress_defined_nginx_used: test fixture
    """
    # make sure the correct number of resources categories are defined
    assert len(gathered_resources_all_ingress_defined_nginx_used) == TestVals.RESOURCE_LIST_ALL_COUNT

    for kind in TestVals.RESOURCE_LIST_ALL:
        assert kind in gathered_resources_all_ingress_defined_nginx_used
        assert gathered_resources_all_ingress_defined_nginx_used[kind][ReportKeys.KindDetails.AVAILABLE] is True


@pytest.mark.usefixtures("gathered_resources_only_contour")
def test_gather_details_only_contour(gathered_resources_only_contour: Dict) -> None:
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param gathered_resources_only_contour: test fixture
    """
    # make sure the correct number of resources categories are defined
    assert len(gathered_resources_only_contour) == TestVals.RESOURCE_LIST_CONTOUR_COUNT

    for kind in TestVals.RESOURCE_LIST_CONTOUR:
        assert kind in gathered_resources_only_contour
        assert gathered_resources_only_contour[kind][ReportKeys.KindDetails.AVAILABLE] is True


@pytest.mark.usefixtures("gathered_resources_only_istio")
def test_gather_details_only_istio(gathered_resources_only_istio: Dict) -> None:
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param gathered_resources_only_istio: test fixture
    """
    # make sure the correct number of resources categories are defined
    assert len(gathered_resources_only_istio) == TestVals.RESOURCE_LIST_ISTIO_COUNT

    for kind in TestVals.RESOURCE_LIST_ISTIO:
        assert kind in gathered_resources_only_istio
        assert gathered_resources_only_istio[kind][ReportKeys.KindDetails.AVAILABLE] is True


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_only_nginx(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the correct number of resources categories are defined
    assert len(gathered_resources_only_nginx) == TestVals.RESOURCE_LIST_NGINX_COUNT

    for kind in TestVals.RESOURCE_LIST_NGINX:
        assert kind in gathered_resources_only_nginx
        assert gathered_resources_only_nginx[kind][ReportKeys.KindDetails.AVAILABLE] is True


@pytest.mark.usefixtures("gathered_resources_only_openshift")
def test_gather_details_only_openshift(gathered_resources_only_openshift) -> None:
    """
    This test verifies that all resources gathered during the execution of the gathered_resources fixture are present.
    The gathered_resources fixture includes Pods, which are the smallest unit, so Pods as well as all owning object,
    nodes, and networking resources should be gathered.

    :param gathered_resources_only_openshift: test fixture
    """
    # make sure the correct number of resources categories are defined
    assert len(gathered_resources_only_openshift) == TestVals.RESOURCE_LIST_OPENSHIFT_COUNT

    for kind in TestVals.RESOURCE_LIST_OPENSHIFT:
        assert kind in gathered_resources_only_openshift
        assert gathered_resources_only_openshift[kind][ReportKeys.KindDetails.AVAILABLE] is True


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_cas_deployments(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that expected details about CASDeployment resources are in the gathered details.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the CASDeployment count is correct
    assert gathered_resources_only_nginx[KubernetesResource.Kinds.CAS_DEPLOYMENT][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_CAS_DEPLOYMENT_COUNT

    for name in TestVals.RESOURCE_CAS_DEPLOYMENT_LIST:
        # make sure the expected CASDeployment is available by name
        assert name in gathered_resources_only_nginx[KubernetesResource.Kinds.CAS_DEPLOYMENT][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_cron_jobs(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that expected details about CronJob resources are in the gathered details.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the CronJob count is correct
    assert gathered_resources_only_nginx[KubernetesResource.Kinds.CRON_JOB][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_CRON_JOB_COUNT

    for name in TestVals.RESOURCE_CRON_JOB_LIST:
        # make sure the expected CronJob is available by name
        assert name in gathered_resources_only_nginx[KubernetesResource.Kinds.CRON_JOB][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_deployments(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that expected details about Deployment resources are in the gathered details.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the Deployment resource count is correct
    assert gathered_resources_only_nginx[KubernetesResource.Kinds.DEPLOYMENT][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_DEPLOYMENT_COUNT

    for name in TestVals.RESOURCE_DEPLOYMENT_LIST:
        # make sure the expected Deployment is available by name
        assert name in gathered_resources_only_nginx[KubernetesResource.Kinds.DEPLOYMENT][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_contour_used")
def test_gather_details_httpproxy_all_contour_used(gathered_resources_all_ingress_defined_contour_used: Dict) -> None:
    """
    This test verifies that expected details about HTTPProxy resources are in the gathered details.

    :param gathered_resources_all_ingress_defined_contour_used: test fixture
    """
    # make sure the HTTPProxy resource count is correct
    assert gathered_resources_all_ingress_defined_contour_used[KubernetesResource.Kinds.CONTOUR_HTTPPROXY][
               ReportKeys.KindDetails.COUNT] == TestVals.RESOURCE_HTTPPROXY_COUNT

    for name in TestVals.RESOURCE_HTTPPROXY_LIST:
        # make sure the expected HTTPProxy is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resources_all_ingress_defined_contour_used[KubernetesResource.Kinds.CONTOUR_HTTPPROXY][
            ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_only_contour")
def test_gather_details_httpproxy_only_contour(gathered_resources_only_contour: Dict) -> None:
    """
    This test verifies that expected details about HTTPProxy resources are in the gathered details.

    :param gathered_resources_only_contour: test fixture
    """
    # make sure the HTTPProxy resource count is correct
    assert gathered_resources_only_contour[KubernetesResource.Kinds.CONTOUR_HTTPPROXY][
               ReportKeys.KindDetails.COUNT] == TestVals.RESOURCE_HTTPPROXY_COUNT

    for name in TestVals.RESOURCE_HTTPPROXY_LIST:
        # make sure the expected HTTPProxy is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resources_only_contour[KubernetesResource.Kinds.CONTOUR_HTTPPROXY][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_no_ingress")
def test_gather_details_httpproxy_no_ingress(gathered_resources_no_ingress: Dict) -> None:
    """
    This test verifies that no details are gathered about HTTPProxy resources if no ingress kinds are found.

    :param gathered_resources_no_ingress: test fixture
    """
    assert KubernetesResource.Kinds.CONTOUR_HTTPPROXY not in gathered_resources_no_ingress


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_nginx_used")
def test_gather_details_ingresses_all_nginx_used(gathered_resources_all_ingress_defined_nginx_used: Dict) \
        -> None:
    """
    This test verifies that expected details about Ingress resources are in the gathered details.

    :param gathered_resources_all_ingress_defined_nginx_used: test fixture.
    """
    # make sure the Ingress resource count is correct
    assert gathered_resources_all_ingress_defined_nginx_used[KubernetesResource.Kinds.INGRESS][
               ReportKeys.KindDetails.COUNT] == TestVals.RESOURCE_INGRESS_COUNT

    for name in TestVals.RESOURCE_INGRESS_LIST:
        # make sure the expected Deployment is available by name
        # relationships have not yet been defined between Ingress and Service objects
        assert name in gathered_resources_all_ingress_defined_nginx_used[KubernetesResource.Kinds.INGRESS][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_ingresses_only_nginx(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that expected details about Ingress resources are in the gathered details.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the Ingress resource count is correct
    assert gathered_resources_only_nginx[KubernetesResource.Kinds.INGRESS][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_INGRESS_COUNT

    for name in TestVals.RESOURCE_INGRESS_LIST:
        # make sure the expected Deployment is available by name
        # relationships have not yet been defined between Ingress and Service objects
        assert name in gathered_resources_only_nginx[KubernetesResource.Kinds.INGRESS][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_no_ingress")
def test_gather_details_ingresses_no_ingress(gathered_resources_no_ingress: Dict) -> None:
    """
    This test verifies that no details are gathered about Ingress resources if no ingress kinds are found.

    :param gathered_resources_no_ingress: test fixture
    """
    assert KubernetesResource.Kinds.INGRESS not in gathered_resources_no_ingress


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_jobs(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that expected details about Job resources are in the gathered details.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the Job resource count is correct
    assert gathered_resources_only_nginx[KubernetesResource.Kinds.JOB][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_JOB_COUNT

    for name in TestVals.RESOURCE_JOB_LIST:
        # make sure the expected Job is available by name
        assert name in gathered_resources_only_nginx[KubernetesResource.Kinds.JOB][ITEMS_KEY]

        # the Job object is owned by the CronJob object, make sure it has an ext.relationships definition with 1
        # relationship
        assert len(gathered_resources_only_nginx[KubernetesResource.Kinds.JOB][ITEMS_KEY][name][
            ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_pods(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that expected details about Pod resources are in the gathered details.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the Pod resource count is correct
    assert gathered_resources_only_nginx[KubernetesResource.Kinds.POD][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_POD_COUNT

    for name in TestVals.RESOURCE_POD_LIST:
        # make sure the expected Pod is available by name
        assert name in gathered_resources_only_nginx[KubernetesResource.Kinds.POD][ITEMS_KEY]

        # the Pod object is owned by controller objects, make sure it has an ext.relationships definition with 1
        # relationship
        assert len(gathered_resources_only_nginx[KubernetesResource.Kinds.POD][ITEMS_KEY][name][
                       ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_replica_sets(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that expected details about ReplicaSet resources are in the gathered details.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the ReplicaSet resource count is correct
    assert gathered_resources_only_nginx[KubernetesResource.Kinds.REPLICA_SET][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_REPLICA_SET_COUNT

    for name in TestVals.RESOURCE_REPLICA_SET_LIST:
        # make sure the expected ReplicaSet is available by name
        assert name in gathered_resources_only_nginx[KubernetesResource.Kinds.REPLICA_SET][ITEMS_KEY]

        # the ReplicaSet object is owned Deployment objects, make sure it has an ext.relationships definition with 1
        # relationship
        assert len(gathered_resources_only_nginx[KubernetesResource.Kinds.REPLICA_SET][ITEMS_KEY][name][
                       ReportKeys.ResourceDetails.EXT_DICT][ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]) == 1


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_openshift_used")
def test_gather_details_route_all_openshift_used(gathered_resources_all_ingress_defined_openshift_used: Dict) -> None:
    """
    This test verifies that expected details about Route resources are in the gathered details.

    :param gathered_resources_all_ingress_defined_openshift_used: test fixture
    """
    # make sure the Route resource count is correct
    assert gathered_resources_all_ingress_defined_openshift_used[KubernetesResource.Kinds.OPENSHIFT_ROUTE][
               ReportKeys.KindDetails.COUNT] == TestVals.RESOURCE_ROUTE_COUNT

    for name in TestVals.RESOURCE_ROUTE_LIST:
        # make sure the expected Route is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resources_all_ingress_defined_openshift_used[KubernetesResource.Kinds.OPENSHIFT_ROUTE][
            ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_only_openshift")
def test_gather_details_route_only_openshift(gathered_resources_only_openshift: Dict) -> None:
    """
    This test verifies that expected details about Route resources are in the gathered details.

    :param gathered_resources_only_openshift: test fixture
    """
    # make sure the Route resource count is correct
    assert gathered_resources_only_openshift[KubernetesResource.Kinds.OPENSHIFT_ROUTE][
               ReportKeys.KindDetails.COUNT] == TestVals.RESOURCE_ROUTE_COUNT

    for name in TestVals.RESOURCE_ROUTE_LIST:
        # make sure the expected Route is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resources_only_openshift[KubernetesResource.Kinds.OPENSHIFT_ROUTE][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_no_ingress")
def test_gather_details_route_no_ingress(gathered_resources_no_ingress: Dict) -> None:
    """
    This test verifies that no details are gathered about Ingress resources if no ingress kinds are found.

    :param gathered_resources_no_ingress: test fixture
    """
    assert KubernetesResource.Kinds.OPENSHIFT_ROUTE not in gathered_resources_no_ingress


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_services(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that expected details about Service resources are in the gathered details.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the Service resource count is correct
    assert gathered_resources_only_nginx[KubernetesResource.Kinds.SERVICE][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_SERVICE_COUNT

    for name in TestVals.RESOURCE_SERVICE_LIST:
        # make sure the expected Service is available by name
        # relationships to pods and networking objects have not yet been made
        assert name in gathered_resources_only_nginx[KubernetesResource.Kinds.SERVICE][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_gather_details_stateful_sets(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that expected details about StatefulSet resources are in the gathered details.

    :param gathered_resources_only_nginx: test fixture
    """
    # make sure the StatefulSet resource count is correct
    assert gathered_resources_only_nginx[KubernetesResource.Kinds.STATEFUL_SET][ReportKeys.KindDetails.COUNT] == \
        TestVals.RESOURCE_STATEFUL_SET_COUNT

    # make sure the expected StatefulSet is available by name
    assert TestVals.COMPONENT_SAS_CACHE_SERVER_STATEFUL_SET_NAME in \
        gathered_resources_only_nginx[KubernetesResource.Kinds.STATEFUL_SET][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_istio_used")
def test_gather_details_virtual_services_all_istio_used(gathered_resources_all_ingress_defined_istio_used: Dict) \
        -> None:
    """
    This test verifies that expected details about VirtualService resources are in the gathered details.

    :param gathered_resources_all_ingress_defined_istio_used: test fixture
    """
    # make sure the VirtualService resource count is correct
    assert gathered_resources_all_ingress_defined_istio_used[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE][
               ReportKeys.KindDetails.COUNT] == TestVals.RESOURCE_VIRTUAL_SERVICE_COUNT

    for name in TestVals.RESOURCE_VIRTUAL_SERVICE_LIST:
        # make sure the expected VirtualService is available by name
        # relationships to Service objects have not yet been made
        assert name in \
               gathered_resources_all_ingress_defined_istio_used[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE][
                   ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_only_istio")
def test_gather_details_virtual_services_only_istio(gathered_resources_only_istio: Dict) -> None:
    """
    This test verifies that expected details about VirtualService resources are in the gathered details.

    :param gathered_resources_only_istio: test fixture
    """
    # make sure the VirtualService resource count is correct
    assert gathered_resources_only_istio[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE][
               ReportKeys.KindDetails.COUNT] == TestVals.RESOURCE_VIRTUAL_SERVICE_COUNT

    for name in TestVals.RESOURCE_VIRTUAL_SERVICE_LIST:
        # make sure the expected VirtualService is available by name
        # relationships to Service objects have not yet been made
        assert name in gathered_resources_only_istio[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE][ITEMS_KEY]


@pytest.mark.usefixtures("gathered_resources_no_ingress")
def test_gather_details_virtual_service_no_ingress(gathered_resources_no_ingress: Dict) -> None:
    """
    This test verifies that no details are gathered about VirtualService resources if no ingress kinds are found.

    :param gathered_resources_no_ingress: test fixture
    """
    assert KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE not in gathered_resources_no_ingress
