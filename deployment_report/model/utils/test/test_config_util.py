####################################################################
# ### test_config_util.py                                        ###
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

from deployment_report.model.utils import config_util

from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest


####################################################################
# Unit Tests                                                     ###
####################################################################
def test_get_cadence_version() -> None:
    """
    This test verifies that the provided cadence data is returned when values is passed to get_cadence_version().
    """
    # check for expected attributes
    kubectl: KubectlTest = KubectlTest()

    cadence_data = kubectl.get_resources("ConfigMaps")
    cadence_info: Optional[Text] = None

    for c in cadence_data:
        cadence_info = config_util.get_cadence_version(c)
        if cadence_info:
            break

    assert cadence_info == KubectlTest.Values.CADENCEINFO


def test_get_db_info() -> None:
    """
    This test verifies that the provided db data is returned when values is passed to get_db_info().
    """
    # check for expected attributes
    # check for expected attributes
    kubectl: KubectlTest = KubectlTest()

    db_data = kubectl.get_resources("ConfigMaps")
    db_dict: Dict = dict()

    for c in db_data:
        db_dict = config_util.get_db_info(c)
        if db_dict:
            break

    assert db_dict["Type"] == KubectlTest.Values.DBINFO
