####################################################################
# ### component_util.py                                          ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from typing import Dict, List, Optional, Text

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    NAME_KEY, \
    ViyaDeploymentReportKeys as ReportKeys
from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues

from viya_ark_library.k8s.k8s_resource_keys import KubernetesResourceKeys
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource

def is_component_initialized(component: Dict) -> bool:
    """ Checks whether the component has been initialized with any resources."""
    return bool(component.get(ITEMS_KEY))

def is_pods_present(component: Dict, pods_const: Text) -> bool:
    """ Checks whether the component has pods resource type defined in its items."""
    items = component.get(ITEMS_KEY)
    # prefer passing the project's canonical constant for pods (e.g. ResourceTypeValues.K8S_CORE_PODS)
    return bool(items and pods_const in items and items[pods_const])

def get_resource_type(resource_details: Dict) -> Optional[Text]:
    """ Gets the resource type of the provided resource details, if defined."""
    # safe access: the resource type lives under the extension dict
    ext = resource_details.get(ReportKeys.ResourceDetails.EXT_DICT, {})
    return ext.get(ReportKeys.ResourceDetails.Ext.RESOURCE_TYPE)


def aggregate_resources(resource_details: Dict, component: Dict, resource_cache: Dict) -> None:
    """
    Aggregates the various resources that comprise a SAS component deployed into the Kubernetes cluster.

    This method is called recursively for each relationship extension to aggregate all related resources.

    :param resource_details: The details of the resource that will be used to aggregate other resources that comprise
                             a SAS component. Most commonly, the resource details provided will be for a Pod.
    :param component: The dictionary where the related resources comprising the component will be compiled.
    :param resource_cache: The complete dictionary of resources cached from the Kubernetes cluster.
    """
    # set up the component dict
    if NAME_KEY not in component:
        component[NAME_KEY]: Text = ""

    if ITEMS_KEY not in component:
        component[ITEMS_KEY]: Dict = dict()

    # get the relationships extension list for this resource
    resource_ext: Dict = resource_details[ReportKeys.ResourceDetails.EXT_DICT]
    resource_relationships: List = resource_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]

    # if the component has already been initialized with pods and this resource is a pod,
    # return without moving forward to avoid redundant processing and potential recursion
    # k8s resource relationships.
    if (is_component_initialized(component)
            and is_pods_present(component, KubernetesResourceTypeValues.K8S_CORE_PODS)
            and get_resource_type(resource_details) == KubernetesResourceTypeValues.K8S_CORE_PODS):
        return

    # get the resource type value of this resource
    resource_type: Text = resource_ext[ReportKeys.ResourceDetails.Ext.RESOURCE_TYPE]

    # get the resource definition
    resource: KubernetesResource = resource_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

    # if a SAS component name is defined, use it since this is the most canonical value
    if resource.get_annotation(KubernetesResourceKeys.ANNOTATION_COMPONENT_NAME) is not None:
        component[NAME_KEY] = resource.get_annotation(KubernetesResourceKeys.ANNOTATION_COMPONENT_NAME)

    # if a resource of this type hasn't been added for the component, create the type key
    if resource_type not in component[ITEMS_KEY]:
        component[ITEMS_KEY][resource_type]: Dict = dict()

    # add the resource details to its kind dictionary, keyed by its name
    component[ITEMS_KEY][resource_type][resource.get_name()]: Dict = resource_details

    # aggregate any resources defined in the relationships extension
    for relationship in resource_relationships:
        # get the name and type of the related resource
        rel_name: Text = relationship[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
        rel_type: Text = relationship[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]

        # get the details for the related resource
        try:
            related_resource_details: Optional[Dict] = resource_cache[rel_type][ITEMS_KEY][rel_name]
        except KeyError:
            # ignore any failures that may be raised if the resource is transient and not defined
            # note that the related resource wasn't found
            related_resource_details: Optional[Dict] = None

        # aggregate the related resource
        if related_resource_details is not None:
            try:
                aggregate_resources(resource_details=related_resource_details,
                                    component=component,
                                    resource_cache=resource_cache)
            except RecursionError as e:
                # minimal console output, no stack trace
                print(f"\nRecursionError while aggregating k8s resources {rel_type}/{rel_name}. \n{e}")
                return

    # if this is the last resource in the chain and the component doesn't have a name determined from an annotation,
    # set a name based on the available values
    if not component[NAME_KEY]:
        component[NAME_KEY]: Text = resource.get_name()

    # if a SAS component name is defined, use it instead
    if resource.get_annotation(KubernetesResourceKeys.ANNOTATION_COMPONENT_NAME) is not None:
        component[NAME_KEY] = resource.get_annotation(KubernetesResourceKeys.ANNOTATION_COMPONENT_NAME)
