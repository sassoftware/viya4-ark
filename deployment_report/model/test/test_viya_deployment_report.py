####################################################################
# ### test_viya_deployment_report.py                             ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import json
import os
import pytest

from typing import Dict, List, Text, Type

from deployment_report.model.viya_deployment_report import ViyaDeploymentReport
from deployment_report.model.static.viya_deployment_report_keys import ITEMS_KEY
from deployment_report.model.static.viya_deployment_report_keys import ViyaDeploymentReportKeys as ReportKeys
from viya_ark_library.k8s.k8s_resource_keys import KubernetesResourceKeys

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues
from viya_ark_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError
from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest

# create an alias to the KubectlTest.Values() class
TestVals: Type[KubectlTest.Values] = KubectlTest.Values


####################################################################
# Unit Test Fixtures                                               #
####################################################################
@pytest.fixture(scope="module")
def report() -> ViyaDeploymentReport:
    """
    This fixture method runs the report to populate data. With the "module" scope, this will only run once for this
    test file, which saves time because a generic report can be used by multiple tests.

    :return: The completed ViyaDeploymentReport object.
    """
    report: ViyaDeploymentReport = ViyaDeploymentReport()
    report.gather_details(kubectl=KubectlTest())
    return report


####################################################################
# Unit Tests                                                       #
####################################################################
def test_gather_details_basic_user_invalid_namespace_from_command_line() -> None:
    """
    In the event that a user without the ability to see non-namespaced resources passes an invalid namespace on the
    command line, kubectl won't be able to verify that value as valid or invalid and will pass it along to the report.
    If this occurs, the gather_details() method should throw an error when listing pods is forbidden.
    """
    with pytest.raises(KubectlRequestForbiddenError) as exec_info:
        report: ViyaDeploymentReport = ViyaDeploymentReport()
        report.gather_details(kubectl=KubectlTest(include_non_namespaced_resources=False,
                                                  namespace="Foo"))

    assert ("Listing pods is forbidden in namespace [Foo]. Make sure KUBECONFIG is correctly set and that the correct "
            "namespace is being targeted. A namespace can be given on the command line using the \"--namespace=\" "
            "option.") in str(exec_info.value)


def test_gather_details_basic_user_valid_namespace_from_command_line() -> None:
    """
    In the event that a user without the ability to see non-namespaced resources passes a valid namespace on the
    command line, kubectl won't be able to verify that value as valid or invalid and will pass it along to the report.
    If this occurs, the gather_details() method should not throw an error when listing pods as the request should be
    allowed with a valid namespace.
    """
    try:
        report: ViyaDeploymentReport = ViyaDeploymentReport()
        report.gather_details(kubectl=KubectlTest(include_non_namespaced_resources=False,
                                                  namespace="test"))
    except KubectlRequestForbiddenError as e:
        pytest.fail(f"An unexpected error was raised: {e}")


def test_get_kubernetes_details(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the "kubernetes" dictionary in a report is populated with all of the expected keys.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get the kubernetes details
    kube_details: Dict = report.get_kubernetes_details()

    # check for all expected entries
    assert len(kube_details) == 11
    assert ReportKeys.Kubernetes.API_RESOURCES_DICT in kube_details
    assert ReportKeys.Kubernetes.API_VERSIONS_LIST in kube_details
    assert ReportKeys.Kubernetes.CADENCE_INFO in kube_details
    assert ReportKeys.Kubernetes.CONFIGMAPS_DICT in kube_details
    assert ReportKeys.Kubernetes.DB_INFO in kube_details
    assert ReportKeys.Kubernetes.DISCOVERED_RESOURCE_TYPES_DICT in kube_details
    assert ReportKeys.Kubernetes.INGRESS_CTRL in kube_details
    assert ReportKeys.Kubernetes.NAMESPACE in kube_details
    assert ReportKeys.Kubernetes.NODES_DICT in kube_details
    assert ReportKeys.Kubernetes.SECRETS_DICT in kube_details
    assert ReportKeys.Kubernetes.VERSIONS_DICT in kube_details


def test_get_kubernetes_details_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the "kubernetes" dictionary in a report when the report has
    not yet been populated.
    """
    assert ViyaDeploymentReport().get_kubernetes_details() is None


def test_get_api_resources() -> None:
    """
    This test verifies that all the expected api-resources values returned by the KubectlTest implementation are
    present in the "kubernetes.apiResources" dictionary in the completed report.
    """
    report: ViyaDeploymentReport = ViyaDeploymentReport()
    report.gather_details(kubectl=KubectlTest(ingress_simulator=KubectlTest.IngressSimulator.ALL_NGINX_USED))

    # get the API resources information
    api_resources: Dict = report.get_api_resources()

    # check for expected attributes
    assert len(api_resources) == 18

    assert ResourceTypeValues.CONTOUR_HTTP_PROXIES in api_resources
    assert ResourceTypeValues.ISTIO_VIRTUAL_SERVICES
    assert ResourceTypeValues.K8S_APPS_DEPLOYMENTS in api_resources
    assert ResourceTypeValues.K8S_APPS_REPLICA_SETS in api_resources
    assert ResourceTypeValues.K8S_APPS_STATEFUL_SETS in api_resources
    assert ResourceTypeValues.K8S_BATCH_CRON_JOBS in api_resources
    assert ResourceTypeValues.K8S_BATCH_JOBS in api_resources
    assert ResourceTypeValues.K8S_CORE_CONFIG_MAPS in api_resources
    assert ResourceTypeValues.K8S_CORE_NODES in api_resources
    assert ResourceTypeValues.K8S_CORE_PODS in api_resources
    assert ResourceTypeValues.K8S_CORE_SECRETS in api_resources
    assert ResourceTypeValues.K8S_CORE_SERVICES in api_resources
    assert ResourceTypeValues.K8S_EXTENSIONS_INGRESSES in api_resources
    assert ResourceTypeValues.K8S_METRICS_NODES in api_resources
    assert ResourceTypeValues.K8S_METRICS_PODS in api_resources
    assert ResourceTypeValues.K8S_NETWORKING_INGRESSES in api_resources
    assert ResourceTypeValues.OPENSHIFT_ROUTES in api_resources
    assert ResourceTypeValues.SAS_CAS_DEPLOYMENTS in api_resources


def test_get_api_resources_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the "kubernetes.apiResources" dictionary when the report is
    unpopulated.
    """
    assert ViyaDeploymentReport().get_api_resources() is None


def test_get_api_versions(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that all expected api-versions values from the KubectlTest implementation are present in the
    "kubernetes.apiVersions" list in the completed report.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get the static api-versions list
    test_data_file: Text = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        f"..{os.sep}..{os.sep}..{os.sep}viya_ark_library{os.sep}k8s{os.sep}test_impl"
                                        f"{os.sep}response_data{os.sep}api_versions.json")
    with open(test_data_file, "r") as test_data_file_pointer:
        expected_api_versions: List = json.load(test_data_file_pointer)

    # get API versions information
    api_versions: List = report.get_api_versions()

    # check for expected attributes
    assert len(api_versions) == len(expected_api_versions)
    for api_version in expected_api_versions:
        assert api_version in api_versions


def test_get_api_versions_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the "kubernetes.apiVersions" list in an unpopulated report.
    """
    assert ViyaDeploymentReport().get_api_versions() is None


def test_get_discovered_resources(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that all expected resources discovered while gathering components are present in the
    "kubernetes.discoveredResources" dictionary in a completed report. There is also a spot-check for the correct
    structure for a value inside the dictionary using the first resource (alphabetically).

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get discovered resources information
    discovered_resources: Dict = report.get_discovered_resources()

    # check for expected attributes
    assert len(discovered_resources) == 16
    assert ResourceTypeValues.CONTOUR_HTTP_PROXIES in discovered_resources
    assert ResourceTypeValues.ISTIO_VIRTUAL_SERVICES in discovered_resources
    assert ResourceTypeValues.K8S_APPS_DEPLOYMENTS in discovered_resources
    assert ResourceTypeValues.K8S_APPS_REPLICA_SETS in discovered_resources
    assert ResourceTypeValues.K8S_APPS_STATEFUL_SETS in discovered_resources
    assert ResourceTypeValues.K8S_BATCH_CRON_JOBS in discovered_resources
    assert ResourceTypeValues.K8S_BATCH_JOBS in discovered_resources
    assert ResourceTypeValues.K8S_CORE_CONFIG_MAPS in discovered_resources
    assert ResourceTypeValues.K8S_CORE_NODES in discovered_resources
    assert ResourceTypeValues.K8S_CORE_PODS in discovered_resources
    assert ResourceTypeValues.K8S_CORE_SECRETS in discovered_resources
    assert ResourceTypeValues.K8S_CORE_SERVICES in discovered_resources
    assert ResourceTypeValues.K8S_EXTENSIONS_INGRESSES in discovered_resources
    assert ResourceTypeValues.K8S_NETWORKING_INGRESSES in discovered_resources
    assert ResourceTypeValues.OPENSHIFT_ROUTES in discovered_resources
    assert ResourceTypeValues.SAS_CAS_DEPLOYMENTS in discovered_resources

    # get details of a discovered types
    details: Dict = discovered_resources[ResourceTypeValues.SAS_CAS_DEPLOYMENTS]

    # check for expected attributes in discovered types
    assert details[ReportKeys.ResourceTypeDetails.AVAILABLE] is True
    assert details[ReportKeys.ResourceTypeDetails.COUNT] == 1
    assert details[ReportKeys.ResourceTypeDetails.SAS_CRD] is True


def test_get_discovered_resources_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the "kubernetes.discoveredResources" dictionary in an
    unpopulated report.
    """
    # make sure None is returned
    assert ViyaDeploymentReport().get_discovered_resources() is None


def test_get_ingress_controller(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that NGINX is returned as the ingress controller when VirtualService objects are not available
    in the api-resources.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # check for expected attributes
    assert report.get_ingress_controller() == SupportedIngress.Controllers.NGINX


def test_get_ingress_controller_none() -> None:
    """
    This test verifies that a None value is returned when both Ingress and VirtualService resources are unavailable.
    """
    # run the report
    report: ViyaDeploymentReport = ViyaDeploymentReport()
    report.gather_details(kubectl=KubectlTest(KubectlTest.IngressSimulator.NONE))

    # check for expected attributes
    assert report.get_ingress_controller() is None


def test_get_ingress_controller_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the ingress controller when the report is unpopulated.
    """
    # make sure None is returned
    assert ViyaDeploymentReport().get_ingress_controller() is None


def test_get_namespace_provided(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the provided namespace is returned when a namespace values is passed to gather_details().

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # check for expected attributes
    assert report.get_namespace() == TestVals.NAMESPACE


def test_get_namespace_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the namespace when the report is unpopulated.
    """
    # create unpopulated report instance
    report: ViyaDeploymentReport = ViyaDeploymentReport()

    # make sure None is returned
    assert report.get_namespace() is None


def test_get_node_details(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that node details are correctly returned in a completed report.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get node information
    node_details: Dict = report.get_node_details()

    # check for expected attributes
    assert len(node_details) == 4
    assert node_details[ReportKeys.ResourceTypeDetails.AVAILABLE] is True
    assert node_details[ReportKeys.ResourceTypeDetails.COUNT] == 1
    assert node_details[ReportKeys.ResourceTypeDetails.KIND] == "Node"
    assert len(node_details[ITEMS_KEY]) == 1
    assert TestVals.RESOURCE_NODE_1_NAME in node_details[ITEMS_KEY]


def test_get_node_details_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the node details when the report is unpopulated.
    """
    # make sure None is returned
    assert ViyaDeploymentReport().get_node_details() is None


def test_get_kubernetes_version_details(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the kubernetes version information is returned correctly in a completed report.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get Kubernetes version information
    kube_ver_details: Dict = report.get_kubernetes_version_details()

    # check for expected attributes
    assert len(kube_ver_details) == 2
    assert "clientVersion" in kube_ver_details
    assert "serverVersion" in kube_ver_details


def test_get_kubernetes_version_details_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the kubernetes version information when the report is
    unpopulated.
    """
    # make sure None is returned
    assert ViyaDeploymentReport().get_kubernetes_version_details() is None


def test_get_other_components(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the non-SAS component is correctly collected in a completed report.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get other components information
    other_components: Dict = report.get_other_components()

    # check for expected attributes
    assert len(other_components) == 1
    assert TestVals.COMPONENT_PROMETHEUS_NAME in other_components
    assert ResourceTypeValues.K8S_APPS_DEPLOYMENTS in other_components[TestVals.COMPONENT_PROMETHEUS_NAME]
    assert ResourceTypeValues.K8S_CORE_PODS in other_components[TestVals.COMPONENT_PROMETHEUS_NAME]
    assert ResourceTypeValues.K8S_APPS_REPLICA_SETS in other_components[TestVals.COMPONENT_PROMETHEUS_NAME]
    assert ResourceTypeValues.K8S_CORE_SERVICES in other_components[TestVals.COMPONENT_PROMETHEUS_NAME]


def test_get_other_components_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the otherComponents dictionary when the report is unpopulated.
    """
    # make sure None is returned
    assert ViyaDeploymentReport().get_other_components() is None


def test_get_sas_components(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the correct number of SAS components are returned in a completed report.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get SAS components information
    sas_components: Dict = report.get_sas_components()

    # check for expected attributes
    assert len(sas_components) == 4


def test_get_sas_components_casdeployment_owned(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the component owned by a CASDeployment object is correctly collected in a completed report.
    Tests the collection of: (1) CASDeployment, (2) Deployment, (3) Pod, (4) ReplicaSet, (5) Service

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get SAS components information
    sas_components: Dict = report.get_sas_components()

    # check for expected attributes
    assert TestVals.COMPONENT_SAS_CAS_OPERATOR_NAME in sas_components
    assert ResourceTypeValues.SAS_CAS_DEPLOYMENTS in sas_components[TestVals.COMPONENT_SAS_CAS_OPERATOR_NAME]
    assert ResourceTypeValues.K8S_APPS_DEPLOYMENTS in sas_components[TestVals.COMPONENT_SAS_CAS_OPERATOR_NAME]
    assert ResourceTypeValues.K8S_CORE_PODS in sas_components[TestVals.COMPONENT_SAS_CAS_OPERATOR_NAME]
    assert ResourceTypeValues.K8S_APPS_REPLICA_SETS in sas_components[TestVals.COMPONENT_SAS_CAS_OPERATOR_NAME]
    assert ResourceTypeValues.K8S_CORE_SERVICES in sas_components[TestVals.COMPONENT_SAS_CAS_OPERATOR_NAME]


def test_get_sas_components_cronjob_owned(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the component owned by a CronJob object is correctly collected in a completed report.
    Tests the collection of: (1) CronJob, (2) Job, (3) Pod

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get SAS components information
    sas_components: Dict = report.get_sas_components()

    # check for expected attributes
    assert TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_NAME in sas_components
    assert ResourceTypeValues.K8S_BATCH_CRON_JOBS in \
        sas_components[TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_NAME]
    assert ResourceTypeValues.K8S_BATCH_JOBS in sas_components[TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_NAME]
    assert ResourceTypeValues.K8S_CORE_PODS in sas_components[TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_NAME]


def test_get_sas_components_deployment_owned(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the component owned by a Deployment object is correctly collected in a completed report.
    Tests the collection of: (1) Deployment, (2) Ingress, (3) Pod, (4) ReplicaSet, (5) Service

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get SAS components information
    sas_components: Dict = report.get_sas_components()

    # check for expected attributes
    assert TestVals.COMPONENT_SAS_ANNOTATIONS_NAME in sas_components
    assert ResourceTypeValues.K8S_APPS_DEPLOYMENTS in sas_components[TestVals.COMPONENT_SAS_ANNOTATIONS_NAME]
    assert ResourceTypeValues.K8S_EXTENSIONS_INGRESSES in sas_components[TestVals.COMPONENT_SAS_ANNOTATIONS_NAME]
    assert ResourceTypeValues.K8S_NETWORKING_INGRESSES in sas_components[TestVals.COMPONENT_SAS_ANNOTATIONS_NAME]
    assert ResourceTypeValues.K8S_CORE_PODS in sas_components[TestVals.COMPONENT_SAS_ANNOTATIONS_NAME]
    assert ResourceTypeValues.K8S_APPS_REPLICA_SETS in sas_components[TestVals.COMPONENT_SAS_ANNOTATIONS_NAME]
    assert ResourceTypeValues.K8S_CORE_SERVICES in sas_components[TestVals.COMPONENT_SAS_ANNOTATIONS_NAME]


def test_get_sas_components_statefulset_owned(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the component owned by a StatefulSet object is correctly collected in a completed report.
    Test the collection of: (1) Pod, (2) Service, (3) StatefulSet

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get SAS components information
    sas_components: Dict = report.get_sas_components()

    # check for expected attributes
    assert TestVals.COMPONENT_SAS_CACHE_SERVER_NAME in sas_components
    assert ResourceTypeValues.K8S_CORE_PODS in sas_components[TestVals.COMPONENT_SAS_CACHE_SERVER_NAME]
    assert ResourceTypeValues.K8S_CORE_SERVICES in \
        sas_components[TestVals.COMPONENT_SAS_CACHE_SERVER_NAME]
    assert ResourceTypeValues.K8S_APPS_STATEFUL_SETS in \
        sas_components[TestVals.COMPONENT_SAS_CACHE_SERVER_NAME]


def test_get_sas_components_unpopulated() -> None:
    """
    This test verifies that a None value is returned for the sasComponents dictionary when the report is unpopulated.
    """
    # make sure None is returned
    assert ViyaDeploymentReport().get_sas_components() is None


def test_get_sas_component(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that an existing SAS component is correctly returned from the gathered components.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get SAS component information
    component: Dict = report.get_sas_component(TestVals.COMPONENT_SAS_ANNOTATIONS_NAME)

    # check for expected attributes
    assert len(component) == 6
    assert ResourceTypeValues.K8S_APPS_DEPLOYMENTS in component
    assert ResourceTypeValues.K8S_EXTENSIONS_INGRESSES in component
    assert ResourceTypeValues.K8S_NETWORKING_INGRESSES in component
    assert ResourceTypeValues.K8S_CORE_PODS in component
    assert ResourceTypeValues.K8S_APPS_REPLICA_SETS in component
    assert ResourceTypeValues.K8S_CORE_SERVICES in component


def test_get_sas_component_bad_param(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that a None value is returned when a request is made for an undefined SAS component in a
    completed report.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # make sure None is returned
    assert report.get_sas_component("sas-foo") is None


def test_get_sas_component_unpopulated() -> None:
    """
    This test verifies that a None value is returned for a requested SAS component when the report is unpopulated.
    """
    # make sure None is returned
    assert ViyaDeploymentReport().get_sas_component(TestVals.COMPONENT_SAS_ANNOTATIONS_NAME) is None


def test_get_sas_component_resources(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that the resources from the given SAS Component is correctly returned from a completed report.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # get component resource details
    component_resource_details: Dict = report.get_sas_component_resources(
        TestVals.COMPONENT_SAS_ANNOTATIONS_NAME, ResourceTypeValues.K8S_APPS_DEPLOYMENTS)

    # check for expected attributes
    assert len(component_resource_details) == 1
    assert TestVals.COMPONENT_SAS_ANNOTATIONS_NAME in component_resource_details
    assert component_resource_details[TestVals.COMPONENT_SAS_ANNOTATIONS_NAME][
               ReportKeys.ResourceDetails.RESOURCE_DEFINITION][KubernetesResourceKeys.KIND] == "Deployment"


def test_get_sas_component_resources_bad_params(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that a None value is returned when a request is made for a SAS component that isn't defined
    or for a resource that is not defined for an existing component.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # make sure None is returned
    assert report.get_sas_component_resources("sas-foo", ResourceTypeValues.K8S_APPS_DEPLOYMENTS) is None
    assert report.get_sas_component_resources(TestVals.COMPONENT_SAS_ANNOTATIONS_NAME, "Foo") is None


def test_get_sas_component_resources_unpopulated() -> None:
    """
    This test verifies that a None value is returned for a requested component resource when the report is unpopulated.
    """
    # make sure None is returned
    assert ViyaDeploymentReport().get_sas_component_resources(TestVals.COMPONENT_SAS_ANNOTATIONS_NAME,
                                                              ResourceTypeValues.K8S_APPS_DEPLOYMENTS) is None


def test_write_report(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that a completed report is correctly written to disk as both an HTML report and a JSON data file.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # write the report and data file
    data_file, html_file = report.write_report()

    # check for expected files
    assert os.path.exists(data_file)
    assert os.path.isfile(data_file)
    assert os.path.exists(html_file)
    assert os.path.exists(html_file)

    # clean up files
    os.remove(data_file)
    os.remove(html_file)


def test_write_report_data_only(report: ViyaDeploymentReport) -> None:
    """
    This test verifies that only the JSON data file is written to disk when requested from a completed report.

    :param report: The populated ViyaDeploymentReport returned by the report() fixture.
    """
    # write data file only
    data_file, html_file = report.write_report(data_file_only=True)

    # make sure HTML report is None
    assert html_file is None

    # check for expected file
    assert os.path.exists(data_file)
    assert os.path.isfile(data_file)

    # clean up file
    os.remove(data_file)


def test_write_report_unpopulated() -> None:
    """
    This test verifies that a None value is returned for each file when the report is unpopulated.
    """
    # create unpopulated report instance
    report = ViyaDeploymentReport()

    # write report
    data_file, html_file = report.write_report()

    # make sure None is returned
    assert data_file is None
    assert html_file is None
