####################################################################
# ### test_sas_k8s_objects.py                                    ###
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
import json
import os
import pytest
from typing import Dict, List, Text, Union
from viya_ark_library.k8s.sas_k8s_objects import KubernetesApiResources, KubernetesMetrics, KubernetesResource

# test data file names
_API_RESOURCES_TEST_DATA_ = "api_resources.json"
_METRICS_TEST_DATA_ = "metrics.json"
_NON_SAS_RESOURCE_TEST_DATA_ = "non_sas_resource.json"
_SAS_RESOURCE_TEST_DATA_ = "sas_resource.json"


####################################################################
# Unit Test Utility Methods                                        #
####################################################################
def load_test_data(filename) -> Union[Dict, List]:
    """
    Unit test utility method used to load JSON test data from a file and return it as a Python-native object.

    :param filename: The name of the JSON data file to load from the data directory.
    :return: A Python-native dictionary or list loaded from the JSON data.
    """
    # get the current directory of this script to create absolute path
    current_dir: Text = os.path.dirname(os.path.abspath(__file__))
    # join the path to this file with the remaining path to the requested test data
    test_data_file: Text = os.path.join(current_dir, f"data{os.sep}{filename}")
    # open the test file and return the contents as a Python-native dictionary
    with open(test_data_file, "r") as test_data_file_pointer:
        return json.load(test_data_file_pointer)


####################################################################
# Unit Test Fixtures                                               #
####################################################################
@pytest.fixture(scope="module")
def kubernetes_api_resources_obj() -> KubernetesApiResources:
    """
    This pytest fixture loads a KubernetesApiResources object representing the API resources as they might be returned
    from kubectl. With the "module" scope, this is only run once before the tests defined in this file are executed.

    :return: A KubernetesApiResources object loaded with Kubernetes API resource definitions for testing.
    """
    api_resources_dict: Dict = load_test_data(_API_RESOURCES_TEST_DATA_)
    return KubernetesApiResources(api_resources_dict)


@pytest.fixture(scope="module")
def kubernetes_metrics_obj() -> KubernetesMetrics:
    """
    This pytest fixture loads a KubernetesMetrics object representing the Metrics data as it might be returned from
    kubectl. With the "module" scope, this is only run once before the tests defined in this file are executed.

    :return: A KubernetesMetrics object loaded with Kubernetes metrics data for testing.
    """
    metrics_dict: Dict = load_test_data(_METRICS_TEST_DATA_)
    return KubernetesMetrics(metrics_dict)


@pytest.fixture(scope="module")
def non_sas_kubernetes_resource_obj() -> KubernetesResource:
    """
    This pytest fixture loads a KubernetesResource object representing a non-SAS resource as it might be returned from
    kubectl. With the "module" scope, this is only run once before the tests defined in this file are executed.

    :return: A KubernetesResource object loaded with a non-SAS resource for testing.
    """
    non_sas_resource_dict: Dict = load_test_data(_NON_SAS_RESOURCE_TEST_DATA_)
    return KubernetesResource(non_sas_resource_dict)


@pytest.fixture(scope="module")
def sas_kubernetes_resource_obj() -> KubernetesResource:
    """
    This pytest fixture loads a KubernetesResource object representing a SAS resource as it might be returned from
    kubectl. With the "module" scope, this is only run once before the tests defined in this file are executed.

    :return: A KubernetesResource object loaded with a SAS resource for testing.
    """
    sas_resource_dict: Dict = load_test_data(_SAS_RESOURCE_TEST_DATA_)
    return KubernetesResource(sas_resource_dict)


####################################################################
# KubernetesApiResources Unit Tests                                #
####################################################################
def test_kubernetes_api_resources_is_available_true(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.is_available() correctly reports a defined resource as available.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.is_available("APIService") is True


def test_kubernetes_api_resources_is_available_false(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.is_available() correctly reports an undefined resource as not
    available.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.is_available("FooKind") is False


def test_kubernetes_api_resources_is_available_incomplete() -> None:
    """
    This test verifies that KubernetesApiResources.is_available() correctly reports a resource as not available when
    no resources are defined.
    """
    assert KubernetesApiResources(dict()).is_available("APIService") is False


def test_kubernetes_api_resources_get_api_group(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.get_api_group() returns the correct API group for a defined
    resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.get_api_group("APIService") == "apiregistration.k8s.io"


def test_kubernetes_api_resources_get_api_group_missing(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.get_api_group() returns None for an undefined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.get_api_group("FooKind") is None


def test_kubernetes_api_resources_get_api_group_incomplete() -> None:
    """
    This test verifies that KubernetesApiResources.get_api_group() returns None when no resources are defined.
    """
    assert KubernetesApiResources(dict()).get_api_group("APIService") is None


def test_kubernetes_api_resources_get_name(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that Kubernetes.get_name() returns the correct value for a defined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.get_name("APIService") == "apiservices"


def test_kubernetes_api_resources_get_name_missing(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that Kubernetes.get_name() returns None for an undefined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.get_name("FooKind") is None


def test_kubernetes_api_resources_get_name_incomplete() -> None:
    """
    This test verifies that Kubernetes.get_name() returns None when no resources are defined.
    """
    assert KubernetesApiResources(dict()).get_name("APIService") is None


def test_kubernetes_api_resources_is_namespaced(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.is_namespaced() returns the correct value for a defined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.is_namespaced("APIService") is True


def test_kubernetes_api_resources_is_namespaced_missing(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.is_namespaced() returns None for an undefined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.get_api_group("FooKind") is None


def test_kubernetes_api_resources_is_namespaced_incomplete() -> None:
    """
    This test verifies that KubernetesApiResources.is_namespaced() returns None when no resources are defined.
    """
    assert KubernetesApiResources(dict()).is_namespaced("APIService") is None


def test_kubernetes_api_resources_get_short_name(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.get_short_name() returns the correct value for a defined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.get_short_name("APIService") == ""


def test_kubernetes_api_resources_get_short_name_missing(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.get_short_name() returns None for an undefined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.get_short_name("FooKind") is None


def test_kubernetes_api_resources_get_short_name_incomplete() -> None:
    """
    This test verifies that KubernetesApiResources.get_short_name() returns None when no resources are defined.
    """
    assert KubernetesApiResources(dict()).get_short_name("APIService") is None


def test_kubernetes_api_resources_get_verbs(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.get_verbs() returns the correct value for a defined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.get_verbs("APIService") == [
            "create",
            "delete",
            "deletecollection",
            "get",
            "list",
            "patch",
            "update",
            "watch"
        ]


def test_kubernetes_api_resources_get_verbs_missing(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.get_verbs() returns None when for an undefined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.get_verbs("FooKind") is None


def test_kubernetes_api_resources_get_verbs_incomplete() -> None:
    """
    This test verifies that KubernetesApiResources.get_verbs() returns None when no resources are defined.
    """
    assert KubernetesApiResources(dict()).get_verbs("APIService") is None


def test_kubernetes_api_resources_kind_as_dict(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.kind_as_dict() returns the correct dictionary for a defined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    # get a single kind as a dict
    details: Dict = kubernetes_api_resources_obj.kind_as_dict("APIService")

    # verify that a dict was returned, it's the correct length, and has the expected keys
    assert isinstance(details, dict)
    assert len(details) == 5
    assert KubernetesApiResources.Keys.API_GROUP in details
    assert KubernetesApiResources.Keys.NAME in details
    assert KubernetesApiResources.Keys.NAMESPACED in details
    assert KubernetesApiResources.Keys.SHORT_NAME in details
    assert KubernetesApiResources.Keys.VERBS in details


def test_kubernetes_api_resources_kind_as_dict_missing(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.kind_as_dict() returns None for an undefined resource.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    assert kubernetes_api_resources_obj.kind_as_dict("FooKind") is None


def test_kubernetes_api_resources_kind_as_dict_incomplete() -> None:
    """
    This test verifies that KubernetesApiResources.kind_as_dict() returns None when no resources are defined.
    """
    assert KubernetesApiResources(dict()).kind_as_dict("APIService") is None


def test_kubernetes_api_resources_as_dict(kubernetes_api_resources_obj: KubernetesApiResources) -> None:
    """
    This test verifies that KubernetesApiResources.as_dict() returns the correct dictionary.

    :param kubernetes_api_resources_obj: The pre-loaded KubernetesApiResources fixture object for testing.
    """
    # convert the object to a dict
    converted_api_resources: Dict = kubernetes_api_resources_obj.as_dict()

    # make sure a dict was returned, it's the correct length, and has the expected keys
    assert isinstance(converted_api_resources, dict)
    assert len(converted_api_resources) == 1
    assert "APIService" in converted_api_resources


####################################################################
# KubernetesMetrics Tests                                          #
####################################################################
def test_kubernetes_metrics_get_cpu_cores(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.get_cpu_cores() returns the correct value for defined metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    assert kubernetes_metrics_obj.get_cpu_cores("node") == "398m"
    assert kubernetes_metrics_obj.get_cpu_cores("pod") == "13m"


def test_kubernetes_metrics_get_cpu_cores_missing(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.get_cpu_cores() returns None for undefined metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    assert kubernetes_metrics_obj.get_cpu_cores("foo") is None


def test_kubernetes_metrics_get_cpu_cores_incomplete() -> None:
    """
    This test verifies that KubernetesMetrics.get_cpu_cores() returns None when no metrics are defined.
    """
    assert KubernetesMetrics(dict()).get_cpu_cores("node") is None


def test_kubernetes_metrics_get_cpu_used(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.get_cpu_used() returns the correct value for defined metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    assert kubernetes_metrics_obj.get_cpu_used("node") == "3%"
    assert kubernetes_metrics_obj.get_cpu_used("pod") is None


def test_kubernetes_metrics_get_cpu_used_missing(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.get_cpu_used() returns None for undefined metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    assert kubernetes_metrics_obj.get_cpu_used("foo") is None


def test_kubernetes_metrics_get_cpu_used_incomplete() -> None:
    """
    This test verifies that KubernetesMetrics.get_cpu_used() returns None when no metrics are defined.
    """
    assert KubernetesMetrics(dict()).get_cpu_used("node") is None


def test_kubernetes_metrics_get_memory_bytes(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.get_memory_bytes() returns the correct value for defined metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    assert kubernetes_metrics_obj.get_memory_bytes("node") == "2255Mi"
    assert kubernetes_metrics_obj.get_memory_bytes("pod") == "50Mi"


def test_kubernetes_metrics_get_memory_bytes_missing(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.get_memory_bytes() returns None for undefined metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    assert kubernetes_metrics_obj.get_memory_bytes("foo") is None


def test_kubernetes_metrics_get_memory_bytes_incomplete() -> None:
    """
    This test verifies that KubernetesMetrics.get_memory_bytes() returns None when no metrics are defined.
    """
    assert KubernetesMetrics(dict()).get_memory_bytes("node") is None


def test_kubernetes_metrics_get_memory_used(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.get_memory_used() returns the correct value for defined metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    assert kubernetes_metrics_obj.get_memory_used("node") == "14%"
    assert kubernetes_metrics_obj.get_memory_used("pod") is None


def test_kubernetes_metrics_get_memory_used_missing(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.get_memory_used() returns None for undefined metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    assert kubernetes_metrics_obj.get_memory_used("foo") is None


def test_kubernetes_metrics_get_memory_used_incomplete() -> None:
    """
    This test verifies that KubernetesMetrics.get_memory_used() returns None when no metrics are defined.
    """
    assert KubernetesMetrics(dict()).get_memory_used("node") is None


def test_kubernetes_metrics_resource_metrics_as_dict(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.resource_metrics_as_dict() returns the correct dictionary for defined
    resource metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    # get a single metrics dict
    node_metrics: Dict = kubernetes_metrics_obj.resource_metrics_as_dict("node")

    # make sure it is the correct type, length, and has the expected keys
    assert isinstance(node_metrics, dict)
    assert len(node_metrics) == 4
    assert KubernetesMetrics.Keys.CPU_CORES in node_metrics
    assert KubernetesMetrics.Keys.CPU_USED in node_metrics
    assert KubernetesMetrics.Keys.MEMORY_BYTES in node_metrics
    assert KubernetesMetrics.Keys.MEMORY_USED in node_metrics


def test_kubernetes_metrics_resource_metrics_as_dict_missing(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.resource_metrics_as_dict() returns None for undefined resource metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    assert kubernetes_metrics_obj.resource_metrics_as_dict("foo") is None


def test_kubernetes_metrics_resource_metrics_as_dict_incomplete() -> None:
    """
    This test verifies that KubernetesMetrics.resource_metrics_as_dict() returns None when no metrics are defined.
    """
    assert KubernetesMetrics(dict()).resource_metrics_as_dict("node") is None


def test_kubernetes_metrics_as_dict(kubernetes_metrics_obj: KubernetesMetrics) -> None:
    """
    This test verifies that KubernetesMetrics.as_dict() returns the correct dictionary for the defined metrics.

    :param kubernetes_metrics_obj: The pre-loaded KubernetesMetrics fixture object for testing.
    """
    # convert the object to a dict
    converted_metrics: Dict = kubernetes_metrics_obj.as_dict()

    # make sure it's the correct type, length, and has the expected keys
    assert isinstance(converted_metrics, dict)
    assert len(converted_metrics) == 2
    assert "node" in converted_metrics
    assert "pod" in converted_metrics


####################################################################
# KubernetesResource Tests                                         #
####################################################################
def test_kubernetes_resource_get(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get() returns the correct dictionary for a defined key. This tests the
    overridden __get__() method for the MutableMapping implementation.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get(KubernetesResource.Keys.KIND) == KubernetesResource.Kinds.DEPLOYMENT
    assert sas_kubernetes_resource_obj[KubernetesResource.Keys.KIND] == KubernetesResource.Kinds.DEPLOYMENT


def test_kubernetes_resource_set(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.set() correct defines a new key/value pair in the resource. This tests
    the overridden __set__() method for the MutableMapping implementation.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    # copy the resource so the fixture version isn't modified for other test
    resource_copy: KubernetesResource = copy.deepcopy(sas_kubernetes_resource_obj)

    # set new values using direct assignment and the MutableMapping .setdefault() method
    resource_copy["testKey1"] = True
    resource_copy.setdefault("testKey2", "True")

    # make sure the keys are defined in the object with the correct value
    assert "testKey1" in resource_copy
    assert "testKey2" in resource_copy
    assert resource_copy["testKey1"] is True
    assert resource_copy["testKey2"] == "True"


def test_kubernetes_resource_del(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.pop and del remove the specified keys and that the correct values are
    returned, if applicable. This tests the overridden __del__() method in the MutableMapping implementation.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    # copy the resource so the fixture version isn't modified for other test
    resource: KubernetesResource = copy.deepcopy(sas_kubernetes_resource_obj)

    # directly delete a key and pop a second key
    del resource[KubernetesResource.Keys.API_VERSION]
    kind = resource.pop(KubernetesResource.Keys.KIND)

    # make sure the keys were removed and the expected value was popped
    assert KubernetesResource.Keys.API_VERSION not in resource
    assert KubernetesResource.Keys.KIND not in resource
    assert kind == KubernetesResource.Kinds.DEPLOYMENT


def test_kubernetes_resource_iter(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that the correct iterator is returned for the KubernetesResource object. This tests the
    overridden __iter__() method in the MutableMapping implementation.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    # iterate over the object and collect the key values
    keys: List = list()
    for key in sas_kubernetes_resource_obj.keys():
        keys.append(key)

    # make sure the expected keys were iterated over
    assert len(keys) == 5
    assert keys == [KubernetesResource.Keys.API_VERSION,
                    KubernetesResource.Keys.KIND,
                    KubernetesResource.Keys.METADATA,
                    KubernetesResource.Keys.SPEC,
                    KubernetesResource.Keys.STATUS]


def test_kubernetes_resource_len(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource len returns the correct number of top-level keys. This tests the
    overridden __len__() method in the MutableMapping implementation.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert len(sas_kubernetes_resource_obj) == 5


def test_kubernetes_resource_is_sas_resource_true(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.is_sas_resource() returns the correct value for a SAS resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.is_sas_resource() is True


def test_kubernetes_resource_is_sas_resource_false(non_sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.is_sas_resource() returns the correct value for a non-SAS resource.

    :param non_sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object for testing.
    """
    assert non_sas_kubernetes_resource_obj.is_sas_resource() is False


def test_kubernetes_resource_is_sas_resource_incomplete() -> None:
    """
    This test verifies that KubernetesResource.is_sas_resource() returns the correct value when no resource is defined.
    """
    assert KubernetesResource(dict()).is_sas_resource() is False


def test_kubernetes_resource_get_api_version(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_api_version() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_api_version() == "apps/v1"


def test_kubernetes_resource_get_api_version_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_api_version() returns None when the resource isn't defined.
    """
    assert KubernetesResource(dict()).get_api_version() is None


def test_kubernetes_resource_get_kind(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_kind() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_kind() == KubernetesResource.Kinds.DEPLOYMENT


def test_kubernetes_resource_get_kind_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_kind() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_kind() is None


def test_kubernetes_resource_get_metadata(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_kind() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    # get the metadata dict
    metadata: Dict = sas_kubernetes_resource_obj.get_metadata()

    # make sure it's the right type, length, and has the expected keys
    assert isinstance(metadata, dict)
    assert len(metadata) == 9
    assert KubernetesResource.Keys.ANNOTATIONS in metadata
    assert KubernetesResource.Keys.CREATION_TIMESTAMP in metadata
    assert KubernetesResource.Keys.GENERATION in metadata
    assert KubernetesResource.Keys.LABELS in metadata
    assert KubernetesResource.Keys.NAME in metadata
    assert KubernetesResource.Keys.NAMESPACE in metadata
    assert KubernetesResource.Keys.RESOURCE_VERSION in metadata
    assert KubernetesResource.Keys.SELF_LINK in metadata
    assert KubernetesResource.Keys.UID in metadata


def test_kubernetes_resource_get_metadata_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_metadata() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_metadata() is None


def test_kubernetes_resource_get_metadata_value(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_metadata_value() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_metadata_value(KubernetesResource.Keys.NAME) == "sas-annotations"


def test_kubernetes_resource_get_metadata_value_missing(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_kind() returns None for an undefined metadata key.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_metadata_value("foo") is None


def test_kubernetes_resource_get_metadata_value_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_metadata_value() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_metadata_value(KubernetesResource.Keys.NAME) is None


def test_kubernetes_resource_get_annotations(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_annotations() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    # get the annotations dict
    annotations: Dict = sas_kubernetes_resource_obj.get_annotations()

    # make sure it's the right size
    assert len(annotations) == 12

    # spot check than an expected annotation is defined
    assert KubernetesResource.Keys.ANNOTATION_COMPONENT_NAME in annotations


def test_kubernetes_resource_get_annotations_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_annotations() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_annotations() is None


def test_kubernetes_resource_get_sas_component_name(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_sas_component_name() returns the correct value for a defined SAS
    resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_sas_component_name() == "sas-annotations"


def test_kubernetes_resource_get_sas_component_name_non_sas_component(
        non_sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_sas_component_name() returns None for a defined non-SAS resource.

    :param non_sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object for testing.
    """
    assert non_sas_kubernetes_resource_obj.get_sas_component_name() is None


def test_kubernetes_resource_get_sas_component_name_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_sas_component_name() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_sas_component_name() is None


def test_kubernetes_resource_get_sas_component_version(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_sas_component_version() returns the correct value for a defined SAS
    resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_sas_component_version() == "2.2.20-20200420.1587366873499"


def test_kubernetes_resource_get_sas_component_version_non_sas_component(
        non_sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_sas_component_version() returns None for a defined non-SAS resource.

    :param non_sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object for testing.
    """
    assert non_sas_kubernetes_resource_obj.get_sas_component_version() is None


def test_kubernetes_resource_get_sas_component_version_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_sas_component_version() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_sas_component_version() is None


def test_kubernetes_resource_get_sas_version(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_sas_version() returns the correct value for a defined SAS resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_sas_version() == "2.2.20"


def test_kubernetes_resource_get_sas_version_non_sas_component(non_sas_kubernetes_resource_obj: KubernetesResource) \
        -> None:
    """
    This test verifies that KubernetesResource.get_kind() returns None for a defined non-SAS resource.

    :param non_sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object for testing.
    """
    assert non_sas_kubernetes_resource_obj.get_sas_version() is None


def test_kubernetes_resource_get_sas_version_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_sas_version() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_sas_version() is None


def test_kubernetes_resource_get_creation_timestamp(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_creation_timestamp() returns the correct value for a defined
    resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_creation_timestamp() == "2020-04-21T12:47:03Z"


def test_kubernetes_resource_get_creation_timestamp_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_creation_timestamp() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_creation_timestamp() is None


def test_kubernetes_resource_get_generation(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_generation() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_generation() == 1


def test_kubernetes_resource_get_generation_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_generation() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_generation() is None


def test_kubernetes_resource_get_labels(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_labels() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    # get the labels dict
    labels: Dict = sas_kubernetes_resource_obj.get_labels()

    # make sure it's the expected length
    assert len(labels) == 4

    # spot check that it contains an expected label
    assert "sas.com/admin" in labels


def test_kubernetes_resource_get_labels_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_labels() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_labels() is None


def test_kubernetes_resource_get_label(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_label() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_label("sas.com/admin") == "namespace"


def test_kubernetes_resource_get_label_missing(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_label() returns None for an undefined label on a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_label("foo") is None


def test_kubernetes_resource_get_label_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_label() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_label("sas.com/admin") is None


def test_kubernetes_resource_get_name(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_name() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_name() == "sas-annotations"


def test_kubernetes_resource_get_name_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_name() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_name() is None


def test_kubernetes_resource_get_namespace(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_namespace() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_namespace() == "test"


def test_kubernetes_resource_get_namespace_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_namespace() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_namespace() is None


def test_kubernetes_resource_get_resource_version(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_resource_version() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_resource_version() == "17399617"


def test_kubernetes_resource_get_resource_version_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_resource_version() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_resource_version() is None


def test_kubernetes_resource_get_self_link(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_self_link() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_self_link() == "/apis/apps/v1/namespaces/test/deployments/sas-annotations"


def test_kubernetes_resource_get_self_link_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_self_link() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_self_link() is None


def test_kubernetes_resource_get_uid(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_uid() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_uid() == "ec191de7-44db-46d5-b3b8-5b7af4141a58"


def test_kubernetes_resource_get_uid_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_uid() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_uid() is None


def test_kubernetes_resource_get_spec(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_spec() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    # get the spec dict
    spec: Dict = sas_kubernetes_resource_obj.get_spec()

    # make sure it's the right length
    assert len(spec) == 6

    # spot check for an expected key
    assert "progressDeadlineSeconds" in spec


def test_kubernetes_resource_get_spec_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_spec() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_spec() is None


def test_kubernetes_resource_get_spec_value(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_spec_value() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_spec_value("replicas") == 1


def test_kubernetes_resource_get_spec_value_missing(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_spec_value() returns None for an defined value on a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_spec_value("foo") is None


def test_kubernetes_resource_get_spec_value_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_spec_value() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_spec_value("replicas") is None


def test_kubernetes_resource_get_status(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_status() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    # get the status dict
    status: Dict = sas_kubernetes_resource_obj.get_status()

    # make sure it's the expected length
    assert len(status) == 5

    # spot check for an expected status key
    assert "observedGeneration" in status


def test_kubernetes_resource_get_status_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_status() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_status() is None


def test_kubernetes_resource_get_status_value(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_status_value() returns the correct value for a defined value on a
    defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_status_value("replicas") == 1


def test_kubernetes_resource_get_status_value_missing(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.get_status_value() returns None for an undefined value on a defined
    resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    assert sas_kubernetes_resource_obj.get_status_value("foo") is None


def test_kubernetes_resource_get_status_value_incomplete() -> None:
    """
    This test verifies that KubernetesResource.get_status_value() returns None for an undefined resource.
    """
    assert KubernetesResource(dict()).get_status_value("replicas") is None


def test_kubernetes_resource_as_dict(sas_kubernetes_resource_obj: KubernetesResource) -> None:
    """
    This test verifies that KubernetesResource.as_dict() returns the correct value for a defined resource.

    :param sas_kubernetes_resource_obj: The pre-loaded SAS KubernetesResource object fixture for testing.
    """
    # convert the object
    converted_resource: Dict = sas_kubernetes_resource_obj.as_dict()

    # make sure it's the expected type
    assert isinstance(converted_resource, dict)
