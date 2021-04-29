
####################################################################
# ### test_ldap_validator.py                                 ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import os
import sys

import logging
import pytest

from ldap_validator.ldap_validator import ping_host, parse_connection_results, import_site_default, perform_ldap_query
from ldap_validator.ldap_validator import failTestSuite
from viya_ark_library.logging import ViyaARKLogger

sas_logger = ViyaARKLogger("test_report.log", logging_level=logging.INFO, logger_name="test_logger")
ldap_logger = sas_logger.get_logger()
# setup sys.path for import of viya_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)))
#
# setup sys.path for import of ldap_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)))


def test_pinghost():
    result = ping_host(ldap_logger)
    assert(result is False)


def test_failTestSuite():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        failTestSuite(ldap_logger)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 3


def test_parse_connection_results_true():
    result = {'description': 'sizeLimitExceeded', 'dn': '', 'message': '', 'referrals': None,
              'result': 4, 'type': 'searchResDone'}
    entries = [{'attributes': {},
                'dn': 'DC=SAS,DC=com'},
               {'attributes': {},
                'dn': 'OU=Microsoft Exchange Security Groups,DC=SAS,DC=com'},
               {'attributes': {},
                'dn': 'CN=Exchange Servers,OU=Microsoft Exchange Security Groups,DC=SAS,DC=com'},
               {'attributes': {},
                'dn': 'CN=Exchange Organization Administrators,OU=Microsoft Exchange Security Groups,DC=SAS,DC=com'},
               {'attributes': {},
                'dn': 'CN=Exchange Recipient Administrators,OU=Microsoft Exchange Security Groups,DC=SAS,DC=com'}]
    response = \
        {"entries": [{"attributes": {}, "dn": "OU=Groups,DC=na,DC=SAS,DC=com"},
                     {"attributes": {}, "dn": "CN=[PTD] XML Case Study Team,OU=Groups,DC=na,DC=SAS,DC=com"},
                     {"attributes": {}, "dn": "CN=PMM PAM Team,OU=Groups,DC=na,DC=SAS,DC=com"},
                     {"attributes": {}, "dn": "CN=CCG Cumulus Digital Asset Management System,OU=Groups,DC=na,"
                                              "DC=SAS,DC=com"},
                     {"attributes": {}, "dn": "CN=VSTI ONDEMAND,OU=Groups,DC=na,DC=SAS,DC=com"}]}
    verify = True
    parse_result: bool = parse_connection_results(ldap_logger, response, result, entries, verify)
    ldap_logger.info(" Parse result is " + str(parse_result))
    assert(parse_result is True)


def test_parse_connection_results_false():
    result = {'description': 'sizeLimitExceeded', 'dn': '', 'message': '', 'referrals': None,
              'result': 999, 'type': 'searchResDone'}
    entries = [{'attributes': {}, 'dn': 'DC=SAS,DC=com'},
               {'attributes': {}, 'dn': 'OU=Microsoft Exchange Security Groups,DC=SAS,DC=com'},
               {'attributes': {}, 'dn': 'CN=Exchange Servers,OU=Microsoft Exchange Security Groups,DC=SAS,DC=com'},
               {'attributes': {}, 'dn': 'CN=Exchange Organization Administrators,OU=Microsoft Exchange Security Groups,'
                                        'DC=SAS,DC=com'},
               {'attributes': {}, 'dn': 'CN=Exchange Recipient Administrators,OU=Microsoft Exchange Security Groups,'
                                        'DC=SAS,DC=com'}]
    response = {"entries": [{"attributes": {}, "dn": "OU=Groups,DC=na,DC=SAS,DC=com"},
                            {"attributes": {}, "dn": "CN=[PTD] XML Case Study Team,OU=Groups,DC=na,DC=SAS,DC=com"},
                            {"attributes": {}, "dn": "CN=PMM PAM Team,OU=Groups,DC=na,DC=SAS,DC=com"},
                            {"attributes": {}, "dn": "CN=CCG Cumulus Digital Asset Management System,OU=Groups,"
                                                     "DC=na,DC=SAS,DC=com"},
                            {"attributes": {}, "dn": "CN=VSTI ONDEMAND,OU=Groups,DC=na,DC=SAS,DC=com"}]}
    verify = True
    parse_result: bool = parse_connection_results(ldap_logger, response, result, entries, verify)
    ldap_logger.info(" Parse result is " + str(parse_result))
    assert(parse_result is False)


def test_parse_connection_results_empty():
    result = {'description': 'sizeLimitExceeded', 'dn': '', 'message': '', 'referrals': None,
              'result': 4, 'type': 'searchResDone'}
    entries = []
    response = \
        {"entries": [
                {"attributes": {}, "dn": "OU=Groups,DC=na,DC=SAS,DC=com"},
                {"attributes": {}, "dn": "CN=[PTD] XML Case Study Team,OU=Groups,DC=na,DC=SAS,DC=com"},
                {"attributes": {}, "dn": "CN=PMM PAM Team,OU=Groups,DC=na,DC=SAS,DC=com"},
                {"attributes": {}, "dn": "CN=CCG Cumulus Digital Asset Management System,OU=Groups,"
                                         "DC=na,DC=SAS,DC=com"},
                {"attributes": {}, "dn": "CN=VSTI ONDEMAND,OU=Groups,DC=na,DC=SAS,DC=com"}]}
    verify = True
    parse_result: bool = parse_connection_results(ldap_logger, response, result, entries, verify)
    ldap_logger.info(" Parse result is " + str(parse_result))
    assert(parse_result is False)


def test_import_site_default_bad_file_loc():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sitedefault_loc = os.path.join(current_dir,
                                   "test_data" + os.sep + "yaml_data" + os.sep + "testsitedefault_invalid.yml")
    ldap_logger.info(" sitedefault file = " + str(sitedefault_loc))
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        import_site_default(sitedefault_loc, ldap_logger, sas_logger)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 3
    ldap_logger.info("pytest code" + str(pytest_wrapped_e.value.code))


def test_import_site_default_keyerror():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sitedefault_loc = os.path.join(current_dir, "test_data" + os.sep + "yaml_data" +
                                   os.sep + "testsitedefault_keyerror.yml")
    ldap_logger.info(" sitedefault file = " + str(sitedefault_loc))
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        import_site_default(sitedefault_loc, ldap_logger, sas_logger)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 3
    ldap_logger.info("pytest code" + str(pytest_wrapped_e.value.code))


def test_import_site_default_asserterror():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sitedefault_loc = os.path.join(current_dir, "test_data" + os.sep
                                   + "yaml_data" + os.sep + "testsitedefault_assertion.yml")
    ldap_logger.info(" sitedefault file = " + str(sitedefault_loc))
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        import_site_default(sitedefault_loc, ldap_logger, sas_logger)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 3
    ldap_logger.info("pytest code" + str(pytest_wrapped_e.value.code))


def test_import_site_default_valid():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sitedefault_loc = os.path.join(current_dir, "test_data" + os.sep + "yaml_data"
                                   + os.sep + "testsitedefault_invalidServer.yml")
    ldap_logger.info(" sitedefault file = " + str(sitedefault_loc))
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        import_site_default(sitedefault_loc, ldap_logger, sas_logger)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 3
    ldap_logger.info("pytest code" + str(pytest_wrapped_e.value.code))


def test_perform_ldat_query_invalid():
    searchBase = "OU = Groups, DC = na, DC = SAS, DC = com"
    searchFilter = "(objectclass= *)"
    server = "myldapserver.mycompany.com"

    parse_result = perform_ldap_query(ldap_logger, server, searchBase, searchFilter, False)
    assert(parse_result is False)
