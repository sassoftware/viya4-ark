####################################################################
# ### sas_k8s_ingress.py                                         ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from typing import Dict, Text

from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource


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

    @staticmethod
    def get_ingress_controller_to_kind_map() -> Dict[Text, Text]:
        """
        Returns a dictionary mapping an ingress controller type to the k8s resource kind that it uses.
        This can be used when evaluating a deployment to see which controller is used based on the presence
        of resources defined in the cluster.
        """
        return {
            SupportedIngress.Controllers.CONTOUR: KubernetesResource.Kinds.CONTOUR_HTTPPROXY,
            SupportedIngress.Controllers.ISTIO: KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE,
            SupportedIngress.Controllers.OPENSHIFT: KubernetesResource.Kinds.OPENSHIFT_ROUTE,
            # NGINX is placed last in the map intentionally
            # Ingress kinds could be present in deployments using one of the above controllers
            # If iterating over the dict, NGINX should be evaluated last to avoid false-positives
            SupportedIngress.Controllers.NGINX: KubernetesResource.Kinds.INGRESS
        }
