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

from viya_ark_library.k8s.sas_k8s_objects import KubernetesApiResources, KubernetesResource
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface


# last applied config annotation
_LAST_APPLIED_CONFIG_ANNOTATION_ = "kubectl.kubernetes.io/last-applied-configuration"


def gather_details(kubectl: KubectlInterface, gathered_resources: Dict,
                   api_resources: KubernetesApiResources, resource_kind: Text) -> None:
    """
    Gathers details about resources in the target Kubernetes cluster.

    The method is called recursively and will gather details about any resources described in the current resource's
    "ownerReferences", if defined. If all discovered resource kinds are listable, a complete ownership chain will be
    gathered.

    :param kubectl: The KubectlInterface object for issuing requests to the target Kubernetes cluster.
    :param gathered_resources: The dictionary where gathered resources will be stored.
    :param api_resources: The KubernetesApiResources object defining the API resources available in the target
                          Kubernetes cluster.
    :param resource_kind: The 'kind' value of the resources to gather.
    """
    # if an attempt has been made to gather this kind, return without moving forward
    if resource_kind in gathered_resources:
        return

    # get the resource name associated with the kind
    resource_name: Text = api_resources.get_name(resource_kind)

    # create a list to hold the resources gathered for this kind
    resources: List[KubernetesResource] = list()

    # note whether the resource is available for listing
    resource_available: bool = True

    if resource_name:
        try:
            # get the name associated with the resource kind
            resources: Optional[List[KubernetesResource]] = kubectl.get_resources(api_resources.get_name(resource_kind))
        except CalledProcessError as e:
            if resource_kind == KubernetesResource.Kinds.POD:
                # if a CalledProcessError is raised for pods, surface the error
                # if the resource kind is not "Pod", move forward without raising an error since
                # pods can still be reported
                raise e
            else:
                # note that this resource was not available
                resource_available = False

    # save the resources by kind
    gathered_resources[resource_kind]: Dict = dict()

    # create a key to note whether this resource kind was available for listing: bool
    gathered_resources[resource_kind][Keys.KindDetails.AVAILABLE]: bool = resource_available

    # create a key to define the number of resources of this kind returned by k8s: int
    gathered_resources[resource_kind][Keys.KindDetails.COUNT]: int = len(resources)

    # create a key to hold the resources returned by k8s: dict
    gathered_resources[resource_kind][ITEMS_KEY]: bool = dict()

    # store a unique list of kinds in any 'ownerReferences' definitions
    owner_kinds: List = list()

    # loop over the resources returned
    for resource in resources:
        # remove the 'managedFields' key, if it exists, to reduce file size
        metadata: Optional[Dict] = resource.get_metadata()
        if metadata:
            metadata.pop(KubernetesResource.Keys.MANAGED_FIELDS, None)

        # remove the 'kubectl.kubernetes.io/last-applied-configuration' annotation, if it exists, to reduce file size
        annotations: Optional[Dict] = resource.get_annotations()
        if annotations:
            annotations.pop(_LAST_APPLIED_CONFIG_ANNOTATION_, None)

        # add the resource to its kind dictionary
        # create a key set to the name of the resource, under which all resource details will be stored: dict
        resource_details = gathered_resources[resource_kind][ITEMS_KEY][resource.get_name()] = dict()

        # create a key to hold extra details about the resource not provided in the resource definition: dict
        resource_details[Keys.ResourceDetails.EXT_DICT]: Dict = dict()

        # create a key to hold the ext.relationships list, which defines the name and kind of resources
        # related to this resource: list
        resource_ext: Dict = resource_details[Keys.ResourceDetails.EXT_DICT]
        resource_relationships = resource_ext[Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST] = list()

        # create a key under which the resource definition will be stored: KubernetesResource
        resource_details[Keys.ResourceDetails.RESOURCE_DEFINITION]: KubernetesResource = resource

        # see if this resource defines any 'ownerReferences'
        owner_references: List = resource.get_metadata_value(KubernetesResource.Keys.OWNER_REFERENCES)

        # if the resource does define 'ownerReferences', process them
        if owner_references is not None:
            # iterate over the references
            for owner_reference in owner_references:
                # if the owner reference kind isn't in the owner_kinds list, add it
                if owner_reference[KubernetesResource.Keys.KIND] not in owner_kinds:
                    owner_kinds.append(owner_reference[KubernetesResource.Keys.KIND])

                # create a relationship for the owning object
                owner_kind = owner_reference[KubernetesResource.Keys.KIND]
                owner_name = owner_reference[KubernetesResource.Keys.NAME]
                relationship: Dict = relationship_util.create_relationship_dict(owner_kind, owner_name)

                # and add it to the relationship list
                resource_relationships.append(relationship)

    # if more kinds have been discovered, gather them as well #
    for owner_kind in owner_kinds:
        gather_details(kubectl, gathered_resources, api_resources, owner_kind)
