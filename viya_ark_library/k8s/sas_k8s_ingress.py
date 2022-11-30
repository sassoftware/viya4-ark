####################################################################
# ### sas_k8s_ingress.py                                         ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2022, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from typing import Dict, List, Text

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues


class SupportedIngress(object):
    """
    Values and utility methods to help in determining the ingress controller used by a k8s deployment.
    """

    class Controllers(object):
        """
        Displayable name values for supported ingress controllers.
        """
        CONTOUR = "Contour"
        ISTIO = "Istio"
        NGINX = "NGINX"
        OPENSHIFT = "OpenShift"
        UNSUPPORTED = "Unsupported"
        NS_CONTOUR = "projectcontour"
        NS_ISTIO = "istio-system"
        NS_NGINX = "ingress-nginx"
        NS_OPENSHIFT = "openshift-ingress-operator"

    @staticmethod
    def get_ingress_controller_to_resource_types_map() -> Dict[Text, List[Text]]:
        """
        Returns a dictionary mapping an ingress controller type to the k8s resource types that it uses.
        This can be used when evaluating a deployment to see which controller is used based on the presence
        of resources/resource types defined in the cluster.
        """
        return {
            SupportedIngress.Controllers.CONTOUR: [KubernetesResourceTypeValues.CONTOUR_HTTP_PROXIES],
            SupportedIngress.Controllers.ISTIO: [KubernetesResourceTypeValues.ISTIO_VIRTUAL_SERVICES],
            SupportedIngress.Controllers.OPENSHIFT: [KubernetesResourceTypeValues.OPENSHIFT_ROUTES],
            # NGINX is placed last in the map intentionally
            # Ingress kinds could be present in deployments using one of the above controllers
            # If iterating over the dict, NGINX should be evaluated last to avoid false-positives
            SupportedIngress.Controllers.NGINX: [
                KubernetesResourceTypeValues.K8S_NETWORKING_INGRESSES,
                KubernetesResourceTypeValues.K8S_EXTENSIONS_INGRESSES
            ]
        }
