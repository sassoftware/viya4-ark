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

from typing import Dict, Type

from deployment_report.model.utils import resource_util, relationship_util

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues
from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesAvailableResourceTypes
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest

####################################################################
# Unit Test Fixture Names                                        ###
####################################################################
ALL_AVAILABLE_CONTOUR_USED_SIMULATION_FIXTURE = "all_available_contour_used_simulation_fixture"
ALL_AVAILABLE_ISTIO_USED_SIMULATION_FIXTURE = "all_available_istio_used_simulation_fixture"
ALL_AVAILABLE_NGINX_USED_SIMULATION_FIXTURE = "all_available_nginx_used_simulation_fixture"
ALL_AVAILABLE_OPENSHIFT_USED_SIMULATION_FIXTURE = "all_available_openshift_used_simulation_fixture"
NO_INGRESS_SIMULATION_FIXTURE = "no_ingress_simulation_fixture"
ONLY_CONTOUR_SIMULATION_FIXTURE = "only_contour_simulation_fixture"
ONLY_ISTIO_SIMULATION_FIXTURE = "only_istio_simulation_fixture"
ONLY_NGINX_SIMULATION_FIXTURE = "only_nginx_simulation_fixture"
ONLY_OPENSHIFT_SIMULATION_FIXTURE = "only_openshift_simulation_fixture"


####################################################################
# Class: DeploymentSimulationArtifacts                           ###
####################################################################
class DeploymentSimulationArtifacts(object):
    """
    Simple class defining all the artifacts required for testing Viya deployment report utilities against simulated
    deployments with a mocked ingress controller.
    """
    def __init__(self, resource_cache: Dict, available_resources: KubernetesAvailableResourceTypes):
        """
        IngressSimulationArtifacts constructor.

        :param resource_cache: The dictionary of cached resources gathered from the simulated deployment.
        :param available_resources: The resource types available in the simulated deployment.
        """
        self._resource_cache: Dict = resource_cache
        self._available_resources: KubernetesAvailableResourceTypes = available_resources

    def api_resource_types(self) -> KubernetesAvailableResourceTypes:
        """
        :return: a KubernetesApiResourceTypes object with all available resources defined for the simulated deployment
        """
        return self._available_resources

    def resource_cache(self) -> Dict:
        """
        :return: a dictionary of cached resources gathered from the simulated deployment.
        """
        return self._resource_cache


####################################################################
# Alias: DSA -> DeploymentSimulationArtifacts                    ###
####################################################################
DSA: Type[DeploymentSimulationArtifacts] = DeploymentSimulationArtifacts


####################################################################
# Unit Test Fixtures                                             ###
####################################################################
@pytest.fixture(name=ALL_AVAILABLE_CONTOUR_USED_SIMULATION_FIXTURE, scope="module")
def all_available_contour_used_simulation_fixture() -> DeploymentSimulationArtifacts:
    """
    This fixture creates a DeploymentSimulationArtifacts object with artifacts simulating a deployment with all ingress
    resource types available but only Contour HTTPProxy resource objects defined. All relationships between resources
    are defined in the provided gathered_resources dictionary.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: a DeploymentSimulationArtifacts object
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ALL_CONTOUR_USED)


@pytest.fixture(name=ALL_AVAILABLE_ISTIO_USED_SIMULATION_FIXTURE, scope="module")
def all_available_istio_used_simulation_fixture() -> DeploymentSimulationArtifacts:
    """
    This fixture creates a DeploymentSimulationArtifacts object with artifacts simulating a deployment with all ingress
    resource types available but only Istio VirtualService resource objects defined. All relationships between resources
    are defined in the provided gathered_resources dictionary.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: a DeploymentSimulationArtifacts object
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ALL_ISTIO_USED)


@pytest.fixture(name=ALL_AVAILABLE_NGINX_USED_SIMULATION_FIXTURE, scope="module")
def all_available_nginx_used_simulation_fixture() -> DeploymentSimulationArtifacts:
    """
    This fixture creates a DeploymentSimulationArtifacts object with artifacts simulating a deployment with all ingress
    resource types available but only NGINX Ingress resource objects defined. All relationships between resources
    are defined in the provided gathered_resources dictionary.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: a DeploymentSimulationArtifacts object
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ALL_NGINX_USED)


@pytest.fixture(name=ALL_AVAILABLE_OPENSHIFT_USED_SIMULATION_FIXTURE, scope="module")
def all_available_openshift_used_simulation_fixture() -> DeploymentSimulationArtifacts:
    """
    This fixture creates a DeploymentSimulationArtifacts object with artifacts simulating a deployment with all ingress
    resource types available but only OpenShift Route resource objects defined. All relationships between resources
    are defined in the provided gathered_resources dictionary.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: a DeploymentSimulationArtifacts object
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ALL_OPENSHIFT_USED)


@pytest.fixture(name=NO_INGRESS_SIMULATION_FIXTURE, scope="module")
def no_ingress_simulation_fixture() -> DeploymentSimulationArtifacts:
    """
    This fixture creates a DeploymentSimulationArtifacts object with artifacts simulating a deployment with no
    determinable ingress controller. All relationships between resources are defined in the provided gathered_resources
    dictionary.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: a DeploymentSimulationArtifacts object
    """
    return _gathered_resources(KubectlTest.IngressSimulator.NONE)


@pytest.fixture(name=ONLY_CONTOUR_SIMULATION_FIXTURE, scope="module")
def only_contour_simulation_fixture() -> DeploymentSimulationArtifacts:
    """
    This fixture creates a DeploymentSimulationArtifacts object with artifacts simulating a deployment with only the
    Contour HTTPProxy resource type available and only HTTPProxy objects defined. All relationships between resources
    are defined in the provided gathered_resources dictionary.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: a DeploymentSimulationArtifacts object
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ONLY_CONTOUR)


@pytest.fixture(name=ONLY_ISTIO_SIMULATION_FIXTURE, scope="module")
def only_istio_simulation_fixture() -> DeploymentSimulationArtifacts:
    """
    This fixture creates a DeploymentSimulationArtifacts object with artifacts simulating a deployment with only the
    Istio VirtualService resource type available and only VirtualService objects defined. All relationships between
    resources are defined in the provided gathered_resources dictionary.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: a DeploymentSimulationArtifacts object
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ONLY_ISTIO)


@pytest.fixture(name=ONLY_NGINX_SIMULATION_FIXTURE, scope="module")
def only_nginx_simulation_fixture() -> DeploymentSimulationArtifacts:
    """
    This fixture creates a DeploymentSimulationArtifacts object with artifacts simulating a deployment with only the
    NGINX Ingress resource type available and only Ingress objects defined. All relationships between resources
    are defined in the provided gathered_resources dictionary.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: a DeploymentSimulationArtifacts object
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ONLY_NGINX)


@pytest.fixture(name=ONLY_OPENSHIFT_SIMULATION_FIXTURE, scope="module")
def only_openshift_simulation_fixture() -> DeploymentSimulationArtifacts:
    """
    This fixture creates a DeploymentSimulationArtifacts object with artifacts simulating a deployment with only the
    OpenShift Route resource type available and only Route objects defined. All relationships between resources
    are defined in the provided gathered_resources dictionary.

    This method is run once before tests in this file are executed. All tests use the same instance.

    :return: a DeploymentSimulationArtifacts object
    """
    return _gathered_resources(KubectlTest.IngressSimulator.ONLY_OPENSHIFT)


def _gathered_resources(ingress_simulator: KubectlTest.IngressSimulator) -> DeploymentSimulationArtifacts:
    """
    Internal helper method for creating the objects needed to simulate resources gathered from a deployment with
    a given simulated ingress controller.

    :param ingress_simulator: The ingress simulation to use.
    :return: a DeploymentSimulationArtifacts object
    """
    # set up kubectl and get the available api resource types
    kubectl: KubectlTest = KubectlTest(ingress_simulator=ingress_simulator)
    api_resource_types: KubernetesAvailableResourceTypes = kubectl.api_resources()

    # set up dict to hold the resource cache
    resource_cache: Dict = dict()

    # iterate over all available types and gather any existing resources of that type
    for resource_type in api_resource_types.as_dict().keys():
        # ignore any types defined under the "metrics.k8s.io" group, these are retrieved via "top" calls
        # and don't need to be gathered
        if KubernetesResourceTypeValues.K8S_GROUP_METRICS_K8S_IO not in resource_type:
            resource_util.cache_resources(resource_type=resource_type,
                                          kubectl=kubectl,
                                          resource_cache=resource_cache)

    # define the node to pod relationships
    relationship_util.define_node_to_pod_relationships(resource_cache=resource_cache)

    # define the pod to service relationships
    relationship_util.define_pod_to_service_relationships(resource_cache=resource_cache)

    # define the service to ingress controller resource relationships
    for controller in SupportedIngress.get_ingress_controller_to_resource_types_map().keys():
        relationship_util.define_service_to_ingress_relationships(resource_cache=resource_cache,
                                                                  ingress_controller=controller)

    # return a DeploymentSimulationArtifacts object loaded with artifacts for the given deployment ingress simulation
    return DeploymentSimulationArtifacts(resource_cache=resource_cache, available_resources=api_resource_types)
