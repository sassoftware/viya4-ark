####################################################################
# ### config_util.py                                             ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2022, SAS Institute Inc., Cary, NC, USA.         ###
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

# database info values
_EXTERNAL_DB_ = "External"
_INTERNAL_DB_ = "Internal"
_UNSUPPORTED_DB_ = "Unsupported"
_CRUNCH_DB_ = "crunch"
_CRUNCHDATA_DB_ = "sas-crunchy-data-"
_CRUNCH5DATA_DB_ = "sas-crunchy-platform-"
_ALT_DB_ = "sas.database.alternative.databaseServerName"
_UNAVAIL_DB_ = "not available"

# database name key values
_DBNAME_POSTGRES_ = "postgres"
_DBNAME_CONFIG_POSTGRES_ = "sas-postgres-config"
_DBNAME_CPSPOSTGRES_ = "cpspostgres"
_DBNAME_CONFIG_CPSPOSTGRES_ = "sas-planning-cpspostgres-config"


def get_cadence_version(resource_cache: Dict) -> Optional[Text]:
    """
    Returns the cadence version of the targeted SAS deployment.

    :param resource_cache: The dictionary of resources gathered from the k8s deployment.

    :return: A string representing the cadence version of the targeted SAS deployment, or None if the given
             ConfigMap does not contain the requested information.
    """
    # look for the necessary ConfigMap

    try:
        if not resource_cache:
            return None

        config_maps: Dict = resource_cache[ResourceTypeValues.K8S_CORE_CONFIG_MAPS][ITEMS_KEY]

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


def get_db_info(resource_cache: Dict) -> Dict:
    """
    Returns the db information of the targeted SAS deployment.

    :param resource_cache: The dictionary of resources gathered from the k8s deployment.

    :return: A dict representing the db information of the targeted SAS deployment, or None if
             no resource information was cached.
    """

    db_dict: Dict = dict()

    if not resource_cache:
        return None

    if ResourceTypeValues.SAS_CRUNCHYCLUSTERS in resource_cache.keys():
        pgclusters: Dict = resource_cache[ResourceTypeValues.SAS_CRUNCHYCLUSTERS][ITEMS_KEY]
        db_dict = _get_db_info_v3(pgclusters)

    if ResourceTypeValues.SAS_PGCLUSTERS in resource_cache.keys():
        pgclusters: Dict = resource_cache[ResourceTypeValues.SAS_PGCLUSTERS][ITEMS_KEY]
        db_dict = _get_db_info_v2(pgclusters)

    if not db_dict:
        try:
            config_maps: Dict = resource_cache[ResourceTypeValues.K8S_CORE_CONFIG_MAPS][ITEMS_KEY]
            db_dict = _get_db_info_v1(config_maps=config_maps)

        except KeyError:
            db_dict[_UNSUPPORTED_DB_] = {Keys.DatabaseDetails.DBTYPE: _UNSUPPORTED_DB_}

    return db_dict


def _get_db_info_v1(config_maps: Dict) -> Dict:
    """
    Returns the db information of the targeted SAS deployment.

    :param config_maps: The ConfigMap resources to evaluate. This is before data server operator change.

    :return: A dictionary representing the db information of the targeted SAS deployment,
             or None if the given ConfigMap does not contain the requested information.
    """
    # initialize the return value
    db_dict: Dict = dict()

    for config_map_name, config_map_details in config_maps.items():
        dbs: Dict = dict()

        # look for the necessary ConfigMap
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
                        dbs = {Keys.DatabaseDetails.DBTYPE: _INTERNAL_DB_}
                    else:
                        # if external, create the dict of all relevant info
                        dbs = {
                            Keys.DatabaseDetails.DBTYPE: _EXTERNAL_DB_,
                            Keys.DatabaseDetails.DBHOST: db_data[_DATABASE_HOST_KEY_],
                            Keys.DatabaseDetails.DBPORT: db_data[_DATABASE_PORT_KEY_],
                            Keys.DatabaseDetails.DBNAME: db_data[_DATABASE_NAME_KEY_],
                            Keys.DatabaseDetails.DBSSL: db_data[_DATABASE_SSL_ENABLED_KEY_]
                        }
                except KeyError:
                    try:
                        if _CRUNCH_DB_ in db_data[_ALT_DB_]:
                            dbs = {Keys.DatabaseDetails.DBTYPE: _INTERNAL_DB_}
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


def _get_db_info_v3(pgclusters: Dict) -> Dict:
    """
    Returns the db information of the targeted SAS deployment.

    :param pgclusters: The pgclusters resource to evaluate.
    :return: A dictionary representing the db information of the targeted SAS deployment.
    """
    # initialize the return value
    db_dict: Dict = dict()
    for key in pgclusters:
        try:
            resource_definition = pgclusters[key][Keys.ResourceDetails.RESOURCE_DEFINITION]

            db_name: Optional[Text] = resource_definition.get_name()
            db_data: Optional[Dict] = resource_definition.get_spec()

            if not db_data:
                continue

            dbs: Dict = dict()

            try:
                if (db_data['port']):
                    dbs = {Keys.DatabaseDetails.DBTYPE: _INTERNAL_DB_}
                else:
                    dbs = {
                        Keys.DatabaseDetails.DBTYPE: _EXTERNAL_DB_,
                        Keys.DatabaseDetails.DBCONN: _UNAVAIL_DB_
                    }
            except KeyError:
                continue

            if dbs:
                # convert db_name to be aligned
                if _CRUNCH5DATA_DB_ in db_name:
                    db_name = db_name.replace(_CRUNCH5DATA_DB_, "")

                db_dict[db_name] = dbs

        except KeyError:
            continue

    return db_dict


def _get_db_info_v2(pgclusters: Dict) -> Dict:
    """
    Returns the db information of the targeted SAS deployment.

    :param pgclusters: The pgclusters resource to evaluate.
    :return: A dictionary representing the db information of the targeted SAS deployment.
    """
    # initialize the return value
    db_dict: Dict = dict()

    for key in pgclusters:
        try:
            resource_definition = pgclusters[key][Keys.ResourceDetails.RESOURCE_DEFINITION]

            db_name: Optional[Text] = resource_definition.get_name()
            db_data: Optional[Dict] = resource_definition.get_spec()

            dbs: Dict = dict()

            if not db_data:
                continue

            try:
                if bool(db_data['internal']):
                    dbs = {Keys.DatabaseDetails.DBTYPE: _INTERNAL_DB_}
                else:
                    try:
                        dbs = {
                            Keys.DatabaseDetails.DBTYPE: _EXTERNAL_DB_,
                            Keys.DatabaseDetails.DBHOST: db_data[_PGCLUSTER_CONNECT_KEY_][_PGCLUSTER_HOST_KEY_],
                            Keys.DatabaseDetails.DBPORT: db_data[_PGCLUSTER_CONNECT_KEY_][_PGCLUSTER_PORT_KEY_],
                            Keys.DatabaseDetails.DBNAME: db_data[_PGCLUSTER_NAME_KEY_],
                            Keys.DatabaseDetails.DBSSL: db_data[_PGCLUSTER_CONNECT_KEY_][_PGCLUSTER_SSL_KEY_]
                        }
                    except KeyError:
                        dbs = {
                            Keys.DatabaseDetails.DBTYPE: _EXTERNAL_DB_,
                            Keys.DatabaseDetails.DBCONN: _UNAVAIL_DB_
                        }
            except KeyError:
                continue

            if dbs:
                # convert db_name to be aligned
                if _CRUNCHDATA_DB_ in db_name:
                    db_name = db_name.replace(_CRUNCHDATA_DB_, "")

                db_dict[db_name] = dbs
        except KeyError:
            continue

    return db_dict


def get_configmaps_info(resource_cache: Dict) -> Optional[Dict]:
    """
    Returns the configmaps of the targeted SAS deployment.

    :param resource_cache: The dictionary of resources gathered from the k8s deployment.

    :return: A dictionary representing the configmaps information of the targeted SAS deployment.
    """
    configmaps_dict: Dict = dict()
    try:
        if not resource_cache:
            return configmaps_dict

        configmaps: Dict = resource_cache[ResourceTypeValues.K8S_CORE_CONFIG_MAPS][ITEMS_KEY]

        for configmap_name, configmap_details in configmaps.items():

            configmap: KubernetesResource = configmap_details[Keys.ResourceDetails.RESOURCE_DEFINITION]
            # get the ConfigMap data
            data: Optional[Dict] = configmap.get_data()

            if data:
                configmaps_dict[configmap_name] = data

        return configmaps_dict

    except KeyError:
        return configmaps_dict


def get_secrets_info(resource_cache: Dict, secretsnames_dict: Dict) -> Optional[Dict]:
    """
    Returns the secrets of the targeted SAS deployment.

    :param resource_cache: The dictionary of resources gathered from the k8s deployment.
    :param secretsnames_dict: The dictionary to store the secrets

    :return: A dictionary representing the secrets by kind of the targeted SAS deployment.
    """
    secrets_dict: Dict = dict()
    try:
        if not resource_cache:
            return secrets_dict

        secrets: Dict = resource_cache[ResourceTypeValues.K8S_CORE_SECRETS][ITEMS_KEY]

        for name, details in secrets.items():
            secret: KubernetesResource = details[Keys.ResourceDetails.RESOURCE_DEFINITION]
            data: Optional[Dict] = secret.get_data()

            if data:
                type: Optional[Text] = secret.get_type()

                if type in secrets_dict.keys():
                    if name not in secrets_dict[type].keys():
                        secrets_dict[type][name] = {"name": list(data.keys())}
                else:
                    secrets_dict[type]: Dict = dict()
                    secrets_dict[type][name]: Dict = dict()
                    secrets_dict[type][name] = {"name": list(data.keys())}

                secretsnames_dict[name] = type

        return secrets_dict

    except KeyError:
        return secrets_dict
