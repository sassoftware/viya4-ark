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

from typing import Dict, Optional, Text

from deployment_report.model.utils import ingress_util

from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource


####################################################################
# Unit Tests                                                     ###
####################################################################
@pytest.mark.usefixtures("gathered_resources_no_ingress")
def test_determine_ingress_controller_no_ingress(gathered_resources_no_ingress: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when no ingress kinds are available.

    :param gathered_resources_no_ingress: test fixture
    """
    controller: Optional[Text] = ingress_util.determine_ingress_controller(gathered_resources_no_ingress)

    assert controller is None


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_contour_used")
def test_determine_ingress_controller_all_ingress_defined_contour_used(
        gathered_resources_all_ingress_defined_contour_used: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when all ingress kinds are available in the
    cluster but Contour is controlling ingress.

    :param gathered_resources_all_ingress_defined_contour_used: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(gathered_resources_all_ingress_defined_contour_used)

    assert controller == SupportedIngress.Controllers.CONTOUR


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_istio_used")
def test_determine_ingress_controller_all_ingress_defined_istio_used(
        gathered_resources_all_ingress_defined_istio_used: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when all ingress kinds are available in the
    cluster but Istio is controlling ingress.

    :param gathered_resources_all_ingress_defined_istio_used: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(gathered_resources_all_ingress_defined_istio_used)

    assert controller == SupportedIngress.Controllers.ISTIO


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_nginx_used")
def test_determine_ingress_controller_all_ingress_defined_nginx_used(
        gathered_resources_all_ingress_defined_nginx_used: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when all ingress kinds are available in the
    cluster but NGINX is controlling ingress.

    :param gathered_resources_all_ingress_defined_nginx_used: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(gathered_resources_all_ingress_defined_nginx_used)

    assert controller == SupportedIngress.Controllers.NGINX


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_openshift_used")
def test_determine_ingress_controller_all_ingress_defined_openshift_used(
        gathered_resources_all_ingress_defined_openshift_used: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when all ingress kinds are available in the
    cluster but OpenShift is controlling ingress.

    :param gathered_resources_all_ingress_defined_openshift_used: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(gathered_resources_all_ingress_defined_openshift_used)

    assert controller == SupportedIngress.Controllers.OPENSHIFT


@pytest.mark.usefixtures("gathered_resources_only_contour")
def test_determine_ingress_controller_only_contour(gathered_resources_only_contour: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when only Contour ingress kinds are
    available.

    :param gathered_resources_only_contour: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(gathered_resources_only_contour)

    assert controller == SupportedIngress.Controllers.CONTOUR


@pytest.mark.usefixtures("gathered_resources_only_istio")
def test_determine_ingress_controller_only_istio(gathered_resources_only_istio: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when only Istio ingress kinds are
    available.

    :param gathered_resources_only_istio: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(gathered_resources_only_istio)

    assert controller == SupportedIngress.Controllers.ISTIO


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_determine_ingress_controller_only_nginx(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when only NGINX ingress kinds are
    available.

    :param gathered_resources_only_nginx: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(gathered_resources_only_nginx)

    assert controller == SupportedIngress.Controllers.NGINX


@pytest.mark.usefixtures("gathered_resources_only_openshift")
def test_determine_ingress_controller_only_openshift(gathered_resources_only_openshift: Dict) -> None:
    """
    This test verifies that the ingress controller is correctly determined when only OpenShift ingress kinds are
    available.

    :param gathered_resources_only_openshift: test fixture
    """
    controller: Optional[Text] = \
        ingress_util.determine_ingress_controller(gathered_resources_only_openshift)

    assert controller == SupportedIngress.Controllers.OPENSHIFT


def test_ignorable_for_controller_if_unavailable_contour() -> None:
    """
    This test verifies that the correct value is returned if the kind can be ignored when ingress is controlled by
    Contour.
    """
    # ignorable
    # Ingress
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.CONTOUR,
                                                                KubernetesResource.Kinds.INGRESS)
    # Route
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.CONTOUR,
                                                                KubernetesResource.Kinds.OPENSHIFT_ROUTE)
    # VirtualService
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.CONTOUR,
                                                                KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE)

    # not ignorable
    # Pod
    assert not ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.CONTOUR,
                                                                    KubernetesResource.Kinds.POD)
    # HTTPProxy
    assert not ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.CONTOUR,
                                                                    KubernetesResource.Kinds.CONTOUR_HTTPPROXY)


def test_ignorable_for_controller_if_unavailable_istio() -> None:
    """
    This test verifies that the correct value is returned if the kind can be ignored when ingress is controlled by
    Istio.
    """
    # ignorable
    # HTTPProxy
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.ISTIO,
                                                                KubernetesResource.Kinds.CONTOUR_HTTPPROXY)
    # Ingress
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.ISTIO,
                                                                KubernetesResource.Kinds.INGRESS)
    # Route
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.ISTIO,
                                                                KubernetesResource.Kinds.OPENSHIFT_ROUTE)

    # not ignorable
    # Pod
    assert not ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.ISTIO,
                                                                    KubernetesResource.Kinds.POD)
    # VirtualService
    assert not ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.ISTIO,
                                                                    KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE)


def test_ignorable_for_controller_if_unavailable_nginx() -> None:
    """
    This test verifies that the correct value is returned if the kind can be ignored when ingress is controlled by
    NGINX.
    """
    # ignorable
    # HTTPProxy
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.NGINX,
                                                                KubernetesResource.Kinds.CONTOUR_HTTPPROXY)
    # Route
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.NGINX,
                                                                KubernetesResource.Kinds.OPENSHIFT_ROUTE)
    # VirtualService
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.NGINX,
                                                                KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE)

    # not ignorable
    # Pod
    assert not ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.NGINX,
                                                                    KubernetesResource.Kinds.POD)
    # Ingress
    assert not ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.NGINX,
                                                                    KubernetesResource.Kinds.INGRESS)


def test_ignorable_for_controller_if_unavailable_openshift() -> None:
    """
    This test verifies that the correct value is returned if the kind can be ignored when ingress is controlled by
    OpenShift.
    """
    # ignorable
    # HTTPProxy
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.OPENSHIFT,
                                                                KubernetesResource.Kinds.CONTOUR_HTTPPROXY)
    # Ingress
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.OPENSHIFT,
                                                                KubernetesResource.Kinds.INGRESS)
    # VirtualService
    assert ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.OPENSHIFT,
                                                                KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE)

    # not ignorable
    # Pod
    assert not ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.OPENSHIFT,
                                                                    KubernetesResource.Kinds.POD)
    # Route
    assert not ingress_util.ignorable_for_controller_if_unavailable(SupportedIngress.Controllers.OPENSHIFT,
                                                                    KubernetesResource.Kinds.OPENSHIFT_ROUTE)
