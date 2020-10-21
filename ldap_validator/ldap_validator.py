#!/usr/bin/env python3
####################################################################
# ### pre_install_report.py                                  ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

from datetime import datetime
from ldap3 import Server, Connection, SIMPLE, SYNC, ASYNC, SUBTREE, ALL, ALL_ATTRIBUTES
import os
import sys
import inspect
import getopt
import yaml
import traceback
import json
try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

# Control vars
sitedefault_variables = None

# retrieve at most sizelimit entries for a search.  A sizelimit of 0 (zero) or
# none means no limit.  A sizelimit of  max  means  the maximum integer allowable
# by the protocol.  A server may impose a maximal sizelimit which only the root
# user may override.
sizeLimit = 5

# Set up logging
logFile = "ldap_validation_" + str(datetime.now()) + ".log"
open(logFile, 'a').close()

# sitedefault variables
ldap_server_host = ""
ldap_server_port = ""
ldap_protocol = ""
ldap_anon_bind = ""
ldap_bind_userdn = ""
ldap_bind_pw = ""
ldap_user_basedn = ""
ldap_group_basedn = ""
ldap_defaultadmin_user = ""
ldap_url = ""


# --------------------------------------------------------------------------------------------------
def logMessage(message, error_flag=False):
    """
    Adds a message to the log; flag to mark message as error.

    Argument:
        message(str) - message to be added to the log
        error_flag(bool) - flag to mark the message as an ERROR in the log
    Returns:
        None
    """

    dateTimeObj = datetime.now()

    logger = open(logFile, "a")

    if (error_flag):
        message = "[ ERROR ] " + str(message)

    message = str(dateTimeObj) + " - " + str(message)

    # display the message to the terminal and write to the log
    print(message)
    logger.write(message)
    logger.write("\n")

    logger.close()

    return None


# --------------------------------------------------------------------------------------------------
def importConfigYAML(yaml_file):
    """
    Load config yaml file into dict structure.

    Argument:
        yaml_file(str) - full path/filename of yaml
    Returns:
        yaml_content(dict) - containing contents of yaml file
    Raises:
        dict - object containing all content from supplied yaml in dict format
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    if not os.path.exists(yaml_file):
        logMessage("Invalid config yaml specified: " + str(yaml_file))
        sys.exit(1)
        return "failed"

    try:
        logMessage("Importing sitedefault: " + yaml_file)

        # Read the yaml file
        with open(yaml_file, 'r') as yfile:
            yaml_content = yaml.load(yfile, Loader=Loader)
        yfile.close()

        logMessage("Successfully loaded yaml file '" + str(yaml_file) + "'")

        # define simpler variables
        global ldap_server_host
        global ldap_server_port
        global ldap_protocol
        global ldap_anon_bind
        global ldap_bind_userdn
        global ldap_bind_pw
        global ldap_user_basedn
        global ldap_group_basedn
        global ldap_defaultadmin_user
        global ldap_url

        ldap_url = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['url']
        ldap_server_host = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['host']
        ldap_server_port = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['port']
        ldap_anon_bind = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['anonymousBind']
        ldap_bind_pw = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['password']
        ldap_bind_userdn = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['userDN']
        ldap_user_basedn = yaml_content['config']['application']['sas.identities.providers.ldap.user']['baseDN']
        ldap_group_basedn = yaml_content['config']['application']['sas.identities.providers.ldap.group']['baseDN']
        ldap_defaultadmin_user = yaml_content['config']['application']['sas.identities']['administrator']
        ldap_protocol = ldap_url.split(':')[0]
        ldap_anon_bind = (ldap_anon_bind).lower()
        if (ldap_anon_bind ==  'false'): ldap_anon_bind = False
        if (ldap_anon_bind ==  'true'): ldap_anon_bind = True

        logMessage("LDAP URL:                       " + ldap_url)
        logMessage("LDAP Protocol:                  " + ldap_protocol)
        logMessage("LDAP ServerHost:                " + ldap_server_host)
        logMessage("LDAP Server Port:               " + str(ldap_server_port))
        logMessage("LDAP Anonymous Bind:            " + str(ldap_anon_bind))
        if (ldap_bind_pw is not None):
            logMessage("LDAP Anonymous Bind Password:   SET")
        else:
            logMessage("LDAP Anonymous Bind Password:   UNSET")
        logMessage("LDAP Anonymous Bind User DN:    " + ldap_bind_userdn)
        logMessage("LDAP User DN:                   " + ldap_user_basedn)
        logMessage("LDAP Group DN:                  " + ldap_group_basedn)
        logMessage("LDAP Default Admin User:        " + ldap_defaultadmin_user)

        assert(ldap_url is not None), "Error: LDAP Administrator is undefined."
        assert(ldap_server_host is not None), "Error: LDAP Host is undefined."
        assert(ldap_server_port > 0), "Error: LDAP port is in correctly defined."
        assert(ldap_anon_bind is not None), "Error: LDAP anonymousBind is undefined."
        assert(ldap_bind_pw is not None), "Error: LDAP password is undefined."
        assert(ldap_bind_userdn is not None), "Error: LDAP bind userDN is undefined."
        assert(ldap_user_basedn is not None), "Error: LDAP User BaseDN is undefined."
        assert(ldap_group_basedn is not None), "Error: LDAP Group BaseDN is undefined."
        assert(ldap_defaultadmin_user is not None), "Error: LDAP Administrator is undefined."

        logMessage("Sitedefault contains required values.")

    except (IOError, ValueError):
        # Log error and raise exception if yaml can't be read.
        error_msg = '{1}\nError loading yaml file {0}\n'.format(yaml_file, traceback.format_exc())
        logMessage(error_msg)
        raise ValueError(error_msg)

    return yaml_content


# --------------------------------------------------------------------------------------------------
def runTestSchedule():
    """
    Run the list of scheduled LDAP Validation tests.

    Argument:
        None
    Returns:
        success flag(bool) - Success/Failure of test schedule
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    pingHost()

    performLDAPQuery(ldap_group_basedn, '(objectclass=*)')

    performLDAPQuery(ldap_user_basedn, '(objectclass=*)')

    performLDAPQuery(ldap_user_basedn, '(&(objectClass=*)(sAMAccountName={{' + ldap_defaultadmin_user + '}}))')

    return True


# --------------------------------------------------------------------------------------------------
def pingHost():
    """
    Ping the LDAP server on the specified connection.

    Argument:
        None
    Returns:
        success flag(bool) - Success/Failure of ping
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    logMessage("Attempting to ping LDAP server host at " + ldap_server_host)

    response = os.system("ping -c 1 " + ldap_server_host)

    if (int(response) == 0):
        logMessage("Network Active")
        return True
    else:
        logMessage("Network Error")

    return False


# --------------------------------------------------------------------------------------------------
def performLDAPQuery(searchBase, searchFilter):
    """
    Execute a query on the defined LDAP server.

    Argument:
        queryString(string) - LDAP query to be executed
    Returns:
        success flag(bool) - Success/Failure of query
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    server = Server(ldap_protocol + "://" + ldap_server_host)

    logMessage("Attempting to create connection binding.")
    connection = Connection(server, ldap_bind_userdn, ldap_bind_pw, auto_bind=True)
    logMessage("Bind results: " + str(connection))

    logMessage("\n------------------------------------------\nQuery: search_base=" + searchBase + ", search_filter=" + searchFilter)

    # perform search
    connection.search(search_base=searchBase, search_filter=searchFilter, size_limit=sizeLimit)

    # parse results
    for entry in connection.entries:
        logMessage("\n" + str(entry))

    response = json.loads(connection.response_to_json())
    logMessage("\n------------------------------------------\nResponse:\n\n" + str(response))
    result = connection.result
    logMessage("\n------------------------------------------\nResult:\n\n" + str(result))

    logMessage("\n\n------------------------------------------\n------------------------------------------\n")

    connection.unbind()

    return True

# --------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
##################
#     main()     #
##################
def main(argv):

    """
    Main execution point for the ldap_validator script

    Argument:
        arguments(string) - The parameters passed to the script at execution.
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    # Parse command line options/arguments
    try:
        opts, args = getopt.getopt(argv, "y:Y",
                                   ["sitedefault=", "sitedefault="])
    except getopt.GetoptError as opt_error:
        logMessage(opt_error)

    sitedefault_loc = ""

    for opt, arg in opts:
        logMessage("Processing command line option <" + opt + " " + arg + ">")
        if opt in ('-y', '--sitedefault'):
            logMessage("Setting sitedefault to: " + arg)
            sitedefault_loc = arg
        elif opt in ('-Y', '--sitedefault'):
            logMessage("Setting sitedefault to: " + arg)
            sitedefault_loc = arg
        else:
            logMessage("Unrecognized command line option <" + opt + " " + arg + ">")

    # Load site default and define variables
    sitedefault_variables = importConfigYAML(sitedefault_loc)

    # Execute test suite
    runTestSchedule()


# --------------------------------------------------------------------------------------------------
##################
#     main()     #
##################
if __name__ == '__main__':
    main(sys.argv[1:])

# ----------------------------------------------------------------------------
