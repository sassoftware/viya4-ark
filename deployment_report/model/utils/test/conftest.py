####################################################################
# ### conftest.py                                                ###
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

from deployment_report.model.utils import resource_util

from viya_ark_library.k8s.sas_k8s_objects import KubernetesApiResources
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest


####################################################################
# Unit Test Fixtures                                             ###
####################################################################
@pytest.fixture(scope="module")
def gathered_resources_no_ingress() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all gathered resources including all supported ingress kinds, with Contour being
             the ingress controller used.
    """
    return _gathered_resources(KubectlTest.IngressSimulator.NONE)


@pytest.fixture(scope="module")
def gathered_resources_all_ingress_defined_contour_used() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all gathered resources including all supported ingress kinds, with Contour being
             the ingress controller used.
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ALL_CONTOUR_USED)


@pytest.fixture(scope="module")
def gathered_resources_all_ingress_defined_istio_used() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all gathered resources including all supported ingress kinds, with Istio being
             the ingress controller used.
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ALL_ISTIO_USED)


@pytest.fixture(scope="module")
def gathered_resources_all_ingress_defined_nginx_used() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all gathered resources including all supported ingress kinds, with NGINX being
             the ingress controller used.
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ALL_NGINX_USED)


@pytest.fixture(scope="module")
def gathered_resources_all_ingress_defined_openshift_used() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all gathered resources including all supported ingress kinds, with OpenShift being
             the ingress controller used.
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ALL_OPENSHIFT_USED)


@pytest.fixture(scope="module")
def gathered_resources_only_contour() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all gathered resources with only Contour ingress kinds defined.
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ONLY_CONTOUR)


@pytest.fixture(scope="module")
def gathered_resources_only_istio() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all gathered resources with only Istio ingress kinds defined.
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ONLY_ISTIO)


@pytest.fixture(scope="module")
def gathered_resources_only_nginx() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all gathered resources with only NGINX ingress kinds defined.
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ONLY_NGINX)


@pytest.fixture(scope="module")
def gathered_resources_only_openshift() -> Dict:
    """
    This fixture creates a KubectlTest object, collects the available api-resources and calls
    ViyaDeploymentReport.gather_resource_details() to gather all resources to create complete components.
    Relationships not defined by gather_resource_details() are not defined in the resulting dictionary to
    allow for testing of the methods that define them.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: A dictionary of all gathered resources with only OpenShift ingress kinds defined.
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ONLY_OPENSHIFT)


def _gathered_resources(ingress_simulator: KubectlTest.IngressSimulator) -> Dict:
    """
    Internal helper method for creating a gathered_resources dict based on
    a provided ingress simulation.

    :param ingress_simulator: The ingress simulation to use.
    """
    # set up kubectl and get API resources
    kubectl: KubectlTest = KubectlTest(ingress_simulator=ingress_simulator)
    api_resources: KubernetesApiResources = kubectl.api_resources()

    # set up dict to hold gathered resources
    gathered_resources: Dict = dict()

    for resource_kind in api_resources.as_dict().keys():
        resource_util.gather_details(
            kubectl=kubectl,
            gathered_resources=gathered_resources,
            api_resources=api_resources,
            resource_kind=resource_kind)

    return gathered_resources
