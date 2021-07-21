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

from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource


def aggregate_resources(resource_details: Dict, gathered_resources: Dict, component: Dict):
    """
    Aggregates the various resources that comprise a SAS component deployed into the Kubernetes cluster.

    This method is called recursively for each relationship extension to aggregate all related resources.

    :param resource_details: The details of the resource to aggregate into a component.
    :param gathered_resources: The complete dictionary of resources gathered in the Kubernetes cluster.
    :param component: The dictionary where the resources for the current component will be compiled.
    """
    # set up the component dict
    if NAME_KEY not in component:
        component[NAME_KEY]: Text = ""

    if ITEMS_KEY not in component:
        component[ITEMS_KEY]: Dict = dict()

    # get the relationships extension list for this resource
    resource_ext: Dict = resource_details[ReportKeys.ResourceDetails.EXT_DICT]
    resource_relationships: List = resource_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]

    # get the resource definition
    resource: KubernetesResource = resource_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

    # if a SAS component name is defined, use it since this is the most canonical value
    if resource.get_annotation(KubernetesResource.Keys.ANNOTATION_COMPONENT_NAME) is not None:
        component[NAME_KEY] = resource.get_annotation(KubernetesResource.Keys.ANNOTATION_COMPONENT_NAME)

    # if a resource of this kind hasn't been added for the component, create the kind key
    if resource.get_kind() not in component[ITEMS_KEY]:
        component[ITEMS_KEY][resource.get_kind()]: Dict = dict()

    # add the resource details to its kind dictionary, keyed by its name
    component[ITEMS_KEY][resource.get_kind()][resource.get_name()]: Dict = resource_details

    # aggregate any resources defined in the relationships extension #
    for relationship in resource_relationships:
        # get the name and kind of the related resource #
        rel_kind: Text = relationship[ReportKeys.ResourceDetails.Ext.Relationship.KIND]
        rel_name: Text = relationship[ReportKeys.ResourceDetails.Ext.Relationship.NAME]

        # get the details for the related resource
        try:
            related_resource_details: Optional[Dict] = gathered_resources[rel_kind][ITEMS_KEY][rel_name]
        except KeyError:
            # ignore any failures that may be raised if the resource is transient and not defined
            # note that the related resource wasn't found
            related_resource_details: Optional[Dict] = None

        # aggregate the related resource
        if related_resource_details is not None:
            aggregate_resources(related_resource_details, gathered_resources, component)

    # if this is the last resource in the chain and the component doesn't have a name determined from an annotation,
    # set a name based on the available values
    if not component[NAME_KEY]:
        component[NAME_KEY]: Text = resource.get_name()

    # if a SAS component name is defined, use it instead
    if resource.get_annotation(KubernetesResource.Keys.ANNOTATION_COMPONENT_NAME) is not None:
        component[NAME_KEY] = resource.get_annotation(KubernetesResource.Keys.ANNOTATION_COMPONENT_NAME)
