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
from typing import Dict, List, Text

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues
from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress


def test_get_ingress_controller_to_kind_map() -> None:
    """
    Verifies the current supported ingress controllers are in the map and
    that their kinds are correctly mapped.
    """
    supported_ingress_map: Dict[Text, List[Text]] = SupportedIngress.get_ingress_controller_to_resource_types_map()

    # assert 4 supported ingress controllers
    assert len(supported_ingress_map) == 4

    # Contour
    assert SupportedIngress.Controllers.CONTOUR in supported_ingress_map
    assert len(supported_ingress_map[SupportedIngress.Controllers.CONTOUR]) == 1
    assert supported_ingress_map[SupportedIngress.Controllers.CONTOUR][0] == \
           KubernetesResourceTypeValues.CONTOUR_HTTP_PROXIES

    # Istio
    assert SupportedIngress.Controllers.ISTIO in supported_ingress_map
    assert len(supported_ingress_map[SupportedIngress.Controllers.ISTIO]) == 1
    assert supported_ingress_map[SupportedIngress.Controllers.ISTIO][0] == \
           KubernetesResourceTypeValues.ISTIO_VIRTUAL_SERVICES

    # NGINX
    assert SupportedIngress.Controllers.NGINX in supported_ingress_map
    assert len(supported_ingress_map[SupportedIngress.Controllers.NGINX]) == 2
    assert supported_ingress_map[SupportedIngress.Controllers.NGINX][0] == \
           KubernetesResourceTypeValues.K8S_NETWORKING_INGRESSES
    assert supported_ingress_map[SupportedIngress.Controllers.NGINX][1] == \
           KubernetesResourceTypeValues.K8S_EXTENSIONS_INGRESSES

    # OpenShift
    assert SupportedIngress.Controllers.OPENSHIFT in supported_ingress_map
    assert len(supported_ingress_map[SupportedIngress.Controllers.OPENSHIFT]) == 1
    assert supported_ingress_map[SupportedIngress.Controllers.OPENSHIFT][0] == \
           KubernetesResourceTypeValues.OPENSHIFT_ROUTES

    # Verify NGINX is the last key in the dict
    assert list(supported_ingress_map.keys())[-1] == SupportedIngress.Controllers.NGINX
