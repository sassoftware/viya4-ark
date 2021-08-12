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
import pytest

from typing import Dict, Optional, Text

from deployment_report.model.static.viya_deployment_report_keys import ITEMS_KEY
from deployment_report.model.utils import config_util
from deployment_report.model.utils.test import conftest

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues
from viya_ark_library.k8s.test_impl.sas_kubectl_test import KubectlTest


####################################################################
# Unit Tests                                                     ###
####################################################################
@pytest.mark.usefixtures(conftest.NO_INGRESS_SIMULATION_FIXTURE)
def test_get_cadence_version(no_ingress_simulation_fixture: conftest.DSA):
    """
    This test verifies that the provided cadence data is returned when values is passed to get_cadence_version().
    """
    # get the resource cache
    resource_cache: Dict = no_ingress_simulation_fixture.resource_cache()

    # get the ConfigMaps
    config_maps: Dict = resource_cache[ResourceTypeValues.K8S_CORE_CONFIG_MAPS][ITEMS_KEY]

    # test the util method
    assert config_util.get_cadence_version(config_maps=config_maps) == KubectlTest.Values.CADENCEINFO


@pytest.mark.usefixtures(conftest.NO_INGRESS_SIMULATION_FIXTURE)
def test_get_db_info(no_ingress_simulation_fixture: conftest.DSA):
    """
    This test verifies that the provided db data is returned when values is passed to get_db_info().
    """
    # get the resource cache
    resource_cache: Dict = no_ingress_simulation_fixture.resource_cache()

    # get the ConfigMaps
    config_maps: Dict = resource_cache[ResourceTypeValues.K8S_CORE_CONFIG_MAPS][ITEMS_KEY]

    # test the util method
    assert config_util.get_db_info(config_maps=config_maps)["type"] == KubectlTest.Values.DBINFO
