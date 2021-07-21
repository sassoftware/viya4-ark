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

from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource


def get_cadence_version(config_map: KubernetesResource) -> Optional[Text]:
    """
    Returns the cadence version of the targeted SAS deployment.

    :param config_map: The ConfigMap resource to evaluate.
    :return: A string representing the cadence version of the targeted SAS deployment.
    """
    # initialize the return value
    cadence_info: Optional[Text] = None

    try:
        # look for ConfigMap with expected name
        if 'sas-deployment-metadata' in config_map.get_name():
            # get the ConfigMap data
            cadence_data: Optional[Dict] = config_map.get_data()

            # build the cadence string
            cadence_info = (
                f"{cadence_data['SAS_CADENCE_DISPLAY_NAME']} "
                f"{cadence_data['SAS_CADENCE_VERSION']} "
                f"({cadence_data['SAS_CADENCE_RELEASE']})"
            )

        return cadence_info
    except KeyError:
        # if an expected key wasn't defined, return None
        return None


def get_db_info(config_map: KubernetesResource) -> Optional[Dict]:
    """
    Returns the db information of the targeted SAS deployment.

    :param config_map: The ConfigMap resource to evaluate.
    :return: A dict representing the db information of the targeted SAS deployment.
    """
    # initialize the return value
    db_dict: Optional[Dict] = dict()

    try:
        # make sure the ConfigMap has the expected name
        if 'sas-postgres-config' in config_map.get_name():
            # get the ConfigMap data
            db_data: Optional[Dict] = config_map.get_data()

            # check whether the db configuration is external
            if db_data['EXTERNAL_DATABASE'] == "false":
                # return internal config information (all other details will be defined in the component in report)
                return {"Type": "Internal"}

            # if external, create the dict of all relevant info
            db_dict = {
                "Type": "External",
                "Host": db_data['DATABASE_HOST'],
                "Port": db_data['DATABASE_PORT'],
                "Name": db_data['DATABASE_NAME'],
                "User": db_data['SPRING_DATASOURCE_USERNAME']
            }

        return db_dict
    except KeyError:
        # if an expected key wasn't defined, return None
        return None
