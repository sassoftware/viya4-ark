
####################################################################
# ### test_ldap_validator.py                                     ###
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

from ldap_validator.ldap_validator import pingHost, parse_connection_results, importSiteDefault, performLDAPQuery
from ldap_validator.ldap_validator import failTestSuite
from viya_ark_library.logging import ViyaARKLogger
from ldap_validator.library.utils import ldap_messages

sas_logger = ViyaARKLogger("test_report.log", logging_level=logging.INFO, logger_name="test_logger")
ldap_logger = sas_logger.get_logger()
# setup sys.path for import of viya_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)))
#
# setup sys.path for import of ldap_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)))


def test_pinghost():
    result = pingHost()
    assert(result is False)


def test_failTestSuite():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        failTestSuite()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == ldap_messages.BAD_SITEYAML_RC_


def test_parse_connection_results_true():
    #  This test should pass with valid connection results

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


def test_parse_connection_results_empty_response():
    #  This test should fail with empty response json set to {}

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
    response = {}
    verify = True
    parse_result: bool = parse_connection_results(ldap_logger, response, result, entries, verify)
    ldap_logger.info(" Parse result is " + str(parse_result))
    assert (parse_result is False)

def test_parse_connection_results_false():
    # The test should fail since the rc in "result" is set to 999
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
    # This should fail since the entries list is empty
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


def test_importSiteDefault_bad_file_loc():
    # This test should fail since the testsitedefault_invalid.yml file is nonexistent
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sitedefault_loc = os.path.join(current_dir,
                                   "test_data" + os.sep + "yaml_data" + os.sep + "testsitedefault_invalid.yml")
    ldap_logger.info(" sitedefault file = " + str(sitedefault_loc))
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        importSiteDefault(sitedefault_loc, ldap_logger)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == ldap_messages.BAD_SITEYAML_RC_
    ldap_logger.info("pytest code" + str(pytest_wrapped_e.value.code))


def test_importSiteDefault_keyerror():
    #  This test should fail since testsitedefault_keyerror contains invalid key anonymoussBind
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sitedefault_loc = os.path.join(current_dir, "test_data" + os.sep + "yaml_data" +
                                   os.sep + "testsitedefault_keyerror.yml")
    ldap_logger.info(" sitedefault file = " + str(sitedefault_loc))
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        importSiteDefault(sitedefault_loc, ldap_logger)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == ldap_messages.BAD_SITEYAML_RC_
    ldap_logger.info("pytest code" + str(pytest_wrapped_e.value.code))


def test_importSiteDefault_asserterror():
    #  This test should fail since testsitedefault_assertion is missing the URL information
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sitedefault_loc = os.path.join(current_dir, "test_data" + os.sep
                                   + "yaml_data" + os.sep + "testsitedefault_assertion.yml")
    ldap_logger.info(" sitedefault file = " + str(sitedefault_loc))
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        importSiteDefault(sitedefault_loc, ldap_logger)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == ldap_messages.BAD_SITEYAML_RC_
    ldap_logger.info("pytest code" + str(pytest_wrapped_e.value.code))


def test_importSiteDefault_valid():
    # This test should fail since file testsitedefault_invalidServer contains an bad server
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sitedefault_loc = os.path.join(current_dir, "test_data" + os.sep + "yaml_data"
                                   + os.sep + "testsitedefault_invalidServer.yml")
    ldap_logger.info(" sitedefault file = " + str(sitedefault_loc))
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        importSiteDefault(sitedefault_loc, ldap_logger)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == ldap_messages.BAD_SITEYAML_RC_
    ldap_logger.info("pytest code" + str(pytest_wrapped_e.value.code))


def test_performLDAPQuery_invalid():
    searchBase = "OU = Cats, DC = a, DC = MYCOM, DC = com"
    searchFilter = "(objectclass= *)"
    server = "myserver.mycompany.com"

    parse_result = performLDAPQuery(ldap_logger, server, searchBase, searchFilter, False)
    assert(parse_result is False)
