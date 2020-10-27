#!/usr/bin/env python3
####################################################################
# ### ldap_validator.py                                          ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
#                                                                ###
####################################################################

from datetime import datetime
from ldap3 import Server, Connection
import os
import sys
import inspect
import getopt
import yaml
import traceback
import json
import shutil
try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

# retrieve at most sizelimit entries for a search.  A sizelimit of 0 (zero) or
# none means no limit.  A sizelimit of  max  means  the maximum integer allowable
# by the protocol.  A server may impose a maximal sizelimit which only the root
# user may override.
sizeLimit = 5

# default log file
logFile = "ldap_validation_" + str(datetime.now()) + ".log"
logFile = logFile.replace(':', '.')  # remove a couple troublesome characters in the timestamp
logFile = logFile.replace(' ', '_')

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

    if (message == ""):
        return None

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
def importSiteDefault(yaml_file):
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
        ldap_anon_bind = \
            yaml_content['config']['application']['sas.identities.providers.ldap.connection']['anonymousBind']
        ldap_bind_pw = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['password']
        ldap_bind_userdn = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['userDN']
        ldap_user_basedn = yaml_content['config']['application']['sas.identities.providers.ldap.user']['baseDN']
        ldap_group_basedn = yaml_content['config']['application']['sas.identities.providers.ldap.group']['baseDN']
        ldap_defaultadmin_user = yaml_content['config']['application']['sas.identities']['administrator']

        ldap_protocol = ldap_url.split(':')[0]

        ldap_anon_bind = (ldap_anon_bind).lower()
        if (ldap_anon_bind == 'false'):
            ldap_anon_bind = False
        if (ldap_anon_bind == 'true'):
            ldap_anon_bind = True

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

        # check to see if the provided values are valid
        assert(ldap_url is not None), "Error: LDAP URL: is undefined."
        assert(ldap_server_host is not None), "Error: LDAP Host is undefined."
        assert(ldap_server_port > 0), "Error: LDAP port is in correctly defined."
        assert (pingHost() is True), "Error: LDAP server is not accessible on specified host and port."
        assert(ldap_anon_bind is True or ldap_anon_bind is False), \
            "Error: LDAP anonymousBind does not have a value of true or false."
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

    if (not performLDAPQuery(ldap_group_basedn, '(objectclass=*)')):
        failTestSuite()
    if (not performLDAPQuery(ldap_user_basedn, '(objectclass=*)')):
        failTestSuite()
    if (not performLDAPQuery(ldap_user_basedn, '(&(objectClass=user)(sAMAccountName=' + 
        ldap_defaultadmin_user + '))', True)):
        failTestSuite()

    logMessage("--------------------------------------------------------------------")
    logMessage("SUCCESS: All LDAP search queries completed successfully.")
    logMessage("Log: " + logFile)
    logMessage("--------------------------------------------------------------------")

    return True


# --------------------------------------------------------------------------------------------------
def failTestSuite():
    """
    Ping the LDAP server on the specified connection.

    Argument:
        None
    Returns:
        None
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    logMessage("LDAP sitedefault.yaml verification has failed. Please see the logs for more information.", True)

    sys.exit(1)


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
def performLDAPQuery(searchBase, searchFilter, verify=False):
    """
    Execute a query on the defined LDAP server.\n

    Argument:
        searchBase(str) - baseDN to be searched
        queryString(str) - LDAP query to be executed
        verify(bool) - Assert that a valid result is returned
    Returns:
        success flag(bool) - Success/Failure of query
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    # perform search
    try:
        logMessage("--------------------------------------------------------------------")
        server = Server(ldap_protocol + "://" + ldap_server_host)

        logMessage("Attempting to create connection binding.")
        connection = Connection(server, ldap_bind_userdn, ldap_bind_pw, auto_bind=True)
        logMessage("Bind results: " + str(connection))

        logMessage("--------------------------------------------------------------------")
        logMessage("Query: search_base=" + searchBase + ", search_filter=" + searchFilter)
        connection.search(search_base=searchBase, search_filter=searchFilter, size_limit=sizeLimit)

    except Exception as e:
        logMessage("LDAP search failed with the following error code: " + str(e), True)
        connection.unbind()
        return False

    # parse results
    resultsReturned = False
    response = json.loads(connection.response_to_json())
    result = connection.result
    queryRC = int(result['result'])
    logMessage("--------------------------------------------------------------------")
    logMessage("Search query return code: " + str(queryRC))
    logMessage("--------------------------------------------------------------------")
    logMessage("Response: " + str(response['entries']))
    logMessage("--------------------------------------------------------------------")
    logMessage("Result: " + str(result))
    logMessage("--------------------------------------------------------------------")
    logMessage("Entries: ")
    for entry in connection.entries:
        resultsReturned = True
        logMessage(str(entry))
    logMessage("--------------------------------------------------------------------")

    if (verify):
        assert(resultsReturned is True), "LDAP Search did not return any query results for query: 'search_base=" + \
            searchBase + ", search_filter=" + searchFilter + "'"

    connection.unbind()

    assert(queryRC == 0 or queryRC == 4), "Error: LDAP Search query failed with return code: " + str(queryRC)

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

    logMessage("####################################################################")
    logMessage("#                                                                ###")
    logMessage("# SAS Viya 4 LDAP Validator                                      ###")
    logMessage("#                                                                ###")
    logMessage("# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###")
    logMessage("# All Rights Reserved.                                           ###")
    logMessage("#                                                                ###")
    logMessage("####################################################################")

    global logFile

    # Parse command line options/arguments
    try:
        opts, args = getopt.getopt(argv, "s:l:h", ["sitedefault=", "logFile=", "help"])
    except getopt.GetoptError as opt_error:
        logMessage(opt_error)

    sitedefault_loc = ""

    for opt, arg in opts:
        logMessage("Processing command line option <" + opt + " " + arg + ">")
        if opt in ('-s', '--sitedefault'):
            logMessage("Setting sitedefault to: " + arg)
            sitedefault_loc = arg
        elif opt in ('-l', '--logFile'):
            oldLogFile = logFile
            logMessage("Setting logging to: " + arg)
            logFile = arg
            shutil.move(oldLogFile, logFile)
        elif opt in ('-h', '--help'):
            logMessage("\n")
            logMessage("This script will attempt to establish a connection to the LDAP")
            logMessage("server defined in your sitedefault.yaml file, and execute several")
            logMessage("queries to establish the validity of the sitedefault.yaml entries.\n")

            logMessage("Usage: python3 ldap_validator.py <-s|--sitedefault> <-l|--logFile> <-p|--port> [<options>]\n")

            logMessage("Options:\n")
            logMessage("    -s  --sitedefault   (Required)Full path the sitedefault.yaml file being validated.")
            logMessage("    -l  --logFile       (Optional)Specify a customer log file to capture output.")
            logMessage("    -h  --help          (Optional)Show this usage message")
            sys.exit(0)
        else:
            logMessage("Unrecognized command line option <" + opt + " " + arg + ">")
            sys.exit(1)

    # Load site default and define variables
    importSiteDefault(sitedefault_loc)

    # Execute test suite
    runTestSchedule()


# --------------------------------------------------------------------------------------------------
##################
#     main()     #
##################
if __name__ == '__main__':
    main(sys.argv[1:])

# ----------------------------------------------------------------------------
