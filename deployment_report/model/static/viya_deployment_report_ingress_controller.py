####################################################################
# ### viya_deployment_report_ingress_controller.py               ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################


class ViyaDeploymentReportIngressController(object):
    """
    Class defining static references to the supported ingress controller values.
    """
    KUBE_NGINX = "kube-nginx"
    ISTIO = "istio"
