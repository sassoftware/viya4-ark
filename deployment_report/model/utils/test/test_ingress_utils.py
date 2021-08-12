####################################################################
# ### test_ingress_utils.py                                      ###
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

from typing import Optional, Text

from deployment_report.model.utils import ingress_util
from deployment_report.model.utils.test import conftest
from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues

from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress


####################################################################
# Unit Tests                                                     ###
####################################################################
@pytest.mark.usefixtures(conftest.NO_INGRESS_SIMULATION_FIXTURE)
def test_determine_ingress_controller_no_ingress(
        no_ingress_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the ingress controller is correctly determined when no ingress kinds are available.

    :param no_ingress_simulation_fixture: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(no_ingress_simulation_fixture.resource_cache())

    assert controller is None


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_CONTOUR_USED_SIMULATION_FIXTURE)
def test_determine_ingress_controller_all_available_contour_used(
        all_available_contour_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the ingress controller is correctly determined when all ingress kinds are available in the
    cluster but Contour is controlling ingress.

    :param all_available_contour_used_simulation_fixture: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(all_available_contour_used_simulation_fixture.resource_cache())

    assert controller == SupportedIngress.Controllers.CONTOUR


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_ISTIO_USED_SIMULATION_FIXTURE)
def test_determine_ingress_controller_all_available_istio_used(
        all_available_istio_used_simulation_fixture: conftest.DeploymentSimulationArtifacts) -> None:
    """
    This test verifies that the ingress controller is correctly determined when all ingress kinds are available in the
    cluster but Istio is controlling ingress.

    :param all_available_istio_used_simulation_fixture: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(all_available_istio_used_simulation_fixture.resource_cache())

    assert controller == SupportedIngress.Controllers.ISTIO


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_NGINX_USED_SIMULATION_FIXTURE)
def test_determine_ingress_controller_all_available_nginx_used(
        all_available_nginx_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the ingress controller is correctly determined when all ingress kinds are available in the
    cluster but NGINX is controlling ingress.

    :param all_available_nginx_used_simulation_fixture: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(all_available_nginx_used_simulation_fixture.resource_cache())

    assert controller == SupportedIngress.Controllers.NGINX


@pytest.mark.usefixtures(conftest.ALL_AVAILABLE_OPENSHIFT_USED_SIMULATION_FIXTURE)
def test_determine_ingress_controller_all_available_openshift_used(
        all_available_openshift_used_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the ingress controller is correctly determined when all ingress kinds are available in the
    cluster but OpenShift is controlling ingress.

    :param all_available_openshift_used_simulation_fixture: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(all_available_openshift_used_simulation_fixture.resource_cache())

    assert controller == SupportedIngress.Controllers.OPENSHIFT


@pytest.mark.usefixtures(conftest.ONLY_CONTOUR_SIMULATION_FIXTURE)
def test_determine_ingress_controller_only_contour(
        only_contour_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the ingress controller is correctly determined when only Contour ingress kinds are
    available.

    :param only_contour_simulation_fixture: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(only_contour_simulation_fixture.resource_cache())

    assert controller == SupportedIngress.Controllers.CONTOUR


@pytest.mark.usefixtures(conftest.ONLY_ISTIO_SIMULATION_FIXTURE)
def test_determine_ingress_controller_only_istio(
        only_istio_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the ingress controller is correctly determined when only Istio ingress kinds are
    available.

    :param only_istio_simulation_fixture: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(only_istio_simulation_fixture.resource_cache())

    assert controller == SupportedIngress.Controllers.ISTIO


@pytest.mark.usefixtures(conftest.ONLY_NGINX_SIMULATION_FIXTURE)
def test_determine_ingress_controller_only_nginx(
        only_nginx_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the ingress controller is correctly determined when only NGINX ingress kinds are
    available.

    :param only_nginx_simulation_fixture: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(only_nginx_simulation_fixture.resource_cache())

    assert controller == SupportedIngress.Controllers.NGINX


@pytest.mark.usefixtures(conftest.ONLY_OPENSHIFT_SIMULATION_FIXTURE)
def test_determine_ingress_controller_only_openshift(
        only_openshift_simulation_fixture: conftest.DeploymentSimulationArtifacts):
    """
    This test verifies that the ingress controller is correctly determined when only OpenShift ingress kinds are
    available.

    :param only_openshift_simulation_fixture: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(only_openshift_simulation_fixture.resource_cache())

    assert controller == SupportedIngress.Controllers.OPENSHIFT


def test_ignorable_for_controller_if_unavailable_contour():
    """
    This test verifies that the correct value is returned if the kind can be ignored when ingress is controlled by
    Contour.
    """
    # ignorable
    # Ingress
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.CONTOUR,
        resource_type=ResourceTypeValues.K8S_EXTENSIONS_INGRESSES)
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.CONTOUR,
        resource_type=ResourceTypeValues.K8S_NETWORKING_INGRESSES)
    # Route
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.CONTOUR,
        resource_type=ResourceTypeValues.OPENSHIFT_ROUTES)
    # VirtualService
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.CONTOUR,
        resource_type=ResourceTypeValues.ISTIO_VIRTUAL_SERVICES)

    # not ignorable
    # Pod
    assert not ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.CONTOUR,
        resource_type=ResourceTypeValues.K8S_CORE_PODS)
    # HTTPProxy
    assert not ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.CONTOUR,
        resource_type=ResourceTypeValues.CONTOUR_HTTP_PROXIES)


def test_ignorable_for_controller_if_unavailable_istio():
    """
    This test verifies that the correct value is returned if the kind can be ignored when ingress is controlled by
    Istio.
    """
    # ignorable
    # HTTPProxy
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.ISTIO,
        resource_type=ResourceTypeValues.CONTOUR_HTTP_PROXIES)
    # Ingress
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.ISTIO,
        resource_type=ResourceTypeValues.K8S_EXTENSIONS_INGRESSES)
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.ISTIO,
        resource_type=ResourceTypeValues.K8S_NETWORKING_INGRESSES)
    # Route
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.ISTIO,
        resource_type=ResourceTypeValues.OPENSHIFT_ROUTES)

    # not ignorable
    # Pod
    assert not ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.ISTIO,
        resource_type=ResourceTypeValues.K8S_CORE_PODS)
    # VirtualService
    assert not ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.ISTIO,
        resource_type=ResourceTypeValues.ISTIO_VIRTUAL_SERVICES)


def test_ignorable_for_controller_if_unavailable_nginx():
    """
    This test verifies that the correct value is returned if the kind can be ignored when ingress is controlled by
    NGINX.
    """
    # ignorable
    # HTTPProxy
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.NGINX,
        resource_type=ResourceTypeValues.CONTOUR_HTTP_PROXIES)
    # Route
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.NGINX,
        resource_type=ResourceTypeValues.OPENSHIFT_ROUTES)
    # VirtualService
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.NGINX,
        resource_type=ResourceTypeValues.ISTIO_VIRTUAL_SERVICES)

    # not ignorable
    # Pod
    assert not ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.NGINX,
        resource_type=ResourceTypeValues.K8S_CORE_PODS)
    # Ingress
    assert not ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.NGINX,
        resource_type=ResourceTypeValues.K8S_EXTENSIONS_INGRESSES)
    assert not ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.NGINX,
        resource_type=ResourceTypeValues.K8S_NETWORKING_INGRESSES)


def test_ignorable_for_controller_if_unavailable_openshift():
    """
    This test verifies that the correct value is returned if the kind can be ignored when ingress is controlled by
    OpenShift.
    """
    # ignorable
    # HTTPProxy
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.OPENSHIFT,
        resource_type=ResourceTypeValues.CONTOUR_HTTP_PROXIES)
    # Ingress
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.OPENSHIFT,
        resource_type=ResourceTypeValues.K8S_EXTENSIONS_INGRESSES)
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.OPENSHIFT,
        resource_type=ResourceTypeValues.K8S_NETWORKING_INGRESSES)
    # VirtualService
    assert ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.OPENSHIFT,
        resource_type=ResourceTypeValues.ISTIO_VIRTUAL_SERVICES)

    # not ignorable
    # Pod
    assert not ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.OPENSHIFT,
        resource_type=ResourceTypeValues.K8S_CORE_PODS)
    # Route
    assert not ingress_util.ignorable_for_controller_if_unavailable(
        ingress_controller=SupportedIngress.Controllers.OPENSHIFT,
        resource_type=ResourceTypeValues.OPENSHIFT_ROUTES)
