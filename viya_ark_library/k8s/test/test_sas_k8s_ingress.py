####################################################################
# ### test_sas_k8s_ingress.py                                    ###
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

from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource


def test_get_ingress_controller_to_kind_map() -> None:
    """
    Verifies the current supported ingress controllers are in the map and
    that their kinds are correctly mapped.
    """
    supported_ingress_map: Dict[Text, Text] = SupportedIngress.get_ingress_controller_to_kind_map()

    # assert 4 supported ingress controllers
    assert len(supported_ingress_map) == 4

    # Contour
    assert SupportedIngress.Controllers.CONTOUR in supported_ingress_map
    assert supported_ingress_map[SupportedIngress.Controllers.CONTOUR] == KubernetesResource.Kinds.CONTOUR_HTTPPROXY

    # Istio
    assert SupportedIngress.Controllers.ISTIO in supported_ingress_map
    assert supported_ingress_map[SupportedIngress.Controllers.ISTIO] == KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE

    # NGINX
    assert SupportedIngress.Controllers.NGINX in supported_ingress_map
    assert supported_ingress_map[SupportedIngress.Controllers.NGINX] == KubernetesResource.Kinds.INGRESS

    # OpenShift
    assert SupportedIngress.Controllers.OPENSHIFT in supported_ingress_map
    assert supported_ingress_map[SupportedIngress.Controllers.OPENSHIFT] == KubernetesResource.Kinds.OPENSHIFT_ROUTE

    # Verify NGINX is the last key in the dict
    assert list(supported_ingress_map.keys())[-1] == SupportedIngress.Controllers.NGINX
