####################################################################
# ### ingress_util.py                                            ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from typing import Dict, Optional, Text

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as ReportKeys

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues
from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource


def determine_ingress_controller(gathered_resources: Dict) -> Optional[Text]:
    """
    Determines the ingress controller being used in the Kubernetes cluster.

    :param gathered_resources: The complete dictionary of gathered resources from the Kubernetes cluster.
    :return: The ingress controller used in the target cluster or None if the controller cannot be determined.
    """
    for ingress_controller, resource_types in SupportedIngress.get_ingress_controller_to_resource_types_map().items():
        # iterate over all resource types
        for resource_type in resource_types:
            # check if this kind is in the dictionary of gathered resources
            if resource_type in gathered_resources:
                for resource_details in gathered_resources[resource_type][ITEMS_KEY].values():
                    # get the resource definition
                    resource: KubernetesResource = resource_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

                    # check if the resource was created by SAS
                    if resource.is_sas_resource():
                        return ingress_controller

    # if a controller couldn't be determined, return None
    return None


def ignorable_for_controller_if_unavailable(ingress_controller: Text, resource_type: Text) -> bool:
    """
    Determines whether the given resource type is ignorable if unavailable given the ingress controller.

    Example: Unavailable HTTPProxy, Route, and VirtualService resources can be ignored if NGINX controls ingress.

    :param ingress_controller: The ingress controller used by the deployment.
    :param resource_type: The resource type of the unavailable resource.
    """
    ####################
    # Contour
    ####################
    if ingress_controller == SupportedIngress.Controllers.CONTOUR and (
            resource_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
            resource_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES or
            resource_type == ResourceTypeValues.OPENSHIFT_ROUTES or
            resource_type == ResourceTypeValues.ISTIO_VIRTUAL_SERVICES
    ):
        # ignore Ingress, Route, and VirtualService if controller is Contour
        return True

    ####################
    # Istio
    ####################
    elif ingress_controller == SupportedIngress.Controllers.ISTIO and (
            resource_type == ResourceTypeValues.CONTOUR_HTTP_PROXIES or
            resource_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
            resource_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES or
            resource_type == ResourceTypeValues.OPENSHIFT_ROUTES
    ):
        # ignore HTTPProxy, Ingress, and Route if controller is Istio
        return True

    ####################
    # NGINX
    ####################
    elif ingress_controller == SupportedIngress.Controllers.NGINX and (
            resource_type == ResourceTypeValues.CONTOUR_HTTP_PROXIES or
            resource_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
            resource_type == ResourceTypeValues.OPENSHIFT_ROUTES or
            resource_type == ResourceTypeValues.ISTIO_VIRTUAL_SERVICES
    ):
        # ignore HTTPProxy, Route, and VirtualService if controller is NGINX
        return True

    ####################
    # OpenShift
    ####################
    elif ingress_controller == SupportedIngress.Controllers.OPENSHIFT and (
            resource_type == ResourceTypeValues.CONTOUR_HTTP_PROXIES or
            resource_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
            resource_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES or
            resource_type == ResourceTypeValues.ISTIO_VIRTUAL_SERVICES
    ):
        # ignore HTTPProxy, Ingress, and VirtualService if controller is OpenShift
        return True

    # not ignorable
    return False
