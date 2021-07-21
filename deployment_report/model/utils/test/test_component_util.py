####################################################################
# ### test_component_util.py                                     ###
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

from typing import Dict

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    NAME_KEY
from deployment_report.model.utils import \
    component_util, \
    relationship_util

from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest

# create aliases to KubectlTest classes
TestVals: KubectlTest.Values = KubectlTest.Values()


####################################################################
# Unit Tests                                                     ###
####################################################################
@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_aggregate_resources_prometheus(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that all resources which comprise the prometheus component are correctly aggregated to create
    the component definition.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # define pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the prometheus pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][TestVals.COMPONENT_PROMETHEUS_POD_NAME]

    # aggregate the resources in the prometheus component
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_PROMETHEUS_NAME

    # make sure the correct number of resources were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_PROMETHEUS_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_PROMETHEUS_RESOURCES_DICT.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_no_ingress")
def test_aggregate_resources_sas_annotations_no_ingress(gathered_resources_no_ingress: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when no ingress is found.

    :param gathered_resources_no_ingress: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_no_ingress)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    for controller in SupportedIngress.get_ingress_controller_to_kind_map().keys():
        relationship_util.define_service_to_ingress_relationships(
            ingress_controller=controller,
            gathered_resources=gathered_resources_copy
        )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NO_INGRESS

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NO_INGRESS.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_contour_used")
def test_aggregate_resources_sas_annotations_all_ingress_defined_contour_used(
        gathered_resources_all_ingress_defined_contour_used: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when all ingress kinds are present but Contour is providing ingress control.

    :param gathered_resources_all_ingress_defined_contour_used: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_all_ingress_defined_contour_used)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    for controller in SupportedIngress.get_ingress_controller_to_kind_map().keys():
        relationship_util.define_service_to_ingress_relationships(
            ingress_controller=controller,
            gathered_resources=gathered_resources_copy
        )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_CONTOUR

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_CONTOUR.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_istio_used")
def test_aggregate_resources_sas_annotations_all_istio_used(gathered_resources_all_ingress_defined_istio_used: Dict) \
        -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when all ingress kinds are defined but Istio is providing ingress control.

    :param gathered_resources_all_ingress_defined_istio_used: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_all_ingress_defined_istio_used)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    for controller in SupportedIngress.get_ingress_controller_to_kind_map().keys():
        relationship_util.define_service_to_ingress_relationships(
            ingress_controller=controller,
            gathered_resources=gathered_resources_copy
        )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_ISTIO

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_ISTIO.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_nginx_used")
def test_aggregate_resources_sas_annotations_all_nginx_used(gathered_resources_all_ingress_defined_nginx_used: Dict) \
        -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when all ingress kinds are defined but NGINX is providing ingress control.

    :param gathered_resources_all_ingress_defined_nginx_used: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_all_ingress_defined_nginx_used)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    for controller in SupportedIngress.get_ingress_controller_to_kind_map().keys():
        relationship_util.define_service_to_ingress_relationships(
            ingress_controller=controller,
            gathered_resources=gathered_resources_copy
        )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NGINX

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NGINX.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_all_ingress_defined_openshift_used")
def test_aggregate_resources_sas_annotations_all_openshift_used(
        gathered_resources_all_ingress_defined_openshift_used: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when all ingress kinds are defined but OpenShift is providing ingress control.

    :param gathered_resources_all_ingress_defined_openshift_used: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_all_ingress_defined_openshift_used)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    for controller in SupportedIngress.get_ingress_controller_to_kind_map().keys():
        relationship_util.define_service_to_ingress_relationships(
            ingress_controller=controller,
            gathered_resources=gathered_resources_copy
        )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_OPENSHIFT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_OPENSHIFT.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_only_contour")
def test_aggregate_resources_sas_annotations_only_contour(gathered_resources_only_contour: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when only Contour kinds are found.

    :param gathered_resources_only_contour: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_contour)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    for controller in SupportedIngress.get_ingress_controller_to_kind_map().keys():
        relationship_util.define_service_to_ingress_relationships(
            ingress_controller=controller,
            gathered_resources=gathered_resources_copy
        )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_CONTOUR

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_CONTOUR.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_only_istio")
def test_aggregate_resources_sas_annotations_only_istio(gathered_resources_only_istio: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when only Istio kinds are found.

    :param gathered_resources_only_istio: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_istio)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    for controller in SupportedIngress.get_ingress_controller_to_kind_map().keys():
        relationship_util.define_service_to_ingress_relationships(
            ingress_controller=controller,
            gathered_resources=gathered_resources_copy
        )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_ISTIO

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_ISTIO.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_aggregate_resources_sas_annotations_only_nginx(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when only NGINX kinds are found.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    for controller in SupportedIngress.get_ingress_controller_to_kind_map().keys():
        relationship_util.define_service_to_ingress_relationships(
            ingress_controller=controller,
            gathered_resources=gathered_resources_copy
        )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_NGINX

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_NGINX.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_only_openshift")
def test_aggregate_resources_sas_annotations_only_openshift(gathered_resources_only_openshift: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-annotations component are correctly aggregated to
    create the component definition when only OpenShift kinds are found.

    :param gathered_resources_only_openshift: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_openshift)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # define the service to ingress relationships to allow for aggregation
    for controller in SupportedIngress.get_ingress_controller_to_kind_map().keys():
        relationship_util.define_service_to_ingress_relationships(
            ingress_controller=controller,
            gathered_resources=gathered_resources_copy
        )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-annotations pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_ANNOTATIONS_POD_NAME]

    # aggregate the sas-annotations resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_ANNOTATIONS_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_COUNT_OPENSHIFT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_ANNOTATIONS_RESOURCE_DICT_OPENSHIFT.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_aggregate_resources_sas_cache_server(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-cacheserver component are correctly aggregated to
    create the component definition.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-cacheserver pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CACHE_SERVER_POD_NAME]

    # aggregate the resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_CACHE_SERVER_NAME

    # make sure the right number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_CACHE_SERVER_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_CACHE_SERVER_RESOURCE_DICT.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_aggregate_resources_sas_cas_operator(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-cas-operator component are correctly aggregated to
    create the component definition.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-cas-operator pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_OPERATOR_POD_NAME]

    # aggregate the resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_CAS_OPERATOR_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_CAS_OPERATOR_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_CAS_OPERATOR_RESOURCE_DICT.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_aggregate_resources_sas_cas_server(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-cas-server component are correctly aggregated to
    create the component definition.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # define the pod to service relationships to allow for aggregation
    relationship_util.define_pod_to_service_relationships(
        pods=gathered_resources_copy[KubernetesResource.Kinds.POD],
        services=gathered_resources_copy[KubernetesResource.Kinds.SERVICE]
    )

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-cas-server pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_CAS_SERVER_POD_NAME]

    # aggregate the resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_CAS_SERVER_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_CAS_SERVER_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_CAS_SERVER_RESOURCE_DICT.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]


@pytest.mark.usefixtures("gathered_resources_only_nginx")
def test_aggregate_resources_sas_scheduled_backup_job(gathered_resources_only_nginx: Dict) -> None:
    """
    This test verifies that all resources which comprise the sas-scheduled-backup-job component are correctly aggregated
    to create the component definition.

    :param gathered_resources_only_nginx: test fixture
    """
    # copy the gathered_resources dict so it won't be altered for other tests
    gathered_resources_copy: Dict = copy.deepcopy(gathered_resources_only_nginx)

    # create a dictionary to hold the component
    component: Dict = dict()

    # get the sas-scheduled-backup-job pod
    pod: Dict = gathered_resources_copy[KubernetesResource.Kinds.POD][ITEMS_KEY][
        TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_POD_NAME]

    # aggregate the resources
    component_util.aggregate_resources(
        resource_details=pod,
        gathered_resources=gathered_resources_copy,
        component=component
    )

    # make sure the component name is correct
    assert component[NAME_KEY] == TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_NAME

    # make sure the correct number of resource types were aggregated
    assert len(component[ITEMS_KEY]) == TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_RESOURCE_COUNT

    # make sure the all resources are accounted for
    for kind, name_list in TestVals.COMPONENT_SAS_SCHEDULED_BACKUP_JOB_RESOURCE_DICT.items():
        assert kind in component[ITEMS_KEY]
        assert len(component[ITEMS_KEY][kind]) == len(name_list)
        for name in name_list:
            assert name in component[ITEMS_KEY][kind]
