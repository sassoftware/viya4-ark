####################################################################
# ### viya_deployment_report_keys.py                             ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

# key used in the temporary gathered_resources dictionary under which the resource definitions are stored #
ITEMS_KEY = "items"


class ViyaDeploymentReportKeys(object):
    """
    Class defining static references to the top-level keys in the resulting ViyaDeploymentReport data structure.
    """
    GATHERED = "_gathered"
    KUBERNETES_DICT = "kubernetes"
    OTHER_COMPONENTS_DICT = "otherComponents"
    SAS_COMPONENTS_DICT = "sasComponents"
    UNAVAILABLE_RESOURCES_LIST = "_unavailableResources"

    class KindDetails(object):
        """
        Class defining static references to keys in kind detail dictionaries in resulting ViyaDeploymentReport data
        structure.
        """
        AVAILABLE = "available"
        COUNT = "count"
        SAS_CRD = "sasCRD"

    class Kubernetes(object):
        """
        Class defining static references to keys in the 'kubernetes' dictionary in the resulting ViyaDeploymentReport
        data structure.
        """
        API_RESOURCES_DICT = "apiResources"
        API_VERSIONS_LIST = "apiVersions"
        DISCOVERED_KINDS_DICT = "discoveredKinds"
        INGRESS_CTRL = "ingressController"
        NAMESPACE = "namespace"
        NODES_DICT = "nodes"
        VERSIONS_DICT = "versions"

    class ResourceDetails(object):
        """
        Class defining static references to keys in resource detail dictionaries in the resulting ViyaDeploymentReport
        data structure.
        """
        EXT_DICT = "ext"
        RESOURCE_DEFINITION = "resourceDefinition"

        class Ext(object):
            """
            Class defining static references to keys in the 'ext' dictionary for resources in the resulting
            ViyaDeploymentReport data structure.
            """
            COMPONENT_NAME = "componentName"
            LOG_SNIP_LIST = "logSnip"
            METRICS_DICT = "metrics"
            RELATIONSHIPS_LIST = "relationships"

            class Relationship(object):
                """
                Class defining static references to keys in resource's ext.relationships list in the resulting
                ViyaDeploymentReport data structure.
                """
                KIND = "kind"
                NAME = "name"
