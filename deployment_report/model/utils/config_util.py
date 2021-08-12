####################################################################
# ### config_util.py                                             ###
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

from deployment_report.model.static.viya_deployment_report_keys import ViyaDeploymentReportKeys

from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource

# ConfigMap name containing SAS deployment metadata values
_SAS_DEPLOYMENT_METADATA_CONFIG_MAP_NAME_ = "sas-deployment-metadata"
# ConfigMap name containing SAS postgres config values
_SAS_POSTGRES_CONFIG_CONFIG_MAP_NAME_ = "sas-postgres-config"

# SAS deployment metadata keys
_CADENCE_DISPLAY_NAME_KEY_ = "SAS_CADENCE_DISPLAY_NAME"
_CADENCE_RELEASE_KEY_ = "SAS_CADENCE_RELEASE"
_CADENCE_VERSION_KEY_ = "SAS_CADENCE_VERSION"

# SAS postgres config keys
_DATABASE_HOST_KEY_ = "DATABASE_HOST"
_DATABASE_NAME_KEY_ = "DATABASE_NAME"
_DATABASE_PORT_KEY_ = "DATABASE_PORT"
_EXTERNAL_DATABASE_KEY_ = "EXTERNAL_DATABASE"
_DATASOURCE_USERNAME_KEY_ = "SPRING_DATASOURCE_USERNAME"

# database info keys
_HOST_KEY_ = "host"
_NAME_KEY_ = "name"
_PORT_KEY_ = "port"
_TYPE_KEY_ = "type"
_USER_KEY_ = "user"

# database info values
_EXTERNAL_DB_ = "External"
_INTERNAL_DB_ = "Internal"


def get_cadence_version(config_maps: Dict) -> Optional[Text]:
    """
    Returns the cadence version of the targeted SAS deployment.

    :param config_maps: The ConfigMap resources to evaluate.

    :return: A string representing the cadence version of the targeted SAS deployment, or None if the given
             ConfigMap does not contain the requested information.
    """
    # look for the necessary ConfigMap
    for config_map_name, config_map_details in config_maps.items():
        if _SAS_DEPLOYMENT_METADATA_CONFIG_MAP_NAME_ in config_map_name:
            # get the KubernetesResource
            config_map: KubernetesResource = \
                config_map_details[ViyaDeploymentReportKeys.ResourceDetails.RESOURCE_DEFINITION]

            # get the ConfigMap data
            cadence_data: Optional[Dict] = config_map.get_data()

            try:
                # build the cadence string
                return (
                    f"{cadence_data[_CADENCE_DISPLAY_NAME_KEY_]} "
                    f"{cadence_data[_CADENCE_VERSION_KEY_]} "
                    f"({cadence_data[_CADENCE_RELEASE_KEY_]})"
                )
            except KeyError:
                # if an expected key wasn't defined, continue
                continue

    # expected value wasn't found
    return None


def get_db_info(config_maps: Dict) -> Dict:
    """
    Returns the db information of the targeted SAS deployment.

    :param config_maps: The ConfigMap resources to evaluate.

    :return: A dict representing the db information of the targeted SAS deployment, or None if the given
             ConfigMap does not contain the requested information.
    """
    # look for the necessary ConfigMap
    for config_map_name, config_map_details in config_maps.items():
        if _SAS_POSTGRES_CONFIG_CONFIG_MAP_NAME_ in config_map_name:
            # get the KubernetesResource
            config_map: KubernetesResource = \
                config_map_details[ViyaDeploymentReportKeys.ResourceDetails.RESOURCE_DEFINITION]

            # get the ConfigMap data
            db_data: Optional[Dict] = config_map.get_data()

            try:
                # check whether the db configuration is external
                if db_data[_EXTERNAL_DATABASE_KEY_] == "false":
                    # return internal config information (all other details will be defined in the component in report)
                    return {_TYPE_KEY_: _INTERNAL_DB_}

                # if external, create the dict of all relevant info
                return {
                    _TYPE_KEY_: _EXTERNAL_DB_,
                    _HOST_KEY_: db_data[_DATABASE_HOST_KEY_],
                    _PORT_KEY_: db_data[_DATABASE_PORT_KEY_],
                    _NAME_KEY_: db_data[_DATABASE_NAME_KEY_],
                    _USER_KEY_: db_data[_DATASOURCE_USERNAME_KEY_]
                }
            except KeyError:
                # if an expected key wasn't defined, continue
                continue

    # expected value not found
    return dict()
