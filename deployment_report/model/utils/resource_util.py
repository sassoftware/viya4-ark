####################################################################
# ### resource_util.py                                           ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from subprocess import CalledProcessError
from typing import Dict, List, Optional, Text

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as Keys
from deployment_report.model.utils import relationship_util

from viya_ark_library.k8s.k8s_resource_keys import KubernetesResourceKeys
from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface


# last applied config annotation
_LAST_APPLIED_CONFIG_ANNOTATION_ = "kubectl.kubernetes.io/last-applied-configuration"


def cache_resources(resource_type: Text, kubectl: KubectlInterface, resource_cache: Dict) -> None:
    """
    Gets resources in the target Kubernetes cluster and stores them in the provided resource_cache dictionary.

    The method is called recursively and will gather any resources described in "ownerReferences" definitions, if
    defined. If all discovered resources are listable, a complete ownership chain will be cached.

    :param resource_type: The type (name, name.group, or name.version.group) of the resources to cache.
    :param kubectl: The KubectlInterface object configured for issuing requests to the target Kubernetes cluster.
    :param resource_cache: The dictionary where resources will be cached by type.
    """
    # if the current resource type as already been cached, return without moving forward
    if resource_type in resource_cache:
        return

    # create a list to hold the resources gathered of this resource type
    resources: List[KubernetesResource] = list()

    # note whether the resource is available for listing
    resource_type_available: bool = True

    try:
        # list the resources of the requested type
        resources = kubectl.get_resources(resource_type)
    except CalledProcessError as e:
        if resource_type == KubernetesResourceTypeValues.K8S_CORE_PODS:
            # if a CalledProcessError is raised for pods, surface the error
            # if the resource type is not pods, move forward without raising an error since
            # pods can still be reported
            raise e
        else:
            # note that this resource was not available
            resource_type_available = False

    # cache the resources by type
    resource_cache[resource_type]: Dict = dict()
    resource_type_details: Dict = resource_cache[resource_type]

    # create a key to note whether this resource type was available for listing: bool
    resource_type_details[Keys.ResourceTypeDetails.AVAILABLE]: bool = resource_type_available

    # create a key to define the number of resources of this type returned by k8s: int
    resource_type_details[Keys.ResourceTypeDetails.COUNT]: int = len(resources)

    # create a key to define the kind value of this resource type: str
    resource_kind: Text = kubectl.api_resources().get_kind(resource_type=resource_type)
    resource_type_details[Keys.ResourceTypeDetails.KIND]: Text = resource_kind

    # create a key to hold the resources returned by k8s: dict
    resource_type_details[ITEMS_KEY]: Dict = dict()
    resource_type_items: Dict = resource_type_details[ITEMS_KEY]

    # store a unique list of resource types that will be discovered from 'ownerReferences' definitions
    owning_resource_types: List[Text] = list()

    # loop over the resources returned
    for resource in resources:
        # remove the 'managedFields' key, if it exists, to reduce file size
        metadata: Optional[Dict] = resource.get_metadata()
        if metadata:
            metadata.pop(KubernetesResourceKeys.MANAGED_FIELDS, None)

        # remove the 'kubectl.kubernetes.io/last-applied-configuration' annotation, if it exists, to reduce file size
        annotations: Optional[Dict] = resource.get_annotations()
        if annotations:
            annotations.pop(_LAST_APPLIED_CONFIG_ANNOTATION_, None)

        # add the resource to its resource type dictionary
        # create a dict keyed by the name of the resource, under which all resource details will be stored: dict
        resource_type_items[resource.get_name()]: Dict = dict()
        resource_details: Dict = resource_type_items[resource.get_name()]

        # create a key to hold extended details about the resource not provided in the resource definition: dict
        resource_details[Keys.ResourceDetails.EXT_DICT]: Dict = dict()
        resource_ext: Dict = resource_details[Keys.ResourceDetails.EXT_DICT]

        # create a key under which the resource type value will be stored: str
        resource_ext[Keys.ResourceDetails.Ext.RESOURCE_TYPE]: Text = resource_type

        # create a key to hold the ext.relationships list, which defines the name and kind of resources
        # related to this resource: list
        resource_ext[Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST]: List[Dict] = list()
        resource_relationships: List[Dict] = resource_ext[Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST]

        # create a key under which the resource definition will be stored: KubernetesResource
        resource_details[Keys.ResourceDetails.RESOURCE_DEFINITION]: KubernetesResource = resource

        # skip ownerReferences for secret and configmap
        if resource_type == "configmaps" or resource_type == "secrets":
            continue

        # see if this resource defines any 'ownerReferences'
        owner_references: Optional[List[Dict]] = resource.get_metadata_value(KubernetesResourceKeys.OWNER_REFERENCES)

        # if the resource does define 'ownerReferences', process them
        if owner_references is not None:
            # iterate over the references
            for owner_reference in owner_references:
                # get the requisite values from the owner reference
                owner_api_version: Text = owner_reference[KubernetesResourceKeys.API_VERSION]
                owner_kind: Text = owner_reference[KubernetesResourceKeys.KIND]
                owner_name: Text = owner_reference[KubernetesResourceKeys.NAME]

                # lookup the owner's resource type
                owner_type: Text = kubectl.api_resources().get_type(kind=owner_kind, api_version=owner_api_version)

                # if the owning resource type isn't in the owning resource types list, add it
                if owner_type not in owning_resource_types:
                    owning_resource_types.append(owner_type)

                # create a relationship for the owning object
                relationship: Dict = relationship_util.create_relationship_dict(resource_name=owner_name,
                                                                                resource_type=owner_type)

                # and add it to the relationship list
                resource_relationships.append(relationship)

    # if more resource types have been discovered, gather them as well
    for owning_resource_type in owning_resource_types:
        cache_resources(resource_type=owning_resource_type,
                        kubectl=kubectl,
                        resource_cache=resource_cache)
