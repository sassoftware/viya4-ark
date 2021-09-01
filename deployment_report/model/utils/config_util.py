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

from deployment_report.model.static.viya_deployment_report_keys import ITEMS_KEY, ViyaDeploymentReportKeys as Keys

from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues

# ConfigMap name containing SAS deployment metadata values
_SAS_DEPLOYMENT_METADATA_CONFIG_MAP_NAME_ = "sas-deployment-metadata"
# ConfigMap name containing SAS postgres config values
_SAS_POSTGRES_CONFIG_CONFIG_MAP_NAME_ = "postgres-config"

# SAS deployment metadata keys
_CADENCE_DISPLAY_NAME_KEY_ = "SAS_CADENCE_DISPLAY_NAME"
_CADENCE_RELEASE_KEY_ = "SAS_CADENCE_RELEASE"
_CADENCE_VERSION_KEY_ = "SAS_CADENCE_VERSION"

# SAS postgres config keys
_DATABASE_HOST_KEY_ = "DATABASE_HOST"
_DATABASE_NAME_KEY_ = "DATABASE_NAME"
_DATABASE_PORT_KEY_ = "DATABASE_PORT"
_DATABASE_SSL_ENABLED_KEY_ = "DATABASE_SSL_ENABLED"
_EXTERNAL_DATABASE_KEY_ = "EXTERNAL_DATABASE"
_DATASOURCE_USERNAME_KEY_ = "SPRING_DATASOURCE_USERNAME"

# SAS postgres pgcluster keys
_PGCLUSTER_HOST_KEY_ = "host"
_PGCLUSTER_PORT_KEY_ = "port"
_PGCLUSTER_NAME_KEY_ = "database"
_PGCLUSTER_SSL_KEY_ = "ssl"
_PGCLUSTER_CONNECT_KEY_ = "connection"

# database info keys
_HOST_KEY_ = "Host"
_NAME_KEY_ = "Name"
_PORT_KEY_ = "Port"
_TYPE_KEY_ = "Type"
_SSLENABLED_KEY_ = "SSL_Enabled"

# database info values
_EXTERNAL_DB_ = "External"
_INTERNAL_DB_ = "Internal"
_UNSUPPORTED_DB_ = "Unsupported"
_CRUNCH_DB_ = "crunch"
_ALT_DB_ = "sas.database.alternative.databaseServerName"
_UNAVAIL_DB_ = "not available"

# database name key values
_DBNAME_POSTGRES_ = "postgres"
_DBNAME_CONFIG_POSTGRES_ = "sas-postgres-config"
_DBNAME_CPSPOSTGRES_ = "cpspostgres"
_DBNAME_CONFIG_CPSPOSTGRES_ = "sas-planning-cpspostgres-config"


def get_cadence_version(resource: Dict) -> Optional[Text]:
    """
    Returns the cadence version of the targeted SAS deployment.

    :param config_maps: The ConfigMap resources to evaluate.

    :return: A string representing the cadence version of the targeted SAS deployment, or None if the given
             ConfigMap does not contain the requested information.
    """
    # look for the necessary ConfigMap

    try:
        if not resource:
            return None

        config_maps: Dict = resource[ResourceTypeValues.K8S_CORE_CONFIG_MAPS][ITEMS_KEY]

        for config_map_name, config_map_details in config_maps.items():
            if _SAS_DEPLOYMENT_METADATA_CONFIG_MAP_NAME_ in config_map_name:
                # get the KubernetesResource
                config_map: KubernetesResource = \
                    config_map_details[Keys.ResourceDetails.RESOURCE_DEFINITION]

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
                    return ("Version information is not defined")

        # expected value wasn't found
        return None

    except KeyError:
        return None


def get_db_info(resource: Dict) -> Dict:

    db_dict: Optional[Dict] = dict()

    if not resource:
        return None

    try:
        pgclusters: Dict = resource[ResourceTypeValues.SAS_PGCLUSTERS][ITEMS_KEY]
        db_dict = _get_db_info_v2(pgclusters)

    except KeyError:
        pass

    if not db_dict:
        try:
            config_maps: Dict = resource[ResourceTypeValues.K8S_CORE_CONFIG_MAPS][ITEMS_KEY]
            db_dict = _get_db_info_v1(config_maps=config_maps)

        except KeyError:
            db_dict[_UNSUPPORTED_DB_] = {_TYPE_KEY_: _UNSUPPORTED_DB_}

    return db_dict


def _get_db_info_v1(config_maps: Dict) -> Dict:
    """
    Returns the db information of the targeted SAS deployment.

    :param config_maps: The ConfigMap resources to evaluate. This is before data server operator change.

    :return: A dict representing the db information of the targeted SAS deployment, or None if the given
             ConfigMap does not contain the requested information.
    """
    # look for the necessary ConfigMap
    db_dict: Optional[Dict] = dict()

    for config_map_name, config_map_details in config_maps.items():
        dbs: Optional[Dict] = dict()
        if _SAS_POSTGRES_CONFIG_CONFIG_MAP_NAME_ in config_map_name:
            # get the KubernetesResource
            config_map: KubernetesResource = \
                config_map_details[Keys.ResourceDetails.RESOURCE_DEFINITION]

            # get the ConfigMap data
            db_name: Optional[Text] = config_map.get_name()
            db_data: Optional[Dict] = config_map.get_data()
            if db_data:
                try:
                    # check whether the db configuration is external
                    if db_data[_EXTERNAL_DATABASE_KEY_] == "false":
                        dbs = {_TYPE_KEY_: _INTERNAL_DB_}
                    else:
                        # if external, create the dict of all relevant info
                        dbs = {
                            _TYPE_KEY_: _EXTERNAL_DB_,
                            _HOST_KEY_: db_data[_DATABASE_HOST_KEY_],
                            _PORT_KEY_: db_data[_DATABASE_PORT_KEY_],
                            _NAME_KEY_: db_data[_DATABASE_NAME_KEY_],
                            _SSLENABLED_KEY_: db_data[_DATABASE_SSL_ENABLED_KEY_]
                        }
                except KeyError:
                    try:
                        if _CRUNCH_DB_ in db_data[_ALT_DB_]:
                            dbs = {_TYPE_KEY_: _INTERNAL_DB_}
                    except KeyError:
                        # if an expected key wasn't defined, continue
                        continue
        if dbs:
            # convert db_name to be aligned with v2
            if _DBNAME_CONFIG_POSTGRES_ in db_name:
                db_name = _DBNAME_POSTGRES_
            elif _DBNAME_CONFIG_CPSPOSTGRES_ in db_name:
                db_name = _DBNAME_CPSPOSTGRES_

            db_dict[db_name] = dbs

    return db_dict


def _get_db_info_v2(pgclusters: Dict) -> Dict:
    """
    Returns the db information of the targeted SAS deployment.

    :param pgclusters: The pgclusters resource to evaluate. (RDCHANGE-434)
    :return: A list of dictionary representing the db information of the targeted SAS deployment.
    """
    # initialize the return value
    db_dict: Optional[Dict] = dict()

    for key in pgclusters:
        try:
            resource_definition = pgclusters[key][Keys.ResourceDetails.RESOURCE_DEFINITION]

            db_name: Optional[Text] = resource_definition.get_name()
            db_data: Optional[Dict] = resource_definition.get_spec()

            dbs: Optional[Dict] = dict()

            if not db_data:
                continue

            try:
                if bool(db_data['internal']):
                    dbs = {_TYPE_KEY_: _INTERNAL_DB_}
                else:
                    try:
                        dbs = {
                            _TYPE_KEY_: _EXTERNAL_DB_,
                            _HOST_KEY_: db_data[_PGCLUSTER_CONNECT_KEY_][_PGCLUSTER_HOST_KEY_],
                            _PORT_KEY_: db_data[_PGCLUSTER_CONNECT_KEY_][_PGCLUSTER_PORT_KEY_],
                            _NAME_KEY_: db_data[_PGCLUSTER_NAME_KEY_],
                            _SSLENABLED_KEY_: db_data[_PGCLUSTER_CONNECT_KEY_][_PGCLUSTER_SSL_KEY_]
                        }
                    except KeyError:
                        dbs = {
                            _TYPE_KEY_: _EXTERNAL_DB_,
                            _PGCLUSTER_CONNECT_KEY_: _UNAVAIL_DB_
                        }
            except KeyError:
                dbs = {_TYPE_KEY_: _UNSUPPORTED_DB_}

            if dbs:
                db_dict[db_name] = dbs
        except KeyError:
            continue

    return db_dict
