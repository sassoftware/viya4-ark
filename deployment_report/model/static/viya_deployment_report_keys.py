####################################################################
# ### viya_deployment_report_keys.py                             ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

# key used in the temporary gathered_resources and components dictionaries
# under which the resource definitions are stored
ITEMS_KEY = "items"
# key used in the temporary components dictionary under which the component name is stored
NAME_KEY = "name"


class ViyaDeploymentReportKeys(object):
    """
    Class defining static references to the top-level keys in the resulting ViyaDeploymentReport data structure.
    """
    GATHERED = "_gathered"
    KUBERNETES_DICT = "kubernetes"
    OTHER_COMPONENTS_DICT = "otherComponents"
    SAS_COMPONENTS_DICT = "sasComponents"
    UNAVAILABLE_RESOURCES_LIST = "_unavailableResources"

    class ResourceTypeDetails(object):
        """
        Class defining static references to keys in resource type details dictionaries in resulting
        ViyaDeploymentReport data structure.
        """
        AVAILABLE = "available"
        COUNT = "count"
        KIND = "kind"
        SAS_CRD = "sasCRD"

    class Kubernetes(object):
        """
        Class defining static references to keys in the 'kubernetes' dictionary in the resulting ViyaDeploymentReport
        data structure.
        """
        API_RESOURCES_DICT = "apiResources"
        API_VERSIONS_LIST = "apiVersions"
        CADENCE_INFO = "cadenceInfo"
        DB_INFO = "dbInfo"
        DISCOVERED_RESOURCE_TYPES_DICT = "discoveredResourceTypes"
        INGRESS_CTRL = "ingressController"
        NAMESPACE = "namespace"
        NODES_DICT = "nodes"
        VERSIONS_DICT = "versions"

    class ResourceDetails(object):
        """
        Class defining static references to keys in resource details dictionaries in the resulting ViyaDeploymentReport
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
            RESOURCE_TYPE = "resourceType"

            class Relationship(object):
                """
                Class defining static references to keys in resource's ext.relationships list in the resulting
                ViyaDeploymentReport data structure.
                """
                RESOURCE_NAME = "resourceName"
                RESOURCE_TYPE = "resourceType"

    class DatabaseDetails(object):
        """
        Class defining static references to keys in Database details dictionaries in resulting
        ViyaDeploymentReport data structure.
        """
        DBHOST = "host"
        DBNAME = "name"
        DBPORT = "port"
        DBTYPE = "type"
        DBSSL = "sslEnabled"
        DBCONN = "connection"
