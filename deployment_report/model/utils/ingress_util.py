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

from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource


def determine_ingress_controller(gathered_resources: Dict) -> Optional[Text]:
    """
    Determines the ingress controller being used in the Kubernetes cluster.

    :param gathered_resources: The complete dictionary of gathered resources from the Kubernetes cluster.
    :return: The ingress controller used in the target cluster or None if the controller cannot be determined.
    """
    for ingress_controller, kind in SupportedIngress.get_ingress_controller_to_kind_map().items():
        # check if this kind is in the dictionary of gathered resources
        if kind in gathered_resources:
            for resource_details in gathered_resources[kind][ITEMS_KEY].values():
                # get the resource definition
                resource: KubernetesResource = resource_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

                # check if the resource was created by SAS
                if resource.is_sas_resource():
                    return ingress_controller

    # if a controller couldn't be determined, return None
    return None


def ignorable_for_controller_if_unavailable(ingress_controller: Text, kind: Text) -> bool:
    """
    Determines whether the given kind is ignorable if unavailable given the ingress controller.

    Example: Unavailable HTTPProxy, Route, and VirtualService kinds can be ignored if ingress is controlled by NGINX.

    :param ingress_controller: The ingress controller used by the deployment.
    :param kind: The kind of the unavailable resource.
    """
    ####################
    # Contour
    ####################
    if ingress_controller == SupportedIngress.Controllers.CONTOUR and (
            kind == KubernetesResource.Kinds.INGRESS or
            kind == KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE or
            kind == KubernetesResource.Kinds.OPENSHIFT_ROUTE
    ):
        # ignore Ingress, Route, and VirtualService if controller is Contour
        return True

    ####################
    # Istio
    ####################
    elif ingress_controller == SupportedIngress.Controllers.ISTIO and (
            kind == KubernetesResource.Kinds.CONTOUR_HTTPPROXY or
            kind == KubernetesResource.Kinds.INGRESS or
            kind == KubernetesResource.Kinds.OPENSHIFT_ROUTE
    ):
        # ignore HTTPProxy, Ingress, and Route if controller is Istio
        return True

    ####################
    # NGINX
    ####################
    elif ingress_controller == SupportedIngress.Controllers.NGINX and (
            kind == KubernetesResource.Kinds.CONTOUR_HTTPPROXY or
            kind == KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE or
            kind == KubernetesResource.Kinds.OPENSHIFT_ROUTE
    ):
        # ignore HTTPProxy, Route, and VirtualService if controller is NGINX
        return True

    ####################
    # OpenShift
    ####################
    elif ingress_controller == SupportedIngress.Controllers.OPENSHIFT and (
            kind == KubernetesResource.Kinds.CONTOUR_HTTPPROXY or
            kind == KubernetesResource.Kinds.INGRESS or
            kind == KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE
    ):
        # ignore HTTPProxy, Ingress, and VirtualService if controller is OpenShift
        return True

    # not ignorable
    return False
